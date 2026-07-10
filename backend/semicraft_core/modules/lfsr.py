"""LFSR (linear-feedback shift register) module (Phase-2 P2-11).

Copies the structure of ``edge_detector.py`` (THE reference module). See
``docs/PLAN-semicraft-phases-2-8.md`` Phase 2 table + Appendix A.3 and
``backend/semicraft_core/modules/contract.py`` for the ``ModuleDef`` shape
this file implements.

What it does
------------

A ``WIDTH``-bit **Fibonacci (many-to-one) LFSR**, shifting *right*: on each
active clock the register shifts one bit toward the LSB, and a new bit
computed by XOR-ing a fixed set of tap bits (the *feedback* function) is fed
back in at the MSB. Concretely, for tap positions ``t1, t2, ...`` (1-indexed
from the LSB, i.e. tap position ``t`` reads bit ``q[t-1]``):

    feedback = q[t1-1] ^ q[t2-1] ^ ...
    q <= {feedback, q[WIDTH-1:1]}

Tap source
----------

Taps are the standard maximal-length Fibonacci-LFSR tap tables (the same
values published in, e.g., Xilinx XAPP052 and the common "primitive
polynomials for maximal-length LFSRs" reference tables), hardcoded per
``width`` -- they are not user-configurable, since an arbitrary tap choice is
not guaranteed to produce a maximal-length (period ``2**WIDTH - 1``)
sequence:

    4:  taps (4, 3)          -- x^4  + x^3  + 1
    8:  taps (8, 6, 5, 4)     -- x^8  + x^6  + x^5  + x^4  + 1
    16: taps (16, 15, 13, 4)  -- x^16 + x^15 + x^13 + x^4  + 1
    24: taps (24, 23, 22, 17) -- x^24 + x^23 + x^22 + x^17 + 1
    32: taps (32, 22, 2, 1)   -- x^32 + x^22 + x^2  + x^1  + 1

Lockup avoidance
-----------------

An all-zero state is a lockup state for any Fibonacci LFSR built purely from
XOR taps (0 XOR 0 ... XOR 0 == 0, so the feedback is always 0 and the
register never leaves all-zero once it gets there). ``init_value`` is
therefore validated to be non-zero (``1 <= init_value < 2**width``), and
reset loads ``init_value`` (parameter ``INIT``), never the all-zero state --
so a correctly generated instance never starts in, and (being maximal-length)
never reaches, the lockup state.

Output styles
-------------

- ``parallel``: the full register state is exposed as the port
  ``q[WIDTH-1:0]``.
- ``serial``: no parallel ``q`` port; instead a single-bit port ``out``
  exposes the *feedback* bit computed combinationally from the current
  register state (the bit that will be shifted into the MSB on the next
  active edge). ``q`` still exists as an internal signal in this style.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    Bit,
    ClockSpec,
    Comment,
    CommentLevel,
    Concat,
    Const,
    ContAssign,
    Header,
    If,
    Module,
    Param,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
    Slice,
)
from ..snippets.contract import ClockedOptions, ExplanationDoc, SignalDoc
from ..version import VERSION
from .contract import Check, PortGroup, TbSpec

# ---------------------------------------------------------------------------
# Standard maximal-length Fibonacci LFSR tap tables (Appendix: see module
# docstring for polynomial form / source). Tap positions are 1-indexed from
# the LSB: tap value ``t`` reads register bit ``q[t-1]``.
# ---------------------------------------------------------------------------

_TAPS: dict[int, tuple[int, ...]] = {
    4: (4, 3),
    8: (8, 6, 5, 4),
    16: (16, 15, 13, 4),
    24: (24, 23, 22, 17),
    32: (32, 22, 2, 1),
}

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class LfsrOptions(ClockedOptions):
    """Configuration for the LFSR module.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments,
    naming) with the LFSR-specific fields below.
    """

    width: Literal[4, 8, 16, 24, 32] = Field(
        default=8,
        description=(
            "Register width in bits (param WIDTH). Selects the hardcoded "
            "maximal-length tap set for that width; taps are not "
            "independently configurable."
        ),
    )
    init_value: int = Field(
        default=1,
        description=(
            "Seed value loaded on reset (param INIT). Must satisfy "
            "1 <= init_value < 2**width: the all-zero state is a lockup "
            "state for a Fibonacci LFSR (the feedback function would "
            "produce 0 forever), so it is forbidden as a seed."
        ),
    )
    enable: bool = Field(
        default=True,
        description="Add an 'en' input that gates shifting; when low the register holds.",
    )
    output_style: Literal["parallel", "serial"] = Field(
        default="parallel",
        description=(
            "'parallel': expose the full register state as q[WIDTH-1:0]. "
            "'serial': no parallel q port; expose a single-bit 'out' port "
            "carrying the combinational feedback bit instead."
        ),
    )

    @model_validator(mode="after")
    def _check_init_value(self) -> LfsrOptions:
        upper = 1 << self.width
        if not (1 <= self.init_value < upper):
            raise ValueError(
                f"init_value={self.init_value} must satisfy "
                f"1 <= init_value < 2**{self.width} ({upper}); the all-zero "
                "state is a lockup state for a Fibonacci LFSR and is "
                "forbidden as a seed."
            )
        return self


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "lfsr"


def _taps(opts: LfsrOptions) -> tuple[int, ...]:
    return _TAPS[opts.width]


def _reset_spec(opts: LfsrOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _feedback_expr(opts: LfsrOptions) -> BinOp | Bit:
    """XOR-chain of the tap bits of the *current* q (before the shift).

    Tap position ``t`` (1-indexed from the LSB) reads bit ``q[t-1]``.
    """
    bits = [Bit(Ref("q"), Const(t - 1)) for t in _taps(opts)]
    expr = bits[0]
    for b in bits[1:]:
        expr = BinOp(BinOpKind.XOR, expr, b)
    return expr


def _shift_expr(opts: LfsrOptions, feedback) -> Concat:
    """Next-value concat: shift right, feedback enters the MSB.

    q <= {feedback, q[WIDTH-1:1]}
    """
    upper = Slice(
        Ref("q"),
        msb=BinOp(BinOpKind.SUB, Ref("WIDTH"), Const(1)),
        lsb=Const(1),
    )
    return Concat([feedback, upper])


def generate(opts: LfsrOptions) -> Module:
    """Build the LFSR IR ``Module`` (pure).

    Structure: one ``AlwaysFF`` holding the register ``q`` (shift-right with
    XOR feedback into the MSB, gated by ``en`` when the enable option is
    set); when ``output_style="serial"`` an additional ``ContAssign`` exposes
    the combinational feedback bit as ``out``.

    The renderer decides always_ff vs always, ``<=`` vs ``=``, and reset
    composition (IR_SPEC design rules 2-4); the generator only chooses the
    logic.
    """
    reset = _reset_spec(opts)
    dtype = vec("WIDTH")
    feedback = _feedback_expr(opts)

    # --- ports (order per clean-rtl: clock, reset, control, data) -----------
    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
    ]
    if opts.enable:
        ports.append(Port("en", IN, bit(), doc="Shift enable (holds when low)"))
    if opts.output_style == "parallel":
        ports.append(Port("q", OUT, dtype, doc="LFSR register state"))
    else:
        ports.append(Port("out", OUT, bit(), doc=_out_doc(opts)))

    # When output_style="serial" removes the 'q' port, the register still
    # needs a declared internal signal to hold its state (IR validation
    # rule 2: every Ref must resolve to a param, port, or declared Signal).
    extra_items: list = []
    if opts.output_style == "serial":
        extra_items.append(
            Signal("q", dtype, doc="Internal LFSR register state (no parallel output port)")
        )

    # --- clocked body --------------------------------------------------
    shift_stmt = Assign(Ref("q"), _shift_expr(opts, feedback))
    body: list = [
        Comment(
            f"{opts.width}-bit Fibonacci LFSR: shift right, feedback = XOR of "
            f"taps {_taps(opts)} (1-indexed from LSB) into the MSB",
            level=CommentLevel.VERBOSE,
        ),
    ]
    if opts.enable:
        body.append(If(Ref("en"), then=[shift_stmt]))
    else:
        body.append(shift_stmt)

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=reset,
        reset_body=[Assign(Ref("q"), Ref("INIT"))],
        body=body,
    )

    items: list = [*extra_items, always]
    if opts.output_style == "serial":
        # 'out' is a pure combinational tap of the current state (the bit
        # about to be fed back into the MSB on the next active edge), not a
        # separate register, so it is a continuous assignment.
        items.append(ContAssign(Ref("out"), feedback))

    params = [
        Param("WIDTH", Const(opts.width), doc="Register width in bits"),
        Param("INIT", Const(opts.init_value, width=Ref("WIDTH")), doc="Reset seed value"),
    ]

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by the generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=params,
        ports=ports,
        items=items,
    )


# ---------------------------------------------------------------------------
# Documentation metadata (port groups)
# ---------------------------------------------------------------------------


def _reset_port_name(opts: LfsrOptions) -> str:
    """Reset port name as it appears in the explanation/RTL (``rst_n`` when
    active-low)."""
    return "rst" + ("_n" if opts.reset_polarity == "active_low" else "")


def port_groups(opts: LfsrOptions) -> list[PortGroup]:
    """Group ports for the datasheet: a clocking group and a data group."""
    clocking_ports = ["clk", _reset_port_name(opts)]
    if opts.enable:
        clocking_ports.append("en")
    data_ports = ["q"] if opts.output_style == "parallel" else ["out"]
    return [
        PortGroup(
            name="Clocking",
            ports=clocking_ports,
            description="Clock, reset, and (optional) shift enable for the LFSR register.",
        ),
        PortGroup(
            name="Data",
            ports=data_ports,
            description=(
                "Full LFSR register state."
                if opts.output_style == "parallel"
                else "Single-bit combinational feedback output."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Smoke-TB recipe
# ---------------------------------------------------------------------------


def _sim_step(q: int, opts: LfsrOptions) -> tuple[int, int]:
    """Pure-Python model of one shift step; mirrors the RTL exactly.

    Returns ``(next_q, feedback_bit)`` for the given current state ``q``.
    """
    taps = _taps(opts)
    fb = 0
    for t in taps:
        fb ^= (q >> (t - 1)) & 1
    mask = (1 << opts.width) - 1
    next_q = ((fb << (opts.width - 1)) | (q >> 1)) & mask
    return next_q, fb


def tb_spec(opts: LfsrOptions) -> TbSpec:
    """A ~6-vector directed smoke TB, honest checks computed by simulating
    the exact same shift-right/XOR-feedback model the RTL implements.

    When ``enable`` is set, one vector holds ``en=0`` to exercise the hold
    behavior; the two checks are the post-reset seed value (cycle 0, before
    any shift) and the state right after the held cycle (demonstrating the
    hold), both computed by :func:`_sim_step` rather than hand-picked.
    """
    signal = "q" if opts.output_style == "parallel" else "out"

    if opts.enable:
        vectors: list[dict[str, int]] = [
            {"en": 1},
            {"en": 1},
            {"en": 1},
            {"en": 0},  # hold cycle
            {"en": 1},
            {"en": 1},
        ]
    else:
        vectors = [{} for _ in range(6)]

    # states[i] = register value at cycle i (post i clock edges from reset).
    states = [opts.init_value]
    for vec_i in vectors:
        en_i = vec_i.get("en", 1) if opts.enable else 1
        cur = states[-1]
        if en_i:
            nxt, _ = _sim_step(cur, opts)
        else:
            nxt = cur
        states.append(nxt)

    def _observed(cycle: int) -> int:
        """Value of the chosen output signal at a given cycle."""
        q_val = states[cycle]
        if signal == "q":
            return q_val
        _, fb = _sim_step(q_val, opts)
        return fb

    hold_cycle = 4  # first cycle after the held (en=0) transition, if enabled
    checks: list[Check] = [
        Check(cycle=0, signal=signal, expected=_observed(0)),
        Check(
            cycle=hold_cycle if opts.enable else len(vectors),
            signal=signal,
            expected=_observed(hold_cycle if opts.enable else len(vectors)),
        ),
    ]

    return TbSpec(
        clock="clk",
        reset="rst",
        reset_cycles=2,
        vectors=vectors,
        checks=checks,
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: LfsrOptions) -> str:
    style_word = "parallel" if opts.output_style == "parallel" else "serial"
    return f"{opts.width}-bit Fibonacci LFSR, {style_word} output"


def _reset_doc(opts: LfsrOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _out_doc(opts: LfsrOptions) -> str:
    return "Combinational feedback bit (XOR of the tap bits of the current state)"


def _reset_behavior_text(opts: LfsrOptions) -> str:
    style = "asynchronously" if opts.reset_style == "async" else "synchronously"
    pol = (
        "active-low (asserted when 0)"
        if opts.reset_polarity == "active_low"
        else "active-high (asserted when 1)"
    )
    edge = (
        "on assertion of reset (independent of the clock)"
        if opts.reset_style == "async"
        else "on the rising clock edge while reset is asserted"
    )
    return (
        f"The {pol} reset loads the seed value INIT ({opts.init_value}) into "
        f"the register {style} {edge} -- never the all-zero lockup state."
    )


def explain(opts: LfsrOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    period = (1 << opts.width) - 1
    taps = _taps(opts)

    configuration = [
        f"Width: {opts.width} bits (param WIDTH)",
        f"Taps: {taps} (1-indexed from LSB; standard maximal-length polynomial)",
        f"Seed (init_value): {opts.init_value} (param INIT)",
        f"Enable input: {'yes' if opts.enable else 'no'}",
        f"Output style: {opts.output_style}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; the register shifts on the rising edge.",
        ),
        SignalDoc(
            name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
            direction="input",
            description=_reset_doc(opts) + " reset input.",
        ),
    ]
    if opts.enable:
        signals.append(
            SignalDoc(
                name="en",
                direction="input",
                description="Shift enable; when low the register holds its current value.",
            )
        )
    signals.append(
        SignalDoc(
            name="q",
            direction="output" if opts.output_style == "parallel" else "internal",
            description=(
                f"{opts.width}-bit LFSR register state."
                if opts.output_style == "parallel"
                else f"{opts.width}-bit internal LFSR register state (no parallel output port)."
            ),
        )
    )
    if opts.output_style == "serial":
        signals.append(
            SignalDoc(
                name="out",
                direction="output",
                description=_out_doc(opts) + ".",
            )
        )

    enable_behavior = (
        "When en is high the register shifts on each clock; when en is low it holds "
        "its current value (the feedback function is not evaluated into the register, "
        "though the combinational 'out' tap, if present, still reflects the current state)."
        if opts.enable
        else None
    )

    assumptions = [
        "A single free-running clock drives the register; all I/O is synchronous to it.",
        "The seed (init_value) is loaded once, at reset; changing it requires "
        "regenerating the module (there is no runtime seed-load input).",
    ]

    limitations = [
        "This is a pseudo-random sequence generator, not a cryptographically "
        "secure random number generator -- do not use it for security-sensitive "
        "randomness (key/nonce generation, etc.).",
        f"Maximal-length Fibonacci LFSR: starting from any nonzero seed, it "
        f"cycles through all {period} nonzero {opts.width}-bit states before "
        f"repeating (period 2^{opts.width}-1 = {period}).",
        "All-zero is an illegal lockup state for this Fibonacci LFSR (the XOR "
        "feedback function produces 0 forever once the register reaches it); "
        "init_value is validated to be non-zero and reset loads init_value "
        "(never zero), so a correctly generated instance never starts in, "
        "and (being maximal-length) never reaches, the lockup state.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A {opts.width}-bit Fibonacci LFSR: a pseudo-random binary sequence "
            f"generator with {opts.output_style} output, period 2^{opts.width}-1."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior=_reset_behavior_text(opts),
        enable_behavior=enable_behavior,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# ModuleDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _LfsrModule:
    """Bundles the LFSR's metadata and pure functions.

    Satisfies the :class:`~.contract.ModuleDef` protocol structurally.
    """

    id: str = "lfsr"
    name: str = "LFSR"
    description: str = (
        "Maximal-length Fibonacci linear-feedback shift register (pseudo-random "
        "sequence generator, parallel or serial output)."
    )
    kind: str = "module"
    maturity: str = "stable"
    options_model: type[LfsrOptions] = LfsrOptions

    def generate(self, opts: LfsrOptions) -> Module:
        return generate(opts)

    def explain(self, opts: LfsrOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: LfsrOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: LfsrOptions) -> TbSpec:
        return tb_spec(opts)


MODULE = _LfsrModule()


__all__ = [
    "LfsrOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "MODULE",
]
