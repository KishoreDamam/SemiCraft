"""Shift register snippet (IMPLEMENTATION_PLAN.md §5 WP-05b).

Follows the ``counter.py`` template (WP-03 reference): options model extending
:class:`ClockedOptions`, a pure ``generate()`` building IR, a pure ``explain()``,
and a module-level ``SNIPPET`` instance discovered by the registry.

Shift semantics
---------------

The register is a ``DEPTH``-bit vector ``q``. Each clock while shifting is
enabled, one new bit (``si``, the serial input) enters at one end and the bit
at the other end is dropped:

- ``direction="right"``: ``q <= {si, q[DEPTH-1:1]}`` — bits move toward the
  LSB; the serial output ``so`` taps the LSB (``q[0]``), i.e. the bit about to
  be shifted out next cycle.
- ``direction="left"``:  ``q <= {q[DEPTH-2:0], si}`` — bits move toward the
  MSB; ``so`` taps the MSB (``q[DEPTH-1]``).

``parallel_load`` adds a ``load`` input and a ``d[DEPTH-1:0]`` input; when
``load`` is high the register loads ``d`` in place of shifting (load beats
shift, which beats hold). ``serial_out_only`` removes the parallel output port
``q`` from the interface, exposing only ``so`` (the internal register named
``q`` still exists for the shift/load logic — only the port is omitted).
``enable`` (added here; not part of ``ClockedOptions``) gates shifting/loading
with an ``en`` input; when low the register holds.
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
    Slice,
)
from ..version import VERSION
from .contract import ClockedOptions, ExplanationDoc, SignalDoc

# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class ShiftRegisterOptions(ClockedOptions):
    """Configuration for the shift-register snippet.

    Extends :class:`ClockedOptions` (language, reset, wrapper, comments,
    naming) with the shift-register-specific fields below.
    """

    depth: int = Field(
        default=8,
        ge=2,
        le=256,
        description="Number of bits in the shift register. Emitted as parameter DEPTH.",
    )
    direction: Literal["left", "right"] = Field(
        default="right",
        description=(
            "Shift direction. 'right' shifts toward the LSB "
            "(q <= {si, q[DEPTH-1:1]}); 'left' shifts toward the MSB "
            "(q <= {q[DEPTH-2:0], si})."
        ),
    )
    parallel_load: bool = Field(
        default=False,
        description=(
            "Add a 'load' input and a 'd[DEPTH-1:0]' input. When 'load' is "
            "high the register loads 'd' instead of shifting (load beats shift)."
        ),
    )
    serial_out_only: bool = Field(
        default=False,
        description=(
            "When true, expose only the serial output 'so' (no parallel "
            "'q[DEPTH-1:0]' output port). When false, expose both 'q' and 'so'."
        ),
    )
    enable: bool = Field(
        default=True,
        description="Add an 'en' input that gates shifting/loading; when low the register holds.",
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

_MODULE_NAME = "shift_register"


def _reset_spec(opts: ShiftRegisterOptions) -> ResetSpec:
    """The single declarative reset (IR_SPEC §4 composes the skeleton)."""
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _reset_value_const() -> Const:
    """DEPTH-wide zero reset literal (renders as ``{DEPTH{1'b0}}``)."""
    return Const(0, width=Ref("DEPTH"))


def _so_tap(opts: ShiftRegisterOptions) -> Slice:
    """Serial output tap: LSB (right shift) or MSB (left shift)."""
    if opts.direction == "right":
        return Slice(Ref("q"), msb=Const(0), lsb=Const(0))
    return Slice(
        Ref("q"),
        msb=BinOp(BinOpKind.SUB, Ref("DEPTH"), Const(1)),
        lsb=BinOp(BinOpKind.SUB, Ref("DEPTH"), Const(1)),
    )


def _shift_expr(opts: ShiftRegisterOptions) -> Concat:
    """The next-value concat expression for one shift step.

    - right: {si, q[DEPTH-1:1]} — si enters at the MSB side, drains to LSB.
    - left:  {q[DEPTH-2:0], si} — si enters at the LSB side, drains to MSB.
    """
    if opts.direction == "right":
        upper = Slice(
            Ref("q"),
            msb=BinOp(BinOpKind.SUB, Ref("DEPTH"), Const(1)),
            lsb=Const(1),
        )
        return Concat([Ref("si"), upper])
    lower = Slice(
        Ref("q"),
        msb=BinOp(BinOpKind.SUB, Ref("DEPTH"), Const(2)),
        lsb=Const(0),
    )
    return Concat([lower, Ref("si")])


def generate(opts: ShiftRegisterOptions) -> Module:
    """Build the shift-register IR ``Module`` (pure). One ``AlwaysFF``, one ``Param``.

    Generator stays language- and polarity-agnostic (IR_SPEC design rules 2-4);
    it only decides *what* logic exists, not how it renders.
    """
    # --- ports (order per clean-rtl: clock, reset, control, data) -----------
    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
    ]
    if opts.enable:
        ports.append(
            Port("en", IN, bit(), doc="Shift/load enable (holds when low)")
        )
    if opts.parallel_load:
        ports.append(Port("load", IN, bit(), doc="Parallel load (beats shift)"))
        ports.append(
            Port("d", IN, vec("DEPTH"), doc="Parallel load data, DEPTH bits wide")
        )
    ports.append(Port("si", IN, bit(), doc="Serial input"))
    if not opts.serial_out_only:
        ports.append(
            Port("q", OUT, vec("DEPTH"), doc="Parallel shift-register contents")
        )
    ports.append(Port("so", OUT, bit(), doc=_so_doc(opts)))

    # --- clocked body ---------------------------------------------------
    # Shift statement always present; load (if enabled) takes priority over it.
    shift_stmt = Assign(Ref("q"), _shift_expr(opts))
    body: list = [
        Comment(
            f"{opts.direction} shift register, depth {opts.depth}",
            level=CommentLevel.VERBOSE,
        )
    ]
    if opts.parallel_load:
        step: list = [If(Ref("load"), then=[Assign(Ref("q"), Ref("d"))], else_=[shift_stmt])]
    else:
        step = [shift_stmt]

    if opts.enable:
        body.append(If(Ref("en"), then=step))
    else:
        body.extend(step)

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=_reset_spec(opts),
        reset_body=[Assign(Ref("q"), _reset_value_const())],
        body=body,
    )

    # ``so`` is a pure combinational tap of ``q`` (not a separate register), so
    # it is emitted as a continuous assignment alongside the clocked process.
    so_assign = ContAssign(Ref("so"), _so_tap(opts))

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",  # filled by generate() entry point with the config hash
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[Param("DEPTH", Const(opts.depth), doc="Shift register depth in bits")],
        ports=ports,
        items=[always, so_assign],
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def _direction_word(opts: ShiftRegisterOptions) -> str:
    return opts.direction


def _description(opts: ShiftRegisterOptions) -> str:
    return f"{opts.direction.capitalize()}-shifting shift register, {opts.depth}-bit"


def _reset_doc(opts: ShiftRegisterOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}"


def _so_doc(opts: ShiftRegisterOptions) -> str:
    tap = "LSB (q[0])" if opts.direction == "right" else "MSB (q[DEPTH-1])"
    return f"Serial output, taps the {tap}"


def _reset_behavior_text(opts: ShiftRegisterOptions) -> str:
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
        f"The {pol} reset resets the register {style} {edge}, clearing q to all zeros."
    )


