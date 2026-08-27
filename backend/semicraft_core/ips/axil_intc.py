"""AXI4-Lite interrupt controller (Phase-4 P4-08).

A flat, single-priority controller: ``num_irq`` request lines in, one masked
request line out. Built on the register-block composition proved in P4-05a —
the AXI frontend is spliced in with ``field_ports=False`` and this module
appends the synchroniser and the trigger logic around it.

Registers
---------

    0x00  PENDING  [num_irq-1:0]  W1C  latched requests; write 1 to clear
    0x04  ENABLE   [num_irq-1:0]  RW   per-source mask
    0x08  STATUS   [num_irq-1:0]  RO   PENDING & ENABLE, the masked view

``irq_out`` is the OR of STATUS, so it is high exactly while some enabled
source is pending.

Latching, and why the mask is not in the latch
----------------------------------------------

A request is latched in PENDING whether or not it is enabled, and ENABLE gates
only the *output*. Masking before the latch would lose a request that arrived
while it was masked, which is precisely what software enabling a source later
wants to find. The cost is that PENDING accumulates requests nobody asked to
see; STATUS exists so a handler never has to compute the masked view itself.

Edge or level, decided at generate time
---------------------------------------

``trigger="edge"`` latches a rising edge of the synchronised request;
``trigger="level"`` latches the level itself, which means a write-1-to-clear
has no lasting effect while the source is still asserted — the flag re-arms on
the same clock. That is correct level behaviour, not a bug: a level source is
deasserted by servicing the device, and the controller has no way to do that.
The testbench checks the difference directly rather than trusting the comment.

The edge history flop sits *after* the synchroniser
---------------------------------------------------

An edge detector needs the previous value of a signal, and it is tempting to
take it from the second-to-last synchroniser stage, which already holds one.
That stage is one flop deep from an asynchronous input, so it can still be
metastable, and feeding it into the comparison puts the hazard straight back
into the latch it was meant to protect. ``irq_hist`` is therefore a separate
flop fed from the *last* synchroniser stage.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field

from ..assertions.spec import (
    AssertionItem,
    AssertionSpec,
    ResetContext,
    ResetKnownValue,
)
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
    ConstBase,
    ContAssign,
    Header,
    Module,
    ModuleItem,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
    UnaryOp,
    UnaryOpKind,
)
from ..modules.contract import PortGroup, TbSpec
from ..snippets.contract import CommonOptions, ExplanationDoc, SignalDoc
from ..version import VERSION
from .bundles import BundlePort, PortBundle
from .regblock import (
    AXI_CLOCK,
    AXI_RESET,
    AxilSequencer,
    RegisterModel,
    axil_ports,
    build_axil_regblock,
)
from .regmap import Register, RegisterField, RegisterMap

_MODULE_NAME = "axil_intc"
_DATA_WIDTH = 32


# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #


class AxilIntcOptions(CommonOptions):
    """Configuration for the AXI4-Lite interrupt controller.

    Extends :class:`CommonOptions`: AXI4-Lite fixes the reset active-low, so
    there is no polarity option, exactly as for the register block.
    """

    num_irq: int = Field(
        default=8,
        ge=1,
        le=_DATA_WIDTH,
        description=(
            "Number of interrupt sources. Bits above this are reserved in "
            "every register, so writing one returns SLVERR."
        ),
    )
    trigger: str = Field(
        default="edge",
        pattern="^(edge|level)$",
        description=(
            "How a request is latched: 'edge' on a rising edge of the "
            "synchronised input, 'level' while it is high (so clearing has no "
            "effect until the source deasserts)."
        ),
    )
    input_sync_stages: int = Field(
        default=2,
        ge=2,
        le=4,
        description=(
            "Flip-flop stages between the asynchronous request and the trigger "
            "logic. Two is the usual metastability guard."
        ),
    )
    reset_style: str = Field(
        default="sync",
        pattern="^(sync|async)$",
        description=(
            "Reset timing for the register block and the synchroniser. The "
            "polarity is fixed active-low by AXI4-Lite."
        ),
    )


# --------------------------------------------------------------------------- #
# Register map
# --------------------------------------------------------------------------- #

_REGISTERS = (
    ("PENDING", "w1c", "Latched interrupt requests; write 1 to clear."),
    ("ENABLE", "rw", "Per-source mask; 1 lets the source reach irq_out."),
    ("STATUS", "ro", "PENDING & ENABLE — the sources actually requesting."),
)


def register_map(opts: AxilIntcOptions) -> RegisterMap:
    """PENDING / ENABLE / STATUS, one field each, ``num_irq`` bits wide."""
    return RegisterMap(
        name="INTC",
        data_width=_DATA_WIDTH,
        addr_width=4,  # three 4-byte registers fit in 16 bytes
        registers=[
            Register(
                name=name,
                offset=index * 4,
                description=blurb,
                fields=[
                    RegisterField(
                        name="value",
                        lsb=0,
                        width=opts.num_irq,
                        access=access,
                        description=blurb,
                    )
                ],
            )
            for index, (name, access, blurb) in enumerate(_REGISTERS)
        ],
    )


def _f(register: str, field: str = "value") -> str:
    """Signal name the spliced register block gives one field."""
    return f"{register.lower()}_{field}"


def _set(register: str, field: str = "value") -> str:
    """Set-request input the register block declares for a ``w1c`` field."""
    return f"{_f(register, field)}_set"


# --------------------------------------------------------------------------- #
# RTL
# --------------------------------------------------------------------------- #

_HIST = "irq_hist"


def _sync_stage(index: int) -> str:
    return f"irq_sync{index}"


def _trigger_expr(opts: AxilIntcOptions, settled: str):
    """What raises a PENDING bit: a rising edge, or the level itself.

    ``settled`` is the last synchroniser stage — the first value in the chain
    that is safe to compare against anything.
    """
    if opts.trigger == "level":
        return Ref(settled)
    return BinOp(
        BinOpKind.AND,
        Ref(settled),
        UnaryOp(UnaryOpKind.NOT_BITWISE, Ref(_HIST)),
    )


def _glue_assignments(opts: AxilIntcOptions, settled: str) -> list[ModuleItem]:
    """Wire the trigger, the masked view and the output request.

    Every spliced field must be used — an unused signal fails the ``-Wall``
    gate — so this is also the list of what the register block expects the
    peripheral to drive: the ``w1c`` set input and the read-only STATUS field.
    """
    return [
        ContAssign(Ref(_set("PENDING")), _trigger_expr(opts, settled)),
        ContAssign(
            Ref(_f("STATUS")),
            BinOp(BinOpKind.AND, Ref(_f("PENDING")), Ref(_f("ENABLE"))),
        ),
        ContAssign(
            Ref("irq_out"),
            UnaryOp(UnaryOpKind.RED_OR, Ref(_f("STATUS"))),
        ),
    ]


def generate(opts: AxilIntcOptions) -> Module:
    """Build the controller IR by splicing the register block into this module."""
    regmap = register_map(opts)
    core = build_axil_regblock(
        _MODULE_NAME,
        regmap,
        sync_reset=opts.reset_style == "sync",
        description=_description(opts),
        field_ports=False,
    )

    lines = vec(opts.num_irq) if opts.num_irq > 1 else bit()
    ports = [
        *core.ports,
        Port("irq_in", IN, lines, doc="Asynchronous interrupt requests"),
        Port("irq_out", OUT, bit(), doc="Masked request; high while any enabled source pends"),
    ]

    stages = [_sync_stage(i) for i in range(opts.input_sync_stages)]
    signals: list[ModuleItem] = [
        Signal(stage, lines, doc=f"Request synchroniser stage {i}")
        for i, stage in enumerate(stages)
    ]
    edge = opts.trigger == "edge"
    if edge:
        signals.append(
            Signal(_HIST, lines, doc="Previous settled request, for edge detection")
        )

    zero = Const(0, width=Const(opts.num_irq), base=ConstBase.BIN)
    front_end = AlwaysFF(
        clock=ClockSpec(AXI_CLOCK),
        reset=ResetSpec(
            name=AXI_RESET,
            kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
            active_low=True,
        ),
        reset_body=[
            *[Assign(Ref(stage), zero) for stage in stages],
            *([Assign(Ref(_HIST), zero)] if edge else []),
        ],
        body=[
            Comment(
                "irq_in is asynchronous to aclk: synchronise before comparing",
                level=CommentLevel.VERBOSE,
            ),
            Assign(Ref(stages[0]), Ref("irq_in")),
            *[
                Assign(Ref(stages[i]), Ref(stages[i - 1]))
                for i in range(1, len(stages))
            ],
            *(
                [
                    Comment(
                        "Edge history is taken after the synchroniser, never "
                        "from inside it",
                        level=CommentLevel.VERBOSE,
                    ),
                    Assign(Ref(_HIST), Ref(stages[-1])),
                ]
                if edge
                else []
            ),
        ],
    )

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",
            config_hash="",
            tool_version=VERSION,
            description=_description(opts),
        ),
        params=[],
        ports=ports,
        items=[*core.items, *signals, front_end, *_glue_assignments(opts, stages[-1])],
    )


def _description(opts: AxilIntcOptions) -> str:
    return f"AXI4-Lite interrupt controller, {opts.num_irq} source(s), {opts.trigger}-triggered"


# --------------------------------------------------------------------------- #
# Directed testbench
# --------------------------------------------------------------------------- #
#
# Request timing, derived from the RTL above rather than observed from a run.
#
# A request driven at cycle t reaches the last synchroniser stage at cycle
# t+S (S = input_sync_stages), which is when the trigger expression is true.
# The register block samples the set input in its own always_ff, so the PENDING
# bit is readable from t+S+1. `_settle` waits S+2 cycles, one more than the
# minimum, so the sequence does not sit exactly on the boundary it is testing —
# the boundary itself is what the `one_stage_short` style mutations attack, and
# they are caught by the trigger-mode section instead.


def _settle(seq: AxilSequencer, opts: AxilIntcOptions) -> None:
    """Let a change on ``irq_in`` reach PENDING."""
    seq.idle(opts.input_sync_stages + 2)


def tb_spec(opts: AxilIntcOptions) -> TbSpec:
    """Latch requests, mask them, clear them, then pin the trigger mode.

    The last section is the one that earns its place: it raises a source and
    leaves it raised, clears PENDING over the top, and requires the bit to come
    back for ``level`` and stay clear for ``edge``. Without it the two modes
    produce testbenches that pass against either design, because every earlier
    step uses a pulse that both modes latch identically.
    """
    regmap = register_map(opts)
    model = RegisterModel(regmap)
    seq = AxilSequencer()
    full_strb = (1 << (_DATA_WIDTH // 8)) - 1
    level = opts.trigger == "level"

    pending = regmap.register("PENDING").offset
    enable = regmap.register("ENABLE").offset
    status = regmap.register("STATUS").offset

    src0 = 0b1
    src1 = 0b10 if opts.num_irq >= 2 else 0

    # Cycle 0 — out of reset nothing pends and nothing is requested.
    seq.expect(0, "bvalid", 0)
    seq.expect(0, "rvalid", 0)
    seq.expect(0, "irq_out", 0)
    seq.idle()

    # A request arrives while every source is masked. It must still latch:
    # masking gates the output, not the latch.
    #
    # Two reads, and the first one is the point. It is issued on the exact
    # cycle the last synchroniser stage goes high, so a correct design has not
    # latched yet and must read zero. A design that took its request one flop
    # earlier — the whole class of "the synchroniser is decorative" defects,
    # invisible in simulation because simulation has no metastability — would
    # already read the request here.
    start = seq.cycle
    seq.drive(irq_in=src0)
    seq.idle(2)
    seq.drive(irq_in=0)
    if opts.input_sync_stages > 2:
        seq.idle(opts.input_sync_stages - 2)
    assert seq.cycle == start + opts.input_sync_stages
    seq.read(pending, *model.read(pending))
    model.hardware_set("PENDING", "value", src0)
    seq.read(pending, *model.read(pending))
    model.drive_ro("STATUS", "value", 0)
    seq.read(status, *model.read(status))

    # Unmasking it is enough to raise the output — no new request needed.
    resp = model.write(enable, src0, full_strb)
    seq.write(enable, src0, full_strb, resp, [("irq_out", 1)])
    model.drive_ro("STATUS", "value", src0)
    seq.read(status, *model.read(status))

    if src1:
        # A second, still-masked source. PENDING grows; STATUS does not, which
        # is what proves the mask is per-bit rather than a single gate on the
        # OR of everything pending.
        seq.drive(irq_in=src1)
        seq.idle(2)
        seq.drive(irq_in=0)
        _settle(seq, opts)
        model.hardware_set("PENDING", "value", src1)
        seq.read(pending, *model.read(pending))
        seq.read(status, *model.read(status))

        # Clearing only the enabled source drops the output while the masked
        # one stays latched, waiting to be enabled later.
        resp = model.write(pending, src0, full_strb)
        seq.write(pending, src0, full_strb, resp, [("irq_out", 0)])
        model.drive_ro("STATUS", "value", 0)
        seq.read(status, *model.read(status))
        seq.read(pending, *model.read(pending))
        resp = model.write(pending, src1, full_strb)
        seq.write(pending, src1, full_strb, resp, [("irq_out", 0)])
    else:
        resp = model.write(pending, src0, full_strb)
        seq.write(pending, src0, full_strb, resp, [("irq_out", 0)])

    seq.read(pending, *model.read(pending))

    # --- the trigger mode itself ------------------------------------------ #
    # Mask everything first so irq_out stays low throughout: this section is
    # about the latch, and a moving output would only obscure it.
    resp = model.write(enable, 0, full_strb)
    seq.write(enable, 0, full_strb, resp, [("irq_out", 0)])

    seq.drive(irq_in=src0)
    _settle(seq, opts)
    model.hardware_set("PENDING", "value", src0)
    seq.read(pending, *model.read(pending))

    # Clear the bit with the source still asserted.
    resp = model.write(pending, src0, full_strb)
    seq.write(pending, src0, full_strb, resp, [("irq_out", 0)])
    _settle(seq, opts)
    if level:
        # The level re-arms the flag on the very clock the write clears it, so
        # software cannot clear a level source it has not serviced.
        model.hardware_set("PENDING", "value", src0)
    seq.read(pending, *model.read(pending))
    seq.drive(irq_in=0)

    # A write into the bits above num_irq is reserved: SLVERR, and ENABLE must
    # be untouched. Skipped when the sources fill the word.
    if opts.num_irq < _DATA_WIDTH:
        reserved = 1 << opts.num_irq
        resp = model.write(enable, reserved, full_strb)
        seq.write(enable, reserved, full_strb, resp, [("irq_out", 0)])

    items: list[AssertionItem] = [
        ResetKnownValue(name="bvalid_idle_after_reset", signal="bvalid", value=0, width=1),
        ResetKnownValue(name="rvalid_idle_after_reset", signal="rvalid", value=0, width=1),
        ResetKnownValue(name="irq_idle_after_reset", signal="irq_out", value=0, width=1),
    ]

    return TbSpec(
        clock=AXI_CLOCK,
        reset=AXI_RESET,
        reset_cycles=2,
        vectors=seq.vectors,
        checks=seq.checks,
        assertion_spec=AssertionSpec(
            clock=AXI_CLOCK,
            items=items,
            reset=ResetContext(
                signal=AXI_RESET, active_low=True, sync=opts.reset_style == "sync"
            ),
        ),
    )


# --------------------------------------------------------------------------- #
# IP metadata
# --------------------------------------------------------------------------- #


def bundles(opts: AxilIntcOptions) -> list[PortBundle]:  # noqa: ARG001
    """The AXI target port. The request lines are wires, not a protocol."""
    return [
        PortBundle(
            name="s_axil",
            protocol="axi4-lite",
            role="target",
            clock=AXI_CLOCK,
            reset=AXI_RESET,
            description="AXI4-Lite target serving PENDING/ENABLE/STATUS.",
            ports=[BundlePort(signal=sig, role_name=sig) for sig in axil_ports()],
        )
    ]


def port_groups(opts: AxilIntcOptions) -> list[PortGroup]:  # noqa: ARG001
    return [
        PortGroup(
            name="Clocking",
            ports=[AXI_CLOCK, f"{AXI_RESET}_n"],
            description="Single AXI clock domain; reset is active-low per the spec.",
        ),
        PortGroup(
            name="AXI4-Lite slave",
            ports=list(axil_ports()),
            description="AXI4-Lite target port (bundle `s_axil`).",
        ),
        PortGroup(
            name="Interrupts",
            ports=["irq_in", "irq_out"],
            description=(
                "Request lines in, one masked request out. Inputs are "
                "synchronised before they are latched."
            ),
        ),
    ]


def explain(opts: AxilIntcOptions) -> ExplanationDoc:
    regmap = register_map(opts)
    signals = [
        SignalDoc(name=AXI_CLOCK, direction="input", description="AXI clock."),
        SignalDoc(
            name=f"{AXI_RESET}_n",
            direction="input",
            description="AXI reset, active-low (the spec calls it ARESETn).",
        ),
    ]
    signals += [
        SignalDoc(
            name=sig,
            direction="output" if sig.endswith("ready") or sig in
            ("bresp", "bvalid", "rdata", "rresp", "rvalid") else "input",
            description="AXI4-Lite signal; see the register block's datasheet.",
        )
        for sig in axil_ports()
    ]
    trigger_blurb = (
        "high level" if opts.trigger == "level" else "rising edge"
    )
    signals += [
        SignalDoc(
            name="irq_in",
            direction="input",
            description=(
                f"Asynchronous interrupt requests; a {trigger_blurb} on a "
                f"synchronised line sets that source's PENDING bit."
            ),
        ),
        SignalDoc(
            name="irq_out",
            direction="output",
            description=(
                "High while any enabled source is pending; the OR of STATUS."
            ),
        ),
    ]

    return ExplanationDoc(
        purpose=(
            f"An AXI4-Lite interrupt controller aggregating {opts.num_irq} "
            f"{opts.trigger}-triggered source(s) into one masked request line. "
            "The AXI frontend is the register-block generator spliced in rather "
            "than instantiated, so the result is one flat module."
        ),
        configuration=[
            f"Sources: {opts.num_irq}",
            f"Trigger: {opts.trigger}",
            f"Input synchroniser: {opts.input_sync_stages} stages",
            f"Registers: {len(regmap.registers)} "
            f"({1 << regmap.addr_width} B decoded, {regmap.span_bytes()} B used)",
            f"Reset: {opts.reset_style}, active-low (fixed by AXI4-Lite)",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The active-low {opts.reset_style} reset clears PENDING and ENABLE, "
            "so the controller comes up with irq_out low and every source "
            "masked. The synchroniser clears too, so a line already high at "
            "reset release reads as a fresh request."
        ),
        assumptions=[
            "irq_in is asynchronous to aclk and is synchronised before use; a "
            f"request takes {opts.input_sync_stages + 1} clocks to appear in "
            "PENDING.",
            "Sources are active-high.",
        ],
        limitations=[
            "Flat priority: irq_out says that something is pending, not what. "
            "Software reads STATUS to find the source.",
            "No vectoring, no nesting, and no per-source priority.",
            "PENDING has one bit per source, so a second request arriving "
            "before the first is cleared is not counted.",
        ]
        + (
            [
                "Level-triggered: writing 1 to a PENDING bit has no lasting "
                "effect while its source is still asserted."
            ]
            if opts.trigger == "level"
            else [
                "Edge-triggered: a source already high when the controller "
                "leaves reset produces one request, then nothing until it "
                "deasserts and rises again."
            ]
        ),
    )


@dataclass(frozen=True)
class _AxilIntcIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "axil-intc"
    name: str = "AXI4-Lite interrupt controller"
    description: str = (
        "AXI4-Lite interrupt controller aggregating edge- or level-triggered "
        "sources into one masked request; the register frontend is spliced in "
        "from the AXI4-Lite register block generator."
    )
    kind: str = "ip"
    maturity: str = "beta"
    options_model: type[AxilIntcOptions] = AxilIntcOptions

    def generate(self, opts: AxilIntcOptions) -> Module:
        return generate(opts)

    def explain(self, opts: AxilIntcOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: AxilIntcOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: AxilIntcOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: AxilIntcOptions) -> RegisterMap:
        return register_map(opts)

    def bundles(self, opts: AxilIntcOptions) -> list[PortBundle]:
        return bundles(opts)


IP = _AxilIntcIp()

__all__ = [
    "AxilIntcOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "register_map",
    "bundles",
    "IP",
]
