"""Reference snippet: parameterizable binary counter (WP-03 task 3).

This is THE reference implementation. Nine later snippet WPs (WP-05a..i) copy
its structure, so it is deliberately over-commented at the level of *intent*:
what each option does to the IR and why, not what each line of Python does.

Anatomy of a snippet (the template others follow)
-------------------------------------------------

1. An options model (Pydantic) extending :class:`ClockedOptions` (clocked) or
   :class:`CommonOptions` (combinational). Every extra field has a constraint
   and a ``Field(description=...)``. Cross-field rules use ``model_validator``
   so illegal combinations fail validation instead of silently generating
   wrong code (PRD §11 / IMPLEMENTATION_PLAN §3 task 3).
2. ``generate(opts) -> Module`` — a pure function building IR per IR_SPEC. It
   never decides ``always_ff`` vs ``always``, ``<=`` vs ``=``, or reset
   composition; those are the renderer's job (IR_SPEC design rules 2-4). The
   generator only chooses *what* logic exists, expressed as a single
   ``ResetSpec`` and one ``AlwaysFF``.
3. ``explain(opts) -> ExplanationDoc`` — every field populated for the actual
   chosen options.
4. A module-level ``SnippetDef`` instance named ``SNIPPET`` (the registry
   discovers it by structural type, so the name is not load-bearing).
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
    Ternary,
)
from ..version import VERSION
from .contract import ClockedOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class CounterOptions(ClockedOptions):
    """Configuration for the counter snippet.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments, naming)
    with the counter-specific fields below.
    """

    width: int = Field(
        default=8,
        ge=1,
        le=1024,
        description="Counter width in bits. The count output is WIDTH bits wide.",
    )
    direction: Literal["up", "down", "updown"] = Field(
        default="up",
        description=(
            "Count direction. 'up' increments, 'down' decrements, 'updown' "
            "adds an up_dn input (1 = count up, 0 = count down)."
        ),
    )
    enable: bool = Field(
        default=True,
        description="Add an 'en' input that gates counting; when low, the count holds.",
    )
    wrap: Literal["overflow", "saturate"] = Field(
        default="overflow",
        description=(
            "Boundary behavior. 'overflow' wraps modulo 2^WIDTH; 'saturate' "
            "stops at the maximum (up) or minimum (down) value."
        ),
    )
    reset_value: int = Field(
        default=0,
        ge=0,
        description="Value loaded into the counter on reset. Must be < 2^width.",
    )

    # ``direction`` and ``wrap`` are validated natively as Literals (so the JSON
    # Schema advertises proper enums and bad values are rejected). This
    # validator handles the only *cross-field* rule: reset_value must fit in the
    # declared width (PRD §11 — never generate a truncated constant silently).
    @model_validator(mode="after")
    def _check(self) -> CounterOptions:
        if self.reset_value >= (1 << self.width):
            raise ValueError(
                f"reset_value {self.reset_value} does not fit in width={self.width} "
                f"(must be < 2^{self.width} = {1 << self.width})"
            )
        return self


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "counter"


def _reset_spec(opts: CounterOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _reset_value_const(opts: CounterOptions) -> Const:
    """WIDTH-wide reset literal. ``0`` renders as ``{WIDTH{1'b0}}`` (IR_SPEC §9);
    a non-zero value renders as a sized literal composed against ``WIDTH``."""
    return Const(opts.reset_value, width=Ref("WIDTH"))


def _step_expr(opts: CounterOptions) -> BinOp | Ternary:
    """The next-count expression for one enabled tick, before saturation.

    - up:     count + 1
    - down:   count - 1
    - updown: up_dn ? count + 1 : count - 1
    """
    inc = BinOp(BinOpKind.ADD, Ref("count"), Const(1))
    dec = BinOp(BinOpKind.SUB, Ref("count"), Const(1))
    if opts.direction == "up":
        return inc
    if opts.direction == "down":
        return dec
    # updown: select at runtime on the up_dn input.
    return Ternary(cond=Ref("up_dn"), then=inc, else_=dec)


def _all_ones(opts: CounterOptions) -> Const:
    """WIDTH-wide all-ones constant (the unsigned maximum), for saturate-up."""
    return Const((1 << opts.width) - 1, width=Ref("WIDTH"))


def _all_zeros() -> Const:
    """WIDTH-wide zero constant (the unsigned minimum), for saturate-down."""
    return Const(0, width=Ref("WIDTH"))


def _saturation_guard(opts: CounterOptions):
    """Build the count-update statement(s), applying saturate if requested.

    For 'overflow' this is a bare ``count <= <step>`` (2^WIDTH wraparound is the
    natural hardware behavior — no logic needed). For 'saturate' we compare the
    current value against the relevant boundary and hold instead of stepping.
    """
    step = _step_expr(opts)
    assign_step = Assign(Ref("count"), step)

    if opts.wrap == "overflow":
        return [assign_step]

    # saturate: guard each direction against its boundary. The comparison is the
    # "comparison logic" the option promises; holding = no assignment.
    if opts.direction == "up":
        # Stop at max: only step while count != all-ones.
        at_max = BinOp(BinOpKind.NE, Ref("count"), _all_ones(opts))
        return [If(at_max, then=[assign_step])]
    if opts.direction == "down":
        # Stop at min: only step while count != 0.
        at_min = BinOp(BinOpKind.NE, Ref("count"), _all_zeros())
        return [If(at_min, then=[assign_step])]

    # updown + saturate: gate up-steps on the max boundary and down-steps on the
    # min boundary, selected by up_dn.
    inc = BinOp(BinOpKind.ADD, Ref("count"), Const(1))
    dec = BinOp(BinOpKind.SUB, Ref("count"), Const(1))
    not_at_max = BinOp(BinOpKind.NE, Ref("count"), _all_ones(opts))
    not_at_min = BinOp(BinOpKind.NE, Ref("count"), _all_zeros())
    return [
        If(
            Ref("up_dn"),
            then=[If(not_at_max, then=[Assign(Ref("count"), inc)])],
            else_=[If(not_at_min, then=[Assign(Ref("count"), dec)])],
        )
    ]


def generate(opts: CounterOptions) -> Module:
    """Build the counter IR ``Module`` (pure). One ``AlwaysFF``, one ``Param``.

    The renderer turns this identical IR into either language and into any of
    the four reset variants — the generator stays language- and
    polarity-agnostic (IR_SPEC design rules 2-4).
    """
    # --- ports (order per clean-rtl: clock, reset, control, data) -----------
    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
    ]
    if opts.enable:
        ports.append(Port("en", IN, bit(), doc="Count enable (holds when low)"))
    if opts.direction == "updown":
        ports.append(
            Port("up_dn", IN, bit(), doc="Direction select (1 = up, 0 = down)")
        )
    ports.append(Port("count", OUT, vec("WIDTH"), doc="Current count value"))

    # --- clocked body -------------------------------------------------------
    # The count-update statements (with saturation applied). When 'enable' is
    # set, they run only while 'en' is high; otherwise they run every cycle.
    update = _saturation_guard(opts)
    body: list = [
        Comment(
            f"{opts.direction} counter, {opts.wrap} on boundary",
            level=CommentLevel.VERBOSE,
        )
    ]
    if opts.enable:
        body.append(If(Ref("en"), then=update))
    else:
        body.extend(update)

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=_reset_spec(opts),
        reset_body=[Assign(Ref("count"), _reset_value_const(opts))],
        body=body,
    )

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[Param("WIDTH", Const(opts.width), doc="Counter width in bits")],
        ports=ports,
        items=[always],
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _direction_word(opts: CounterOptions) -> str:
    return {"up": "up", "down": "down", "updown": "up/down"}[opts.direction]


def _description(opts: CounterOptions) -> str:
    return f"{_direction_word(opts).capitalize()} counter, {opts.width}-bit"


def _reset_doc(opts: CounterOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _reset_behavior_text(opts: CounterOptions) -> str:
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
        f"The {pol} reset resets the counter {style} {edge}, loading "
        f"{opts.reset_value} into count."
    )


def explain(opts: CounterOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    configuration = [
        f"Width: {opts.width} bits",
        f"Direction: {_direction_word(opts)}",
        f"Boundary behavior: {opts.wrap}"
        + (
            " (wraps modulo 2^WIDTH)"
            if opts.wrap == "overflow"
            else " (holds at the boundary value)"
        ),
        f"Enable input: {'yes' if opts.enable else 'no'}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Reset value: {opts.reset_value}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; counter updates on the rising edge.",
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
                description="Count enable; when low the count holds its value.",
            )
        )
    if opts.direction == "updown":
        signals.append(
            SignalDoc(
                name="up_dn",
                direction="input",
                description="Direction select: 1 counts up, 0 counts down.",
            )
        )
    signals.append(
        SignalDoc(
            name="count",
            direction="output",
            description=f"Current {opts.width}-bit count value.",
        )
    )

    enable_behavior = (
        "When en is high the counter updates on each clock; when en is low it "
        "holds its current value."
        if opts.enable
        else None
    )

    assumptions = [
        "A single free-running clock drives the counter; all I/O is synchronous to it.",
        "The reset input is glitch-free and (for async reset) released synchronously.",
    ]
    if opts.direction == "updown":
        assumptions.append(
            "up_dn is stable around the clock edge (treated as a synchronous control)."
        )

    limitations = []
    if opts.wrap == "overflow":
        limitations.append(
            f"On overflow the count wraps modulo 2^{opts.width} "
            f"({'up: max -> 0' if opts.direction != 'down' else 'down: 0 -> max'}); "
            "there is no carry/borrow or overflow flag output."
        )
    else:
        limitations.append(
            "In saturate mode the count stops at the boundary; there is no "
            "saturation-reached flag output."
        )
    limitations.append(
        "Single clock domain only; this snippet performs no clock-domain "
        "crossing (CDC) synchronization on its inputs or outputs."
    )

    return ExplanationDoc(
        purpose=(
            f"A {opts.width}-bit synchronous {_direction_word(opts)} counter"
            + (" with count enable" if opts.enable else "")
            + f", {opts.wrap} boundary behavior."
        ),
        configuration=configuration,
        signals=signals,
        reset_behavior=_reset_behavior_text(opts),
        enable_behavior=enable_behavior,
        assumptions=assumptions,
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# SnippetDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _CounterSnippet:
    """Bundles the counter's metadata and pure ``generate``/``explain`` fns.

    Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "counter"
    name: str = "Counter"
    description: str = "Parameterizable binary counter (up/down, enable, saturate/overflow)."
    options_model: type[CounterOptions] = CounterOptions

    def generate(self, opts: CounterOptions) -> Module:
        return generate(opts)

    def explain(self, opts: CounterOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _CounterSnippet()


__all__ = ["CounterOptions", "generate", "explain", "SNIPPET"]