def explain(opts: ShiftRegisterOptions) -> ExplanationDoc:
    """Fully populated explanation for the chosen options."""
    tap_desc = "LSB (q[0])" if opts.direction == "right" else "MSB (q[DEPTH-1])"

    configuration = [
        f"Depth: {opts.depth} bits",
        f"Direction: {opts.direction} "
        + (
            "(bits move toward the LSB, {si, q[DEPTH-1:1]})"
            if opts.direction == "right"
            else "(bits move toward the MSB, {q[DEPTH-2:0], si})"
        ),
        f"Parallel load: {'yes' if opts.parallel_load else 'no'}",
        f"Serial-out only: {'yes' if opts.serial_out_only else 'no'}"
        + (" (no parallel q output)" if opts.serial_out_only else " (both q and so exposed)"),
        f"Enable input: {'yes' if opts.enable else 'no'}",
        f"Reset: {opts.reset_style}, "
        f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
        f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
    ]

    signals = [
        SignalDoc(
            name="clk",
            direction="input",
            description="Clock; register updates on the rising edge.",
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
                description="Shift/load enable; when low the register holds its value.",
            )
        )
    if opts.parallel_load:
        signals.append(
            SignalDoc(
                name="load",
                direction="input",
                description="Parallel load control; when high, loads 'd' instead of shifting.",
            )
        )
        signals.append(
            SignalDoc(
                name="d",
                direction="input",
                description=f"Parallel load data, {opts.depth} bits wide.",
            )
        )
    signals.append(
        SignalDoc(
            name="si",
            direction="input",
            description="Serial input; the bit shifted into the register each active cycle.",
        )
    )
    if not opts.serial_out_only:
        signals.append(
            SignalDoc(
                name="q",
                direction="output",
                description=f"Parallel contents of the {opts.depth}-bit shift register.",
            )
        )
    signals.append(
        SignalDoc(
            name="so",
            direction="output",
            description=f"Serial output, taps the {tap_desc}.",
        )
    )

    enable_behavior = (
        "When en is high the register shifts (or loads, if load is asserted) on "
        "each clock; when en is low it holds its current value."
        if opts.enable
        else None
    )

    assumptions = [
        "A single free-running clock drives the register; all I/O is synchronous to it.",
        "The reset input is glitch-free and (for async reset) released synchronously.",
    ]
    if opts.parallel_load:
        assumptions.append(
            "d is stable and load is a synchronous control input around the clock edge."
        )

    limitations = [
        f"Serial output so taps the {tap_desc}; it is the bit that will be shifted "
        "out on the next active edge, not a delayed/registered copy.",
    ]
    if opts.parallel_load:
        limitations.append(
            "When load and a shift would otherwise both apply, load takes priority "
            "(the shift is skipped that cycle)."
        )
    limitations.append(
        "Single clock domain only; this snippet performs no clock-domain "
        "crossing (CDC) synchronization on its inputs or outputs."
    )

    return ExplanationDoc(
        purpose=(
            f"A {opts.depth}-bit {opts.direction}-shifting shift register"
            + (" with parallel load" if opts.parallel_load else "")
            + (" and count enable" if opts.enable else "")
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
class _ShiftRegisterSnippet:
    """Bundles the shift-register's metadata and pure ``generate``/``explain`` fns.

    Satisfies the :class:`~.contract.SnippetDef` protocol structurally.
    """

    id: str = "shift-register"
    name: str = "Shift Register"
    description: str = (
        "Parameterizable serial-in shift register (left/right, parallel load, "
        "serial-out-only mode)."
    )
    options_model: type[ShiftRegisterOptions] = ShiftRegisterOptions

    def generate(self, opts: ShiftRegisterOptions) -> Module:
        return generate(opts)

    def explain(self, opts: ShiftRegisterOptions) -> ExplanationDoc:
        return explain(opts)


SNIPPET = _ShiftRegisterSnippet()


__all__ = ["ShiftRegisterOptions", "generate", "explain", "SNIPPET"]
