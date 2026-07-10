"""Gray-code counter module (Phase-2 P2-12).

Copies the structure of ``edge_detector.py`` (THE reference module). See
``docs/PLAN-semicraft-phases-2-8.md`` Phase 2 table + Appendix A.3 and
``backend/semicraft_core/modules/contract.py`` for the ``ModuleDef`` shape
this file implements.

What it does
------------

An ordinary free-running ``WIDTH``-bit binary counter register ``bin``
increments every active clock (naturally wrapping modulo ``2**WIDTH``); the
port ``gray`` is a *combinational* continuous assignment of the standard
binary-to-Gray conversion of the registered binary counter:

    gray = bin ^ (bin >> 1)

Only the binary register is clocked -- ``gray`` is not a separate register,
it is a pure function of ``bin``. Because ``bin`` itself changes by exactly 1
(mod ``2**WIDTH``) each active cycle, the derived Gray value changes by
exactly one bit between successive counts (the defining single-bit-transition
property of a Gray sequence), which is what makes Gray counters useful for
building clock-domain-crossing (CDC) pointers/counters -- see
``semicraft_core.snippets.cdc_synchronizer`` and the VLSI-agkit
``cdc-synchronizer`` skill for how such a multi-bit value is safely
synchronized across clock domains (each bit double-flopped independently is
only safe because at most one bit changes per source-clock cycle).
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    ClockSpec,
    Comment,
    CommentLevel,
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
)
from ..snippets.contract import ClockedOptions, ExplanationDoc, SignalDoc
from ..version import VERSION
from .contract import Check, PortGroup, TbSpec

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class GrayCounterOptions(ClockedOptions):
    """Configuration for the Gray-code counter module.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments,
    naming) with the Gray-counter-specific fields below.
    """

    width: int = Field(
        default=8,
        ge=2,
        le=32,
        description=(
            "Binary counter / Gray output width in bits (param WIDTH). The "
            "counter free-runs and wraps naturally modulo 2**WIDTH."
        ),
    )
    enable: bool = Field(
        default=True,
        description="Add an 'en' input that gates counting; when low the counter holds.",
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "gray_counter"


def _reset_spec(opts: GrayCounterOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _gray_expr() -> BinOp:
    """gray = bin ^ (bin >> 1) -- the standard binary-to-Gray conversion."""
    return BinOp(BinOpKind.XOR, Ref("bin"), BinOp(BinOpKind.SHR, Ref("bin"), Const(1)))


def generate(opts: GrayCounterOptions) -> Module:
    """Build the Gray-counter IR ``Module`` (pure).

    Structure: one ``AlwaysFF`` holding the free-running binary counter
    ``bin`` (gated by ``en`` when the enable option is set); one
    ``ContAssign`` computing ``gray`` combinationally from ``bin``.

    The renderer decides always_ff vs always, ``<=`` vs ``=``, and reset
    composition (IR_SPEC design rules 2-4); the generator only chooses the
    logic.
    """
    reset = _reset_spec(opts)
    dtype = vec("WIDTH")

    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
    ]
    if opts.enable:
        ports.append(Port("en", IN, bit(), doc="Count enable (holds when low)"))
    ports.append(Port("gray", OUT, dtype, doc=_gray_doc()))

    signals: list = [Signal("bin", dtype, doc="Free-running binary counter (registered)")]

    incr_stmt = Assign(Ref("bin"), BinOp(BinOpKind.ADD, Ref("bin"), Const(1)))
    body: list = [
        Comment(
            "Free-running binary counter; wraps naturally modulo 2**WIDTH",
            level=CommentLevel.VERBOSE,
        ),
    ]
    if opts.enable:
        body.append(If(Ref("en"), then=[incr_stmt]))
    else:
        body.append(incr_stmt)

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=reset,
        reset_body=[Assign(Ref("bin"), Const(0, width=Ref("WIDTH")))],
        body=body,
    )

    items: list = [*signals, always, ContAssign(Ref("gray"), _gray_expr())]

    params = [Param("WIDTH", Const(opts.width), doc="Counter/Gray output width in bits")]

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


def _reset_port_name(opts: GrayCounterOptions) -> str:
    """Reset port name as it appears in the explanation/RTL (``rst_n`` when
    active-low)."""
    return "rst" + ("_n" if opts.reset_polarity == "active_low" else "")


def port_groups(opts: GrayCounterOptions) -> list[PortGroup]:
    """Group ports for the datasheet: a clocking group and a data group."""
    clocking_ports = ["clk", _reset_port_name(opts)]
    if opts.enable:
        clocking_ports.append("en")
    return [
        PortGroup(
            name="Clocking",
            ports=clocking_ports,
            description="Clock, reset, and (optional) count enable for the binary counter.",
        ),
        PortGroup(
            name="Data",
            ports=["gray"],
            description=_gray_doc(),
        ),
    ]


# ---------------------------------------------------------------------------
# Smoke-TB recipe
# ---------------------------------------------------------------------------


def _to_gray(value: int) -> int:
    return value ^ (value >> 1)


def tb_spec(opts: GrayCounterOptions) -> TbSpec:
    """A ~6-vector directed smoke TB; checks computed by simulating the exact
    same binary-increment + bin^(bin>>1) model the RTL implements.

    When ``enable`` is set, one vector holds ``en=0`` to exercise the hold
    behavior; the checks are the post-reset value (cycle 0, bin==0 so
    gray==0) and the value right after the held cycle (demonstrating the
    hold), both computed rather than hand-picked.
    """
    mask = (1 << opts.width) - 1

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

    # bins[i] = binary counter value at cycle i (post i clock edges from reset).
    bins = [0]
    for vec_i in vectors:
        en_i = vec_i.get("en", 1) if opts.enable else 1
        cur = bins[-1]
        nxt = ((cur + 1) & mask) if en_i else cur
        bins.append(nxt)

    hold_cycle = 4 if opts.enable else len(vectors)
    checks: list[Check] = [
        Check(cycle=0, signal="gray", expected=_to_gray(bins[0])),
        Check(cycle=hold_cycle, signal="gray", expected=_to_gray(bins[hold_cycle])),
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


def _description(opts: GrayCounterOptions) -> str:
    return f"{opts.width}-bit Gray-code counter"


def _reset_doc(opts: GrayCounterOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _gray_doc() -> str:
    return "Gray-coded output, combinational (bin ^ (bin >> 1)) from the binary counter"


def _reset_behavior_text(opts: GrayCounterOptions) -> str:
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
        f"The {pol} reset clears the binary counter to 0 {style} {edge}; "
        "gray (combinational) follows immediately from the reset counter value."
    )


def explain(opts: GrayCounterOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    period = 1 << opts.width

    configuration = [
        f"Width: {opts.width} bits (param WIDTH, period {period} counts)",
        f"Enable input: {'yes' if opts.enable else 'no'}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; the binary counter increments on the rising edge.",
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
                description="Count enable; when low the counter holds its current value.",
            )
        )
    signals.append(
        SignalDoc(
            name="bin",
            direction="internal",
            description=f"Free-running {opts.width}-bit binary counter (the registered state).",
        )
    )
    signals.append(
        SignalDoc(
            name="gray",
            direction="output",
            description=_gray_doc() + ".",
        )
    )

    enable_behavior = (
        "When en is high the binary counter increments each clock; when en is low "
        "it holds its current value (gray tracks bin combinationally either way, so "
        "it also holds while en is low)."
        if opts.enable
        else None
    )

    assumptions = [
        "A single free-running clock drives the binary counter; gray is purely "
        "combinational from that registered state.",
        "Consumers treat gray as a Gray-coded value (at most one bit differs "
        "between successive samples of a stable, glitch-free bin) -- this "
        "property does not extend to arbitrary combinational manipulation of gray.",
    ]

    limitations = [
        "The single-bit-transition property holds only because bin is a "
        "clean registered signal changing by exactly one count per active "
        "edge; gray is combinational and therefore glitch-free/single-bit-"
        "changing only as observed synchronously to clk, not asynchronously.",
        "This module performs no clock-domain-crossing (CDC) synchronization "
        "itself -- gray is intended to be the source-domain signal fed into a "
        "synchronizer (e.g. semicraft_core.snippets.cdc_synchronizer / the "
        "VLSI-agkit cdc-synchronizer skill) when crossing to another clock domain.",
        "Wraps modulo 2**WIDTH like any free-running counter; there is no "
        "terminal-count or overflow flag.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A {opts.width}-bit Gray-code counter: a free-running binary "
            "counter with a combinational Gray-coded output, changing by "
            "exactly one bit between successive counts -- the property "
            "CDC-safe multi-bit pointers/counters rely on."
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
class _GrayCounterModule:
    """Bundles the Gray-counter's metadata and pure functions.

    Satisfies the :class:`~.contract.ModuleDef` protocol structurally.
    """

    id: str = "gray-counter"
    name: str = "Gray Counter"
    description: str = (
        "Free-running binary counter with a combinational Gray-coded output "
        "(single-bit transitions between successive counts), commonly used "
        "as the source-domain signal for CDC-safe pointers/counters."
    )
    kind: str = "module"
    maturity: str = "stable"
    options_model: type[GrayCounterOptions] = GrayCounterOptions

    def generate(self, opts: GrayCounterOptions) -> Module:
        return generate(opts)

    def explain(self, opts: GrayCounterOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: GrayCounterOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: GrayCounterOptions) -> TbSpec:
        return tb_spec(opts)


MODULE = _GrayCounterModule()


__all__ = [
    "GrayCounterOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "MODULE",
]
