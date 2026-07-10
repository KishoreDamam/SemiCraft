"""Clock-divider module (Phase-2 P2-07).

Copies the structure of ``edge_detector.py`` (THE reference module). See
``docs/PLAN-semicraft-phases-2-8.md`` Phase 2 table + Appendix A.3 and
``backend/semicraft_core/modules/contract.py`` for the ``ModuleDef`` shape
this file implements.

What it does
------------

A free-running counter counts clk cycles up to ``DIV``; two output styles are
offered:

- ``toggle``: a divided clock signal ``clk_out`` toggles every ``DIV/2``
  cycles, producing a 50%-duty divided clock (hence ``divide_by`` is
  restricted to even values — an odd divisor cannot produce a 50%-duty
  toggle output from a single counter compare).
- ``pulse``: ``clk_out`` (interpreted as a clock-enable, not a clock) is
  asserted for exactly one cycle every ``DIV`` cycles — the synthesis-
  friendly "clock enable" idiom: the design stays on the original fast clock
  and gates its registers with this enable, avoiding a second physical clock
  network entirely.

**This is a data signal, not a clock.** The generated ``clk_out`` is an
ordinary flip-flop output; it must not be used to clock other flip-flops
directly on FPGA/ASIC without going through a PLL/MMCM (for a real divided
clock) or by using the ``pulse`` style as a synchronous clock-enable on the
original ``clk`` (the recommended, synthesis-friendly approach). See
``limitations`` in the explanation and the VLSI-agkit ``clean-rtl`` skill.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

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
    Header,
    If,
    Module,
    Param,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
    UnaryOp,
    UnaryOpKind,
)
from ..snippets.contract import ClockedOptions, ExplanationDoc, SignalDoc
from ..version import VERSION
from .contract import Check, PortGroup, TbSpec

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class ClockDividerOptions(ClockedOptions):
    """Configuration for the clock-divider module.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments, naming)
    with the clock-divider-specific fields below.
    """

    divide_by: int = Field(
        default=2,
        ge=2,
        le=65536,
        description=(
            "Division ratio (param DIV). Must be even: a 50%-duty toggle "
            "output is produced by toggling clk_out every DIV/2 input "
            "cycles, which only yields a symmetric divided clock for an "
            "even DIV."
        ),
    )
    output_enable_style: Literal["toggle", "pulse"] = Field(
        default="toggle",
        description=(
            "'toggle': clk_out toggles at DIV/2 cycles, producing a 50%-duty "
            "divided clock signal. 'pulse': clk_out is a single-cycle enable "
            "tick asserted once every DIV cycles — the synthesis-friendly "
            "clock-enable idiom (recommended for real designs; see the "
            "explanation limitations)."
        ),
    )

    @model_validator(mode="after")
    def _check_even(self) -> ClockDividerOptions:
        if self.divide_by % 2 != 0:
            raise ValueError(
                f"divide_by={self.divide_by} must be even: a 50%-duty toggle "
                "output can only be produced by toggling at DIV/2 cycles, "
                "which requires DIV to be even."
            )
        return self


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "clock_divider"


def _cnt_width(opts: ClockDividerOptions) -> int:
    """Counter width: clog2(DIV) bits (counts 0..DIV-1)."""
    return max(1, math.ceil(math.log2(opts.divide_by)))


def _reset_spec(opts: ClockDividerOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def generate(opts: ClockDividerOptions) -> Module:
    """Build the clock-divider IR ``Module`` (pure).

    Structure: one free-running counter ``cnt`` counting 0..DIV-1 in an
    ``AlwaysFF``; clk_out behavior depends on ``output_enable_style``:

    - ``toggle``: cnt resets and clk_out toggles every DIV/2 cycles (a
      half-period compare), producing a 50%-duty divided clock.
    - ``pulse``: cnt resets every DIV cycles; clk_out is asserted for the one
      cycle the counter wraps and held low otherwise (a single-cycle enable
      pulse per full period).

    The renderer decides always_ff vs always, ``<=`` vs ``=``, and reset
    composition (IR_SPEC design rules 2-4); the generator only chooses the
    logic.
    """
    reset = _reset_spec(opts)
    cnt_dtype = vec("CNT_WIDTH")

    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Input clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
        Port("clk_out", OUT, bit(), doc=_clk_out_doc(opts)),
    ]

    signals: list = [
        Signal("cnt", cnt_dtype, doc="Free-running divide counter"),
    ]

    if opts.output_enable_style == "toggle":
        half = Const(opts.divide_by // 2 - 1, width=Ref("CNT_WIDTH"))
        at_half = BinOp(BinOpKind.EQ, Ref("cnt"), half)
        body = [
            Comment(
                "Toggle clk_out every DIV/2 cycles for a 50%-duty divided clock",
                level=CommentLevel.VERBOSE,
            ),
            If(
                at_half,
                then=[
                    Assign(Ref("cnt"), Const(0, width=Ref("CNT_WIDTH"))),
                    Assign(Ref("clk_out"), UnaryOp(UnaryOpKind.NOT_BITWISE, Ref("clk_out"))),
                ],
                else_=[
                    Assign(Ref("cnt"), BinOp(BinOpKind.ADD, Ref("cnt"), Const(1))),
                ],
            ),
        ]
        reset_body = [
            Assign(Ref("cnt"), Const(0, width=Ref("CNT_WIDTH"))),
            Assign(Ref("clk_out"), Const(0)),
        ]
    else:
        # pulse style: cnt wraps at DIV-1; clk_out pulses high for that one
        # cycle and is low every other cycle (single-cycle enable per period).
        terminal = Const(opts.divide_by - 1, width=Ref("CNT_WIDTH"))
        at_terminal = BinOp(BinOpKind.EQ, Ref("cnt"), terminal)
        body = [
            Comment(
                "Free-running counter wraps every DIV cycles; clk_out pulses "
                "high for the single wrap cycle (clock-enable idiom)",
                level=CommentLevel.VERBOSE,
            ),
            If(
                at_terminal,
                then=[
                    Assign(Ref("cnt"), Const(0, width=Ref("CNT_WIDTH"))),
                    Assign(Ref("clk_out"), Const(1)),
                ],
                else_=[
                    Assign(Ref("cnt"), BinOp(BinOpKind.ADD, Ref("cnt"), Const(1))),
                    Assign(Ref("clk_out"), Const(0)),
                ],
            ),
        ]
        reset_body = [
            Assign(Ref("cnt"), Const(0, width=Ref("CNT_WIDTH"))),
            Assign(Ref("clk_out"), Const(0)),
        ]

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=reset,
        reset_body=reset_body,
        body=body,
    )

    # The division ratio is baked into the counter comparison constants, so
    # DIV is not emitted as a parameter (an unreferenced param trips
    # Verilator's UNUSEDPARAM under -Wall); the ratio is documented in the
    # header and doc file.
    params = [
        Param(
            "CNT_WIDTH",
            Const(_cnt_width(opts)),
            doc=f"Divide counter width (clog2 of divide ratio {opts.divide_by})",
        ),
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
        items=[*signals, always],
    )


# ---------------------------------------------------------------------------
# Documentation metadata (port groups)
# ---------------------------------------------------------------------------


def _reset_port_name(opts: ClockDividerOptions) -> str:
    """Reset port name as it appears in the explanation/RTL (``rst_n`` when
    active-low)."""
    return "rst" + ("_n" if opts.reset_polarity == "active_low" else "")


def port_groups(opts: ClockDividerOptions) -> list[PortGroup]:
    """Group ports for the datasheet: a clocking group and a data group."""
    return [
        PortGroup(
            name="Clocking",
            ports=["clk", _reset_port_name(opts)],
            description="Input clock and reset for the divide counter.",
        ),
        PortGroup(
            name="Data",
            ports=["clk_out"],
            description=_clk_out_doc(opts),
        ),
    ]


# ---------------------------------------------------------------------------
# Smoke-TB recipe
# ---------------------------------------------------------------------------


def tb_spec(opts: ClockDividerOptions) -> TbSpec:
    """A directed smoke TB with no inputs beyond clock/reset; checks sample
    clk_out at cycles derived from DIV.

    The divider has no data inputs, so ``vectors`` are empty per-cycle dicts
    (the TB just runs the clock for enough cycles for a full period). Two
    checks assert the expected clk_out value at a known cycle for each style:
    for 'toggle' it asserts clk_out has flipped from its reset value by
    DIV/2 cycles in; for 'pulse' it asserts clk_out is 0 well before the
    wrap and (for the smallest DIV, the honestly-checkable case) at the wrap.
    """
    n = max(opts.divide_by, 4)
    vectors: list[dict[str, int]] = [{} for _ in range(n)]

    checks: list[Check] = []
    if opts.output_enable_style == "toggle":
        half = opts.divide_by // 2
        # clk_out starts at 0 (reset value) and toggles to 1 after half cycles.
        checks.append(Check(cycle=half, signal="clk_out", expected=1))
        checks.append(Check(cycle=1, signal="clk_out", expected=0))
    else:
        # clk_out is 0 except on the single wrap cycle each period.
        checks.append(Check(cycle=1, signal="clk_out", expected=0))
        checks.append(Check(cycle=opts.divide_by, signal="clk_out", expected=1))

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


def _description(opts: ClockDividerOptions) -> str:
    style_word = "toggle" if opts.output_enable_style == "toggle" else "pulse"
    return f"Clock divider by {opts.divide_by} ({style_word} output)"


def _reset_doc(opts: ClockDividerOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _clk_out_doc(opts: ClockDividerOptions) -> str:
    if opts.output_enable_style == "toggle":
        return f"Divided clock signal, toggling every DIV/2={opts.divide_by // 2} input cycles"
    return f"Single-cycle enable pulse, asserted once every DIV={opts.divide_by} input cycles"


def _reset_behavior_text(opts: ClockDividerOptions) -> str:
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
        f"The {pol} reset clears the divide counter and clk_out to 0 "
        f"{style} {edge}."
    )


def explain(opts: ClockDividerOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    style_word = (
        "toggle (50%-duty divided clock)"
        if opts.output_enable_style == "toggle"
        else "pulse (single-cycle clock-enable tick)"
    )
    configuration = [
        f"Divide ratio: {opts.divide_by} (param DIV)",
        f"Output style: {style_word}",
        f"Counter width: {_cnt_width(opts)} bits (clog2(DIV))",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Input clock; the divide counter runs on its rising edge.",
        ),
        SignalDoc(
            name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
            direction="input",
            description=_reset_doc(opts) + " reset input.",
        ),
        SignalDoc(
            name="cnt",
            direction="internal",
            description="Free-running divide counter, counting input clock cycles.",
        ),
        SignalDoc(
            name="clk_out",
            direction="output",
            description=_clk_out_doc(opts) + ".",
        ),
    ]

    assumptions = [
        "A single free-running input clock drives the divider.",
        "The consumer of clk_out either treats it purely as a data signal "
        "(toggle style) or as a synchronous clock-enable on the original "
        "clk (pulse style), not as a low-skew clock network.",
    ]

    limitations = [
        "The generated clk_out is a data signal produced by an ordinary "
        "flip-flop — it is NOT a low-skew clock and must not be routed onto "
        "a clock network or used to directly clock other flip-flops in a "
        "real FPGA/ASIC design. Use a PLL/MMCM for a genuine divided clock, "
        "or prefer the 'pulse' clock-enable style and keep all logic on the "
        "original clk (see the clean-rtl reference).",
        "No fractional division: divide_by must be an even integer, so only "
        "even divisors are representable with a 50%-duty toggle output.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A clock divider by {opts.divide_by}: a free-running counter "
            f"produces clk_out as a {style_word}."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior=_reset_behavior_text(opts),
        enable_behavior=None,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# ModuleDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ClockDividerModule:
    """Bundles the clock-divider's metadata and pure functions.

    Satisfies the :class:`~.contract.ModuleDef` protocol structurally.
    """

    id: str = "clock-divider"
    name: str = "Clock Divider"
    description: str = (
        "Divides an input clock by an even integer ratio, either as a "
        "50%-duty toggled clock signal or a single-cycle clock-enable pulse."
    )
    kind: str = "module"
    maturity: str = "stable"
    options_model: type[ClockDividerOptions] = ClockDividerOptions

    def generate(self, opts: ClockDividerOptions) -> Module:
        return generate(opts)

    def explain(self, opts: ClockDividerOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: ClockDividerOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: ClockDividerOptions) -> TbSpec:
        return tb_spec(opts)


MODULE = _ClockDividerModule()


__all__ = [
    "ClockDividerOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "MODULE",
]
