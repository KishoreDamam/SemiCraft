"""Reference module: edge detector (Phase-2 P2-04 / P2-06 seed).

THE reference ``ModuleDef`` implementation — later module WPs (P2-06..12) copy
its structure, so it is deliberately over-commented at the level of *intent*.
It mirrors the snippet reference (``semicraft_core.snippets.counter``) but adds
the module surface: ``port_groups`` and ``tb_spec`` (Appendix A.3).

What it does
------------

An edge detector emits a one-cycle pulse when its input ``d`` changes in the
selected direction. It samples ``d`` into a one-cycle delay register ``d_q``
and combines the two:

- ``rising``:  ``pulse = d & ~d_q``   (0 -> 1 transition)
- ``falling``: ``pulse = ~d & d_q``   (1 -> 0 transition)
- ``both``:    ``pulse = d ^ d_q``    (any transition)

``width`` replicates this per bit (each bit detected independently). When
``registered_output`` is true the pulse is passed through one more register
stage (``pulse`` is itself a flop) so the output is glitch-free and adds one
cycle of latency; otherwise ``pulse`` is a continuous assignment of the edge
expression (zero extra latency, combinational output).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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


class EdgeDetectorOptions(ClockedOptions):
    """Configuration for the edge detector module.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments, naming)
    with the edge-detector-specific fields below.
    """

    detect: Literal["rising", "falling", "both"] = Field(
        default="rising",
        description=(
            "Which transition produces a pulse. 'rising' fires on 0->1, "
            "'falling' on 1->0, 'both' on any change."
        ),
    )
    width: int = Field(
        default=1,
        ge=1,
        le=64,
        description=(
            "Bit width of d/pulse. Each bit is edge-detected independently; "
            "pulse[i] reflects a transition on d[i]."
        ),
    )
    registered_output: bool = Field(
        default=True,
        description=(
            "When true, the pulse passes through an output register stage: the "
            "output is glitch-free but delayed one extra clock. When false, "
            "pulse is a continuous assignment of the edge expression "
            "(combinational output, no extra latency)."
        ),
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "edge_detector"


def _dtype(opts: EdgeDetectorOptions):
    """Scalar bit for width==1, else a WIDTH-wide vector."""
    return bit() if opts.width == 1 else vec("WIDTH")


def _reset_spec(opts: EdgeDetectorOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _zero_const(opts: EdgeDetectorOptions) -> Const:
    """WIDTH-wide (or scalar) zero reset literal."""
    return Const(0) if opts.width == 1 else Const(0, width=Ref("WIDTH"))


def _edge_expr(opts: EdgeDetectorOptions) -> BinOp:
    """The combinational edge-detect expression over ``d`` and the delayed ``d_q``.

    - rising:  d & ~d_q
    - falling: ~d & d_q
    - both:    d ^ d_q
    """
    d = Ref("d")
    d_q = Ref("d_q")
    if opts.detect == "rising":
        return BinOp(BinOpKind.AND, d, UnaryOp(UnaryOpKind.NOT_BITWISE, d_q))
    if opts.detect == "falling":
        return BinOp(BinOpKind.AND, UnaryOp(UnaryOpKind.NOT_BITWISE, d), d_q)
    # both
    return BinOp(BinOpKind.XOR, d, d_q)


def generate(opts: EdgeDetectorOptions) -> Module:
    """Build the edge-detector IR ``Module`` (pure).

    Structure:

    - always one ``AlwaysFF`` holding the ``d_q`` delay register (``d_q <= d``);
    - ``registered_output=True``: the same process also holds ``pulse`` as a
      register (``pulse <= <edge expr>``) — ``pulse`` is an output flop;
    - ``registered_output=False``: ``pulse`` is a combinational ``ContAssign``
      of the edge expression, and only ``d_q`` lives in the process.

    The renderer decides always_ff vs always, ``<=`` vs ``=``, and reset
    composition (IR_SPEC design rules 2-4); the generator only chooses the logic.
    """
    dtype = _dtype(opts)
    reset = _reset_spec(opts)
    edge = _edge_expr(opts)

    # --- ports (order per clean-rtl: clock, reset, data-in, data-out) -------
    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
        Port("d", IN, dtype, doc="Input signal to detect edges on"),
        Port("pulse", OUT, dtype, doc=_pulse_doc(opts)),
    ]

    # --- internal delay register d_q (always present) -----------------------
    signals: list = [Signal("d_q", dtype, doc="Previous-cycle value of d (delay register)")]

    # --- clocked body -------------------------------------------------------
    body: list = [
        Comment(
            f"{opts.detect}-edge detector: sample d, compare against d_q",
            level=CommentLevel.VERBOSE,
        ),
        Assign(Ref("d_q"), Ref("d")),
    ]
    reset_body: list = [Assign(Ref("d_q"), _zero_const(opts))]

    items: list = []
    if opts.registered_output:
        # pulse is an output flop: register the edge expression one more cycle.
        body.append(Assign(Ref("pulse"), edge))
        reset_body.append(Assign(Ref("pulse"), _zero_const(opts)))
    else:
        # pulse is combinational: continuous assignment of the edge expression.
        items.append(ContAssign(Ref("pulse"), edge))

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=reset,
        reset_body=reset_body,
        body=body,
    )
    items = [*signals, always, *items]

    params = []
    if opts.width > 1:
        params.append(Param("WIDTH", Const(opts.width), doc="Signal bit width"))

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


def _reset_port_name(opts: EdgeDetectorOptions) -> str:
    """Reset port name as it appears in the explanation/RTL (``rst_n`` when
    active-low). ``port_groups`` uses this so the doc port table joins cleanly
    against the ExplanationDoc signals."""
    return "rst" + ("_n" if opts.reset_polarity == "active_low" else "")


def port_groups(opts: EdgeDetectorOptions) -> list[PortGroup]:
    """Group ports for the datasheet: a clocking group and a data group."""
    return [
        PortGroup(
            name="Clocking",
            ports=["clk", _reset_port_name(opts)],
            description="Clock and reset for the sampling and (optional) output registers.",
        ),
        PortGroup(
            name="Data",
            ports=["d", "pulse"],
            description=(
                "Input signal and the detected-edge pulse output "
                f"({'registered' if opts.registered_output else 'combinational'})."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Smoke-TB recipe
# ---------------------------------------------------------------------------


def tb_spec(opts: EdgeDetectorOptions) -> TbSpec:
    """A ~6-vector directed smoke TB with two honest expected-value checks.

    The vectors drive ``d`` through a rising and a falling transition; the two
    checks assert the pulse behaviour for the selected ``detect`` direction one
    cycle after the relevant edge (accounting for the extra cycle of latency
    when ``registered_output`` is set). Checks are declarative recipes; they are
    NOT executed yet (the P2-13 TB generator will consume this).
    """
    lo, hi = 0, (1 << opts.width) - 1  # all-zeros / all-ones for the chosen width

    # Six single-bit-style vectors driving d: hold low, rise, hold high, fall,
    # hold low. (For width>1 the same all-lo/all-hi levels exercise every bit.)
    vectors: list[dict[str, int]] = [
        {"d": lo},  # cycle 0: baseline low
        {"d": hi},  # cycle 1: rising edge here
        {"d": hi},  # cycle 2: hold high
        {"d": lo},  # cycle 3: falling edge here
        {"d": lo},  # cycle 4: hold low
        {"d": hi},  # cycle 5: rising edge again
    ]

    # One cycle of latency for registered output, zero for combinational. The
    # rising edge is applied at cycle 1, the falling edge at cycle 3.
    latency = 1 if opts.registered_output else 0
    rise_cycle = 1 + latency
    fall_cycle = 3 + latency

    checks: list[Check] = []
    if opts.detect in ("rising", "both"):
        checks.append(Check(cycle=rise_cycle, signal="pulse", expected=hi))
    if opts.detect in ("falling", "both"):
        checks.append(Check(cycle=fall_cycle, signal="pulse", expected=hi))
    # 'rising' has no falling check and vice-versa; ensure two honest checks by
    # asserting the pulse is low on a steady-state cycle for the single-edge
    # modes (cycle 2 is a hold-high steady state -> no new edge -> pulse low).
    if opts.detect == "rising":
        checks.append(Check(cycle=2 + latency, signal="pulse", expected=lo))
    elif opts.detect == "falling":
        checks.append(Check(cycle=4 + latency, signal="pulse", expected=lo))

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


def _detect_word(opts: EdgeDetectorOptions) -> str:
    return {"rising": "rising", "falling": "falling", "both": "any (both)"}[opts.detect]


def _description(opts: EdgeDetectorOptions) -> str:
    width_word = f"{opts.width}-bit " if opts.width > 1 else ""
    return f"{_detect_word(opts).capitalize()}-edge detector, {width_word}one-cycle pulse".replace(
        "  ", " "
    )


def _reset_doc(opts: EdgeDetectorOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _pulse_doc(opts: EdgeDetectorOptions) -> str:
    reg = "registered" if opts.registered_output else "combinational"
    return f"One-cycle {_detect_word(opts)}-edge pulse ({reg} output)"


def _reset_behavior_text(opts: EdgeDetectorOptions) -> str:
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
    target = (
        "the delay register d_q and the pulse output register"
        if opts.registered_output
        else "the delay register d_q"
    )
    return (
        f"The {pol} reset clears {target} {style} {edge}, so no spurious pulse is "
        "produced immediately after reset release."
    )


def explain(opts: EdgeDetectorOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    output_word = (
        "registered (one extra cycle of latency)"
        if opts.registered_output
        else "combinational (no extra latency)"
    )
    configuration = [
        f"Detect: {_detect_word(opts)} edge",
        f"Width: {opts.width} bit(s)",
        f"Output: {output_word}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    width_word = f"{opts.width}-bit" if opts.width > 1 else "single-bit"
    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; d is sampled on the rising edge.",
        ),
        SignalDoc(
            name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
            direction="input",
            description=_reset_doc(opts) + " reset input.",
        ),
        SignalDoc(
            name="d",
            direction="input",
            description=f"{width_word} input signal whose edges are detected.",
        ),
        SignalDoc(
            name="d_q",
            direction="internal",
            description="One-cycle delayed copy of d, compared against d to detect an edge.",
        ),
        SignalDoc(
            name="pulse",
            direction="output",
            description=(
                f"One-cycle {_detect_word(opts)}-edge pulse, "
                + (
                    "registered (asserted one cycle after the edge)."
                    if opts.registered_output
                    else "combinational (asserted the same cycle the edge is observed)."
                )
            ),
        ),
    ]

    assumptions = [
        "A single free-running clock drives the detector; d is sampled synchronously to it.",
        "d is already synchronous to clk (no metastability handling here); use a "
        "CDC synchronizer upstream if d crosses clock domains.",
    ]

    limitations = [
        "Detects transitions of d as sampled at the clock edge: a pulse on d "
        "narrower than one clock period, or between sampling edges, can be "
        "missed entirely.",
        "Single clock domain only; this module performs no clock-domain "
        "crossing (CDC) synchronization on d.",
    ]
    if opts.width > 1:
        limitations.append(
            "Each of the WIDTH bits is edge-detected independently; there is no "
            "cross-bit coherency guarantee for multi-bit buses."
        )

    latency_word = "one cycle after" if opts.registered_output else "the same cycle as"
    return ExplanationDoc(
        purpose=(
            f"A {width_word} {_detect_word(opts)}-edge detector: it emits a "
            f"one-clock-wide pulse on pulse {latency_word} a qualifying "
            "transition on d."
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
class _EdgeDetectorModule:
    """Bundles the edge detector's metadata and pure functions.

    Satisfies the :class:`~.contract.ModuleDef` protocol structurally.
    """

    id: str = "edge-detector"
    name: str = "Edge Detector"
    description: str = (
        "Emits a one-cycle pulse on a rising, falling, or any transition of an "
        "input signal (per-bit, optionally registered)."
    )
    kind: str = "module"
    maturity: str = "stable"
    options_model: type[EdgeDetectorOptions] = EdgeDetectorOptions

    def generate(self, opts: EdgeDetectorOptions) -> Module:
        return generate(opts)

    def explain(self, opts: EdgeDetectorOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: EdgeDetectorOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: EdgeDetectorOptions) -> TbSpec:
        return tb_spec(opts)


MODULE = _EdgeDetectorModule()


__all__ = [
    "EdgeDetectorOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "MODULE",
]
