"""PWM generator module (Phase-2 P2-08).

Copies the structure of ``edge_detector.py`` (THE reference module). See
``docs/PLAN-semicraft-phases-2-8.md`` Phase 2 table + Appendix A.3 and
``backend/semicraft_core/modules/contract.py`` for the ``ModuleDef`` shape
this file implements.

What it does
------------

A free-running ``RES``-bit counter increments every clock cycle (wrapping
naturally at ``2**RES``). ``pwm_out`` is a purely combinational comparison of
the counter against the duty-cycle threshold: ``pwm_out = (counter < duty)``,
inverted when ``invert_output`` is set. The counter period is ``2**RES``
clock cycles, and ``duty`` (whether a runtime port or a fixed parameter)
selects how many of those cycles the (uninverted) output is high.

- ``duty_input="port"``: a runtime input ``duty[RES-1:0]`` lets the caller
  change the duty cycle without regenerating the module.
- ``duty_input="param"``: a fixed parameter ``DUTY`` (default
  ``2**(RES-1)``, i.e. 50%) sets the duty cycle at generation time; there is
  no runtime input.

Boundary behavior (documented, not asserted in hardware): ``duty=0`` makes
the comparison ``counter < 0`` always false, so the (uninverted) output is
constant low (constant high when inverted); ``duty=2**RES-1`` (the maximum
representable value) makes the output high for ``2**RES-1`` of the
``2**RES`` counter values — one cycle short of 100% duty, since the
comparison is strict (``<``), not ``<=``.
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


class PwmOptions(ClockedOptions):
    """Configuration for the PWM generator module.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments, naming)
    with the PWM-specific fields below.
    """

    resolution: int = Field(
        default=8,
        ge=4,
        le=16,
        description=(
            "Counter/duty width in bits (param RES). The PWM period is "
            "2**RES clock cycles."
        ),
    )
    duty_input: Literal["port", "param"] = Field(
        default="port",
        description=(
            "'port': duty[RES-1:0] is a runtime input, changeable without "
            "regenerating the module. 'param': the duty cycle is a fixed "
            "parameter DUTY (default 2**(RES-1), 50%) with no runtime input."
        ),
    )
    invert_output: bool = Field(
        default=False,
        description=(
            "When true, pwm_out is the logical inverse of the counter/duty "
            "comparison (active-low PWM)."
        ),
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "pwm"


def _reset_spec(opts: PwmOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def generate(opts: PwmOptions) -> Module:
    """Build the PWM IR ``Module`` (pure).

    Structure: one ``AlwaysFF`` holding the free-running counter (no enable,
    no explicit wrap logic needed — a RES-bit register naturally wraps modulo
    2**RES on overflow); one ``ContAssign`` computing pwm_out combinationally
    as the counter/duty comparison (optionally inverted).

    The renderer decides always_ff vs always, ``<=`` vs ``=``, and reset
    composition (IR_SPEC design rules 2-4); the generator only chooses the
    logic.
    """
    reset = _reset_spec(opts)
    dtype = vec("RES")

    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
    ]
    if opts.duty_input == "port":
        ports.append(Port("duty", IN, dtype, doc="Runtime duty-cycle threshold"))
    ports.append(Port("pwm_out", OUT, bit(), doc=_pwm_out_doc(opts)))

    signals: list = [Signal("cnt", dtype, doc="Free-running PWM period counter")]

    body = [
        Comment(
            "Free-running counter; wraps naturally modulo 2**RES",
            level=CommentLevel.VERBOSE,
        ),
        Assign(Ref("cnt"), BinOp(BinOpKind.ADD, Ref("cnt"), Const(1))),
    ]
    reset_body = [Assign(Ref("cnt"), Const(0, width=Ref("RES")))]

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=reset,
        reset_body=reset_body,
        body=body,
    )

    duty_ref = Ref("duty") if opts.duty_input == "port" else Ref("DUTY")
    compare = BinOp(BinOpKind.LT, Ref("cnt"), duty_ref)
    pwm_expr = UnaryOp(UnaryOpKind.NOT_LOGICAL, compare) if opts.invert_output else compare

    items: list = [*signals, always, ContAssign(Ref("pwm_out"), pwm_expr)]

    params = [Param("RES", Const(opts.resolution), doc="Counter/duty width in bits")]
    if opts.duty_input == "param":
        params.append(
            Param(
                "DUTY",
                Const((1 << opts.resolution) // 2, width=Ref("RES")),
                doc="Fixed duty-cycle threshold (default 50%)",
            )
        )

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


def _reset_port_name(opts: PwmOptions) -> str:
    """Reset port name as it appears in the explanation/RTL (``rst_n`` when
    active-low)."""
    return "rst" + ("_n" if opts.reset_polarity == "active_low" else "")


def port_groups(opts: PwmOptions) -> list[PortGroup]:
    """Group ports for the datasheet: a clocking group and a data group."""
    data_ports = (["duty"] if opts.duty_input == "port" else []) + ["pwm_out"]
    return [
        PortGroup(
            name="Clocking",
            ports=["clk", _reset_port_name(opts)],
            description="Clock and reset for the free-running period counter.",
        ),
        PortGroup(
            name="Data",
            ports=data_ports,
            description=(
                "Runtime duty-cycle threshold and the generated PWM output."
                if opts.duty_input == "port"
                else "Generated PWM output (duty cycle is a fixed parameter)."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Smoke-TB recipe
# ---------------------------------------------------------------------------


def tb_spec(opts: PwmOptions) -> TbSpec:
    """A directed smoke TB driving duty (when a port) through low/mid/high
    values, with two honest checks on pwm_out at cycle 0 (counter==0).

    At cycle 0, immediately out of reset, cnt==0. The output at that instant
    depends only on whether duty > 0 (uninverted) — this is checkable
    without depending on RES-specific timing, so it holds for every
    resolution.
    """
    hi = (1 << opts.resolution) - 1
    lo = 0
    mid = 1 << (opts.resolution - 1)
    on = 0 if opts.invert_output else 1
    off = 1 - on

    if opts.duty_input == "port":
        vectors: list[dict[str, int]] = [
            {"duty": lo},  # cycle 0: duty=0 -> cnt(0) < 0 is false -> 'off'
            {"duty": mid},  # cycle 1: duty=mid -> cnt(1) < mid is true -> 'on'
            {"duty": mid},
            {"duty": hi},
            {"duty": hi},
        ]
        # duty applies the same cycle it is sampled (comparison is combinational).
        checks: list[Check] = [
            Check(cycle=0, signal="pwm_out", expected=off),
            Check(cycle=1, signal="pwm_out", expected=on),
        ]
    else:
        # No runtime input; vectors just advance the clock (empty dicts). DUTY
        # defaults to 2**(RES-1) (>= 8 for the minimum resolution of 4), so
        # cnt < DUTY holds at both cnt==0 and cnt==1 -> 'on' at both checks.
        vectors = [{} for _ in range(5)]
        checks = [
            Check(cycle=0, signal="pwm_out", expected=on),
            Check(cycle=1, signal="pwm_out", expected=on),
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


def _description(opts: PwmOptions) -> str:
    inv = ", inverted" if opts.invert_output else ""
    duty_word = "runtime duty input" if opts.duty_input == "port" else "fixed duty parameter"
    return f"PWM generator, {opts.resolution}-bit, {duty_word}{inv}"


def _reset_doc(opts: PwmOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _pwm_out_doc(opts: PwmOptions) -> str:
    inv = "inverted (active-low)" if opts.invert_output else "active-high"
    return f"PWM output, {inv}"


def _reset_behavior_text(opts: PwmOptions) -> str:
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
        f"The {pol} reset clears the period counter to 0 {style} {edge}; "
        "pwm_out (combinational) follows immediately from the reset counter "
        "value and duty."
    )


def explain(opts: PwmOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    period = 1 << opts.resolution
    duty_word = (
        "a runtime input (duty)" if opts.duty_input == "port" else "a fixed parameter (DUTY)"
    )
    configuration = [
        f"Resolution: {opts.resolution} bits (period = 2^{opts.resolution} = {period} cycles)",
        f"Duty-cycle source: {duty_word}",
        f"Output polarity: {'inverted (active-low)' if opts.invert_output else 'active-high'}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; the period counter increments on the rising edge.",
        ),
        SignalDoc(
            name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
            direction="input",
            description=_reset_doc(opts) + " reset input.",
        ),
    ]
    if opts.duty_input == "port":
        signals.append(
            SignalDoc(
                name="duty",
                direction="input",
                description=(
                    f"{opts.resolution}-bit runtime duty-cycle threshold; "
                    "the output is high while the counter is below this value."
                ),
            )
        )
    signals.append(
        SignalDoc(
            name="cnt",
            direction="internal",
            description=f"Free-running {opts.resolution}-bit period counter.",
        )
    )
    signals.append(
        SignalDoc(
            name="pwm_out",
            direction="output",
            description=_pwm_out_doc(opts)
            + f"; combinational comparison of cnt against duty ({period}-cycle period).",
        )
    )

    assumptions = [
        "A single free-running clock drives the period counter.",
        "duty (when a runtime port) is stable while sampled by the "
        "combinational comparison; the caller is responsible for updating "
        "it synchronously if it varies.",
    ]

    limitations = [
        "duty=0 makes the (uninverted) output constant low for the whole "
        "period (constant high when invert_output is set), since cnt is "
        "never less than 0.",
        f"duty={period - 1} (the maximum representable value) yields the "
        f"output high for {period - 1} of the {period} counter values — one "
        "cycle short of 100% duty, since the comparison is strict (cnt < "
        "duty), not cnt <= duty.",
        "No dead-time, phase-shift, or center-aligned modes; this is a "
        "single-channel, edge-aligned PWM only.",
    ]

    return ExplanationDoc(
        purpose=(
            f"A {opts.resolution}-bit PWM generator: a free-running counter "
            f"compared against {duty_word} produces pwm_out, "
            f"{'inverted' if opts.invert_output else 'active-high'}, "
            f"with a {period}-cycle period."
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
class _PwmModule:
    """Bundles the PWM generator's metadata and pure functions.

    Satisfies the :class:`~.contract.ModuleDef` protocol structurally.
    """

    id: str = "pwm"
    name: str = "PWM Generator"
    description: str = (
        "Free-running counter compared against a runtime or fixed duty "
        "threshold to produce a single-channel PWM output."
    )
    kind: str = "module"
    maturity: str = "stable"
    options_model: type[PwmOptions] = PwmOptions

    def generate(self, opts: PwmOptions) -> Module:
        return generate(opts)

    def explain(self, opts: PwmOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: PwmOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: PwmOptions) -> TbSpec:
        return tb_spec(opts)


MODULE = _PwmModule()


__all__ = [
    "PwmOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "MODULE",
]
