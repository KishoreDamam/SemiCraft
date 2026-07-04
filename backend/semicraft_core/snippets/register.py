"""Register snippet (WP-05a): parameterizable synchronous register.

Follows the ``counter.py`` reference structure (WP-03) exactly: an options
model extending :class:`ClockedOptions`, a pure ``generate()`` building IR, a
pure ``explain()``, and a module-level ``SNIPPET`` instance.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field, model_validator

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    AlwaysFF,
    Assign,
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
)
from ..version import VERSION
from .contract import ClockedOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class RegisterOptions(ClockedOptions):
    """Configuration for the register snippet.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments,
    naming) with the register-specific fields below.
    """

    width: int = Field(
        default=8,
        ge=1,
        le=1024,
        description="Register width in bits. Both d and q are WIDTH bits wide.",
    )
    enable: bool = Field(
        default=True,
        description="Add an 'en' input that gates loading; when low, the register holds its value.",
    )
    reset_value: int = Field(
        default=0,
        ge=0,
        description="Value loaded into the register on reset. Must be < 2^width.",
    )
    clear_input: bool = Field(
        default=False,
        description=(
            "Add a synchronous 'clr' input. When asserted, the register loads "
            "reset_value on the next clock edge regardless of 'en' (clear beats "
            "enable)."
        ),
    )

    # ``reset_value`` is the only cross-field rule: it must fit in the declared
    # width (PRD §11 — never generate a truncated constant silently).
    @model_validator(mode="after")
    def _check(self) -> RegisterOptions:
        if self.reset_value >= (1 << self.width):
            raise ValueError(
                f"reset_value {self.reset_value} does not fit in width={self.width} "
                f"(must be < 2^{self.width} = {1 << self.width})"
            )
        return self


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "register"


def _reset_spec(opts: RegisterOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _reset_value_const(opts: RegisterOptions) -> Const:
    """WIDTH-wide reset literal. ``0`` renders as ``{WIDTH{1'b0}}`` (IR_SPEC §9);
    a non-zero value renders as a sized literal composed against ``WIDTH``."""
    return Const(opts.reset_value, width=Ref("WIDTH"))


def _load_body(opts: RegisterOptions) -> list:
    """The clocked-body statements implementing clear-beats-enable priority.

    - Neither clear nor enable configured: unconditional load every cycle.
    - Enable only: load only while 'en' is high (holds otherwise).
    - Clear only: load reset_value only while 'clr' is high, else load 'd'
      every other cycle (no enable to hold against).
    - Both: clear takes priority over enable. When 'clr' is asserted the
      register loads reset_value regardless of 'en'; otherwise it loads 'd'
      only while 'en' is high.
    """
    load_d = Assign(Ref("q"), Ref("d"))
    load_reset = Assign(Ref("q"), _reset_value_const(opts))

    if opts.clear_input and opts.enable:
        # clear beats enable: clr checked first, en only gates the else branch.
        return [
            If(
                Ref("clr"),
                then=[load_reset],
                else_=[If(Ref("en"), then=[load_d])],
            )
        ]
    if opts.clear_input:
        # clear only (no enable): clr loads reset_value, else load d unconditionally.
        return [If(Ref("clr"), then=[load_reset], else_=[load_d])]
    if opts.enable:
        return [If(Ref("en"), then=[load_d])]
    return [load_d]


def generate(opts: RegisterOptions) -> Module:
    """Build the register IR ``Module`` (pure). One ``AlwaysFF``, one ``Param``.

    The generator only decides *what* logic exists (clear-beats-enable
    priority); the renderer decides always_ff vs always, <= vs =, and reset
    composition (IR_SPEC design rules 2-4).
    """
    # --- ports (order per clean-rtl: clock, reset, control, data) -----------
    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
    ]
    if opts.clear_input:
        ports.append(
            Port("clr", IN, bit(), doc="Synchronous clear (loads reset_value; beats enable)")
        )
    if opts.enable:
        ports.append(Port("en", IN, bit(), doc="Load enable (holds value when low)"))
    ports.append(Port("d", IN, vec("WIDTH"), doc="Data input"))
    ports.append(Port("q", OUT, vec("WIDTH"), doc="Registered data output"))

    # --- clocked body ---------------------------------------------------
    body: list = [
        Comment(
            f"{opts.width}-bit register"
            + (", synchronous clear beats enable" if opts.clear_input and opts.enable else ""),
            level=CommentLevel.VERBOSE,
        )
    ]
    body.extend(_load_body(opts))

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=_reset_spec(opts),
        reset_body=[Assign(Ref("q"), _reset_value_const(opts))],
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
        params=[Param("WIDTH", Const(opts.width), doc="Register width in bits")],
        ports=ports,
        items=[always],
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _description(opts: RegisterOptions) -> str:
    return f"{opts.width}-bit synchronous register"


def _reset_doc(opts: RegisterOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _reset_behavior_text(opts: RegisterOptions) -> str:
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
        f"The {pol} reset resets the register {style} {edge}, loading "
        f"{opts.reset_value} into q."
    )


def explain(opts: RegisterOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    configuration = [
        f"Width: {opts.width} bits",
        f"Enable input: {'yes' if opts.enable else 'no'}",
        f"Synchronous clear input: {'yes' if opts.clear_input else 'no'}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Reset value: {opts.reset_value}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; the register updates on the rising edge.",
        ),
        SignalDoc(
            name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
            direction="input",
            description=_reset_doc(opts) + " reset input.",
        ),
    ]
    if opts.clear_input:
        signals.append(
            SignalDoc(
                name="clr",
                direction="input",
                description=(
                    "Synchronous clear; when high, the register loads "
                    f"{opts.reset_value} on the next clock edge, regardless of "
                    "'en' (clear beats enable)."
                ),
            )
        )
    if opts.enable:
        signals.append(
            SignalDoc(
                name="en",
                direction="input",
                description="Load enable; when low the register holds its current value.",
            )
        )
    signals.append(
        SignalDoc(name="d", direction="input", description=f"{opts.width}-bit data input.")
    )
    signals.append(
        SignalDoc(
            name="q",
            direction="output",
            description=f"Registered {opts.width}-bit data output.",
        )
    )

    if opts.clear_input and opts.enable:
        enable_behavior = (
            "When clr is high the register loads reset_value on the next clock "
            "edge regardless of en (clear has priority). Otherwise, when en is "
            "high the register loads d on each clock edge; when en is low it "
            "holds its current value."
        )
    elif opts.enable:
        enable_behavior = (
            "When en is high the register loads d on each clock edge; when en "
            "is low it holds its current value."
        )
    else:
        enable_behavior = None

    assumptions = [
        "A single free-running clock drives the register; all I/O is synchronous to it.",
        "The reset input is glitch-free and (for async reset) released synchronously.",
    ]
    if opts.clear_input:
        assumptions.append(
            "clr is a synchronous control, stable around the clock edge, and is "
            "evaluated with strictly higher priority than en."
        )

    limitations = [
        "Single clock domain only; this snippet performs no clock-domain "
        "crossing (CDC) synchronization on its inputs or outputs.",
    ]
    if opts.clear_input and opts.enable:
        limitations.append(
            "clr and en cannot both gate a load in the same cycle: clr always "
            "wins, so an asserted en is ignored whenever clr is also asserted."
        )

    return ExplanationDoc(
        purpose=(
            f"A {opts.width}-bit synchronous register"
            + (" with load enable" if opts.enable else "")
            + (" and synchronous clear" if opts.clear_input else "")
            + "."
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
class _RegisterSnippet:
    """Bundles the register's metadata and pure ``generate``/``explain`` fns.

    Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "register"
    name: str = "Register"
    description: str = "Parameterizable synchronous register (enable, synchronous clear)."
    options_model: type[RegisterOptions] = RegisterOptions

    def generate(self, opts: RegisterOptions) -> Module:
        return generate(opts)

    def explain(self, opts: RegisterOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _RegisterSnippet()


__all__ = ["RegisterOptions", "generate", "explain", "SNIPPET"]
