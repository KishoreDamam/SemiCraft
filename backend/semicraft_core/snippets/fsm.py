"""Hero snippet: finite state machine skeleton (WP-05i).

The FSM is the showcase snippet — it exercises the two IR features no other
snippet touches (``EnumDecl`` state encodings and ``Case`` over an enum) and
carries the richest explanation. It deliberately emits a *skeleton*: full state
declarations, a correct two-process (Moore) or output-in-transition (Mealy)
structure, encoding applied at declaration, and a ``TODO`` comment in every
transition arm. The transition and output logic is left for the user to fill in
— that is the design, not an omission (IMPLEMENTATION_PLAN §5 WP-05i).

Anatomy (following the counter reference, IR_SPEC §5 normative)
--------------------------------------------------------------

1. One ``EnumDecl`` (``state_t``) with the chosen encoding. Encoding is applied
   at declaration only (SV enum values / Verilog localparams); the case
   structure never changes when the encoding does.
2. State signals ``state`` and ``state_next`` declared as plain logic vectors
   (legal SV — the register drives the raw vector, not the typed enum). Their
   width matches the encoding: binary/gray = ceil(log2(N)), onehot = N.
3. State register ``AlwaysFF``: reset -> ``EnumRef(reset_state)``; body
   ``Assign(state, state_next)``.
4. Next-state ``AlwaysComb``: FIRST ``Assign(state_next, state)`` (the no-latch,
   hold-on-undefined default), THEN a ``unique`` ``Case`` over ``state`` with one
   arm per state — full enum coverage, so no default arm — each arm carrying a
   ``TODO`` comment for the user to complete.
5. Outputs: Moore -> a separate ``AlwaysComb`` that default-assigns every output
   to 0 then has a per-state ``Case`` with TODO comments; Mealy -> outputs are
   defaulted in the next-state block and their TODO comments note that Mealy
   outputs belong in the transition arms.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    AlwaysComb,
    AlwaysFF,
    Assign,
    Case,
    CaseItem,
    ClockSpec,
    Comment,
    CommentLevel,
    Const,
    EnumDecl,
    EnumEncoding,
    EnumRef,
    Header,
    Module,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
)
from ..version import VERSION
from .contract import ClockedOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------

_IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Emitted names the user options must not collide with (ports + internals).
# ``rst`` is included even though the rendered name may become ``rst_n`` — the
# canonical IR name is ``rst`` and we reserve it either way.
_RESERVED_NAMES = frozenset({"clk", "rst", "state", "state_next", "state_t"})


class FsmOptions(ClockedOptions):
    """Configuration for the FSM snippet.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments, naming)
    with the FSM-specific fields below. The state list is the only non-scalar
    option in the whole snippet catalog; the frontend renders it as a tag/chips
    input (IMPLEMENTATION_PLAN §7 risk "FSM options UX").
    """

    states: list[str] = Field(
        default_factory=lambda: ["idle", "run", "done"],
        min_length=2,
        max_length=16,
        description=(
            "State names, each a valid lower_snake_case identifier, unique. "
            "2-16 states. Become enum members (SV) or localparams (Verilog)."
        ),
    )
    encoding: Literal["binary", "onehot", "gray"] = Field(
        default="binary",
        description=(
            "State encoding. 'binary' is area-efficient (ceil(log2 N) bits); "
            "'onehot' uses one bit per state for fast, cheap decode (FPGA "
            "friendly); 'gray' changes one bit per adjacent transition, "
            "reducing switching glitches and easing CDC of the state vector."
        ),
    )
    machine: Literal["moore", "mealy"] = Field(
        default="moore",
        description=(
            "Machine type. 'moore' outputs depend on the current state only "
            "(registered, glitch-free); 'mealy' outputs depend on state and "
            "inputs (fewer states, but combinational input-to-output paths)."
        ),
    )
    reset_state: str | None = Field(
        default=None,
        description=(
            "State entered on reset. Must be one of 'states'. Defaults to the "
            "first state in the list when omitted."
        ),
    )
    outputs: list[str] = Field(
        default_factory=list,
        max_length=8,
        description=(
            "Output port names (0-8), each a valid lower_snake_case identifier, "
            "unique. Each becomes a 1-bit output with a TODO skeleton in the "
            "output logic. Empty for a state-only FSM."
        ),
    )

    @model_validator(mode="after")
    def _check(self) -> FsmOptions:
        # --- states: identifiers, unique, not reserved ----------------------
        for s in self.states:
            if not _IDENT_RE.match(s):
                raise ValueError(
                    f"state {s!r} is not a valid lower_snake_case identifier "
                    "(must match ^[a-z][a-z0-9_]*$)"
                )
            if s in _RESERVED_NAMES:
                raise ValueError(
                    f"state {s!r} collides with an emitted signal/port name "
                    f"({sorted(_RESERVED_NAMES)})"
                )
        if len(set(self.states)) != len(self.states):
            dupes = sorted({s for s in self.states if self.states.count(s) > 1})
            raise ValueError(f"state names must be unique; duplicates: {dupes}")

        # --- outputs: identifiers, unique, no collisions --------------------
        state_set = set(self.states)
        seen: set[str] = set()
        for o in self.outputs:
            if not _IDENT_RE.match(o):
                raise ValueError(
                    f"output {o!r} is not a valid lower_snake_case identifier "
                    "(must match ^[a-z][a-z0-9_]*$)"
                )
            if o in _RESERVED_NAMES:
                raise ValueError(
                    f"output {o!r} collides with an emitted signal/port name "
                    f"({sorted(_RESERVED_NAMES)})"
                )
            if o in state_set:
                raise ValueError(f"output {o!r} collides with a state name")
            if o in seen:
                raise ValueError(f"output names must be unique; duplicate: {o!r}")
            seen.add(o)

        # --- reset_state: must be a declared state --------------------------
        if self.reset_state is not None and self.reset_state not in state_set:
            raise ValueError(
                f"reset_state {self.reset_state!r} is not one of states "
                f"{self.states!r}"
            )
        return self

    @property
    def resolved_reset_state(self) -> str:
        """The reset state, defaulting to the first state when unset."""
        return self.reset_state if self.reset_state is not None else self.states[0]


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "fsm"
_ENUM_NAME = "state_t"


def _state_width(opts: FsmOptions) -> int:
    """Width of the state vector, matching ``render.base.enum_layout``.

    onehot -> N; binary/gray -> max(1, ceil(log2 N)). Kept in sync so the
    declared ``state``/``state_next`` signals are wide enough for the encoding.
    """
    n = len(opts.states)
    if opts.encoding == "onehot":
        return n
    return max(1, (n - 1).bit_length())


def _encoding_enum(opts: FsmOptions) -> EnumEncoding:
    return {
        "binary": EnumEncoding.BINARY,
        "onehot": EnumEncoding.ONEHOT,
        "gray": EnumEncoding.GRAY,
    }[opts.encoding]


def _reset_spec(opts: FsmOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _next_state_block(opts: FsmOptions) -> AlwaysComb:
    """Next-state logic: default-hold first, then one TODO arm per state.

    Full enum coverage (one arm per member) means no default arm is needed
    (IR_SPEC §6 rule 5). ``unique=True`` documents that the arms are mutually
    exclusive.
    """
    mealy = opts.machine == "mealy"
    body: list = []

    if mealy and opts.outputs:
        # Mealy outputs are defaulted here (they may be assigned inside the
        # transition arms), so no output logic block latches.
        body.append(
            Comment("default Mealy outputs (override in transition arms below)")
        )
        for o in opts.outputs:
            body.append(Assign(Ref(o), Const(0, width=None)))

    # No-latch default: hold the current state unless a transition fires.
    body.append(Comment("default: hold current state (no-latch guarantee)"))
    body.append(Assign(Ref("state_next"), Ref("state")))

    items: list[CaseItem] = []
    for s in opts.states:
        arm: list = [Comment(f"TODO: transition logic for {s}")]
        if mealy and opts.outputs:
            arm.append(
                Comment("TODO: Mealy outputs for this state belong here")
            )
        items.append(CaseItem([EnumRef(_ENUM_NAME, s)], arm))

    # Empty default arm: the state vector can physically hold encodings
    # outside the enum (e.g. 3 states in 2 bits, or non-onehot patterns), so
    # Verilator flags a defaultless case as CASEINCOMPLETE. The pre-case
    # default assignment already defines behavior (hold state).
    body.append(Case(sel=Ref("state"), items=items, unique=True, default=[]))
    return AlwaysComb(body)


def _output_block(opts: FsmOptions) -> AlwaysComb:
    """Moore output logic: default all outputs to 0, then a per-state case.

    Default-first assignment guarantees no latch; each arm carries a TODO for
    the user to set the outputs active in that state.
    """
    body: list = [Comment("default all outputs inactive (no-latch guarantee)")]
    for o in opts.outputs:
        body.append(Assign(Ref(o), Const(0, width=None)))

    items = [
        CaseItem(
            [EnumRef(_ENUM_NAME, s)],
            [Comment(f"TODO: Moore outputs for state {s}")],
        )
        for s in opts.states
    ]
    # Empty default arm for the same CASEINCOMPLETE reason as the next-state
    # case; outputs are already default-assigned above.
    body.append(Case(sel=Ref("state"), items=items, unique=True, default=[]))
    return AlwaysComb(body)


def generate(opts: FsmOptions) -> Module:
    """Build the FSM skeleton IR ``Module`` (pure).

    One ``EnumDecl``, two state signals, a state-register ``AlwaysFF``, a
    next-state ``AlwaysComb``, and (Moore only) an output ``AlwaysComb``. The
    renderer turns this identical IR into either language and any reset variant
    (IR_SPEC design rules 2-4).
    """
    reset_state = opts.resolved_reset_state
    sw = _state_width(opts)

    # --- ports (clean-rtl order: clock, reset, then outputs) ----------------
    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
    ]
    for o in opts.outputs:
        kind = "Moore" if opts.machine == "moore" else "Mealy"
        ports.append(Port(o, OUT, bit(), doc=f"{kind} output (TODO: drive)"))

    # --- state type + registers ---------------------------------------------
    enum = EnumDecl(_ENUM_NAME, opts.states, _encoding_enum(opts))
    state_sig = Signal("state", vec(sw), doc="Current state")
    state_next_sig = Signal("state_next", vec(sw), doc="Next state (comb)")

    # State register: reset to the reset state, else advance to state_next.
    state_reg = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=_reset_spec(opts),
        reset_body=[Assign(Ref("state"), EnumRef(_ENUM_NAME, reset_state))],
        body=[Assign(Ref("state"), Ref("state_next"))],
    )

    items: list = [
        enum,
        state_sig,
        state_next_sig,
        Comment("State register", level=CommentLevel.VERBOSE),
        state_reg,
        Comment("Next-state logic (transitions are user-completed)"),
        _next_state_block(opts),
    ]
    if opts.machine == "moore" and opts.outputs:
        items.append(Comment("Moore output logic"))
        items.append(_output_block(opts))

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by the generate() entry point
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[],
        ports=ports,
        items=items,
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _reset_doc(opts: FsmOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _description(opts: FsmOptions) -> str:
    return (
        f"{opts.machine.capitalize()} FSM, {len(opts.states)} states, "
        f"{opts.encoding} encoding"
    )


def _encoding_text(opts: FsmOptions) -> str:
    sw = _state_width(opts)
    return {
        "binary": (
            f"Binary encoding: {sw}-bit dense state vector "
            "(area-efficient; ceil(log2 N) flops)."
        ),
        "onehot": (
            f"One-hot encoding: {sw}-bit vector, one bit per state "
            "(fast, cheap single-bit state decode; FPGA-friendly)."
        ),
        "gray": (
            f"Gray encoding: {sw}-bit vector where adjacent states differ in "
            "one bit (reduces switching glitches; eases CDC of the state)."
        ),
    }[opts.encoding]


def _machine_text(opts: FsmOptions) -> str:
    if opts.machine == "moore":
        return (
            "Moore machine: outputs are a function of the current state only, "
            "so they are glitch-free and easy to time."
        )
    return (
        "Mealy machine: outputs depend on the current state and the inputs, "
        "which can reduce the state count but introduces combinational "
        "input-to-output paths."
    )


def _reset_behavior_text(opts: FsmOptions) -> str:
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
        f"The {pol} reset forces the machine {style} {edge} into the "
        f"'{opts.resolved_reset_state}' state."
    )


def explain(opts: FsmOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options (hero snippet)."""
    configuration = [
        f"States ({len(opts.states)}): {', '.join(opts.states)}",
        f"Machine type: {opts.machine}",
        f"Encoding: {opts.encoding}",
        f"Reset state: {opts.resolved_reset_state}",
        f"Outputs: {', '.join(opts.outputs) if opts.outputs else 'none'}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; the state register updates on the rising edge.",
        ),
        SignalDoc(
            name="rst" + ("_n" if opts.reset_polarity == "active_low" else ""),
            direction="input",
            description=_reset_doc(opts) + " reset input.",
        ),
    ]
    for o in opts.outputs:
        kind = "Moore" if opts.machine == "moore" else "Mealy"
        signals.append(
            SignalDoc(
                name=o,
                direction="output",
                description=(
                    f"{kind} output (skeleton: currently driven inactive; "
                    "complete the TODO in the output logic)."
                ),
            )
        )
    signals.append(
        SignalDoc(
            name="state",
            direction="internal",
            description=(
                f"Current-state register ({_state_width(opts)}-bit, "
                f"{opts.encoding} encoding)."
            ),
        )
    )
    signals.append(
        SignalDoc(
            name="state_next",
            direction="internal",
            description="Combinational next-state value (defaults to state).",
        )
    )

    purpose = (
        f"A {len(opts.states)}-state {opts.machine} finite state machine "
        f"skeleton with {opts.encoding} encoding. It provides the state type, "
        "state register, and a fully-covered next-state case; the transition "
        "and output logic are marked TODO for you to complete."
    )

    assumptions = [
        "A single free-running clock drives the machine; all I/O is synchronous to it.",
        "The reset input is glitch-free and (for async reset) released synchronously.",
        (
            "The next-state case is exhaustive over all states, so the state "
            "vector never takes an undefined value in normal operation."
        ),
    ]

    limitations = [
        (
            "This is a skeleton: every transition arm and output is a TODO "
            "comment. The generated FSM holds its reset state until you fill in "
            "the transitions — it is not a working machine as emitted."
        ),
        (
            "No inputs are generated for the transition conditions; add the "
            "condition ports your transitions need when completing the arms."
        ),
        (
            "Single clock domain only; this snippet performs no clock-domain "
            "crossing (CDC) synchronization. Gray encoding reduces state-vector "
            "glitches but is not a substitute for a CDC synchronizer."
        ),
    ]
    if opts.machine == "mealy" and opts.outputs:
        limitations.append(
            "Mealy outputs are combinational functions of the inputs and so "
            "may glitch within a cycle; register them downstream if a clean "
            "single-cycle pulse is required."
        )

    return ExplanationDoc(
        purpose=purpose,
        configuration=configuration,
        signals=signals,
        reset_behavior=_reset_behavior_text(opts),
        enable_behavior=None,
        assumptions=assumptions
        + [_encoding_text(opts), _machine_text(opts)],
        limitations=limitations,
    )


# ---------------------------------------------------------------------------
# SnippetDef instance (discovered by the registry)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _FsmSnippet:
    """Bundles the FSM's metadata and pure ``generate``/``explain`` fns.

    Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "fsm"
    name: str = "Finite State Machine"
    description: str = (
        "State machine skeleton (enum states, Moore/Mealy, "
        "binary/onehot/gray encoding) with TODO transition logic."
    )
    options_model: type[FsmOptions] = FsmOptions

    def generate(self, opts: FsmOptions) -> Module:
        return generate(opts)

    def explain(self, opts: FsmOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _FsmSnippet()


__all__ = ["FsmOptions", "generate", "explain", "SNIPPET"]
