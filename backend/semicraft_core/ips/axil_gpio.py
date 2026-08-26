"""AXI4-Lite GPIO — the first *composed* IP (Phase-4 P4-05a).

Where ``axil-regblock`` ships the register block as a standalone module, this
IP **splices** it into its own: ``build_axil_regblock(..., field_ports=False)``
emits the register logic with its hardware face as internal signals, and this
module appends the pins and the input synchroniser around it. The result is
one flat module with an AXI4-Lite frontend and no submodule instantiation.

That is the mechanism P4-05..P4-08 all need — a UART or SPI is its own logic
plus a register frontend — so it is proved here on the simplest peripheral
that can exercise it, rather than debugged for the first time underneath a
baud-rate generator.

Registers
---------

    0x00  DIR   RW  1 = drive the pin (gpio_oe)
    0x04  OUT   RW  value driven when the pin is an output
    0x08  IN    RO  synchronised pin input

Bits above ``num_pins`` are reserved in all three, so writing one returns
SLVERR — the register block's standard policy, inherited unchanged.

Inputs are synchronised, not sampled raw
----------------------------------------

``gpio_in`` is asynchronous to ``aclk`` by definition: it comes from a pin. It
passes through a two-stage (configurable) flip-flop synchroniser before
reaching the IN register, which is what keeps a metastable sample from
propagating into the AXI read data. The cost is that a pin change takes
``input_sync_stages`` clocks to become visible, which the datasheet states and
the testbench waits out.

No tri-state
------------

The IR has no ``inout``, so the pad direction is exposed as a separate
``gpio_oe`` output rather than driving a bidirectional net. Instantiating a
tri-state buffer is the integrator's job — and keeping it out of the generated
RTL is what lets the same module target both FPGA and ASIC flows.
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
    ClockSpec,
    Comment,
    CommentLevel,
    Const,
    ContAssign,
    Header,
    Module,
    ModuleItem,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
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

_MODULE_NAME = "axil_gpio"
_DATA_WIDTH = 32


# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #


class AxilGpioOptions(CommonOptions):
    """Configuration for the AXI4-Lite GPIO.

    Extends :class:`CommonOptions`: AXI4-Lite fixes the reset active-low, so
    there is no polarity option, exactly as for the register block.
    """

    num_pins: int = Field(
        default=8,
        ge=1,
        le=_DATA_WIDTH,
        description=(
            "Number of GPIO pins. Bits above this are reserved in every "
            "register, so writing one returns SLVERR."
        ),
    )
    input_sync_stages: int = Field(
        default=2,
        ge=2,
        le=4,
        description=(
            "Flip-flop stages between the asynchronous pin and the IN "
            "register. Two is the usual metastability guard; more trades "
            "latency for a longer mean time between failures."
        ),
    )
    reset_style: str = Field(
        default="sync",
        pattern="^(sync|async)$",
        description=(
            "Reset timing for the register block and the input synchroniser. "
            "The polarity is fixed active-low by AXI4-Lite."
        ),
    )


# --------------------------------------------------------------------------- #
# Register map
# --------------------------------------------------------------------------- #

_REGISTERS = (
    ("DIR", "rw", "Per-pin direction; 1 drives the pin."),
    ("OUT", "rw", "Per-pin output value, driven where DIR is 1."),
    ("IN", "ro", "Synchronised pin input."),
)


def register_map(opts: AxilGpioOptions) -> RegisterMap:
    """DIR / OUT / IN, one field each, ``num_pins`` bits wide."""
    return RegisterMap(
        name="GPIO",
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
                        width=opts.num_pins,
                        access=access,
                        description=blurb,
                    )
                ],
            )
            for index, (name, access, blurb) in enumerate(_REGISTERS)
        ],
    )


def _field(name: str) -> str:
    """Signal name the register block gives a register's ``value`` field."""
    return f"{name.lower()}_value"


# --------------------------------------------------------------------------- #
# RTL
# --------------------------------------------------------------------------- #


def _sync_stage(index: int) -> str:
    return f"in_sync{index}"


def _glue_assignments(stages: list[str]) -> list[ModuleItem]:
    """Wire the spliced register fields to the pins.

    The register block drives ``dir_value``/``out_value`` and reads
    ``in_value``; the peripheral does the mirror image. Every spliced field
    must be used — an unused signal fails the ``-Wall`` gate.
    """
    return [
        ContAssign(Ref("gpio_oe"), Ref(_field("DIR"))),
        ContAssign(Ref("gpio_out"), Ref(_field("OUT"))),
        ContAssign(Ref(_field("IN")), Ref(stages[-1])),
    ]


def generate(opts: AxilGpioOptions) -> Module:
    """Build the GPIO IR by splicing the register block into this module."""
    regmap = register_map(opts)
    core = build_axil_regblock(
        _MODULE_NAME,
        regmap,
        sync_reset=opts.reset_style == "sync",
        description=_description(opts),
        field_ports=False,  # the hardware face becomes internal signals
    )

    pins = vec(opts.num_pins) if opts.num_pins > 1 else bit()
    ports = [
        *core.ports,
        Port("gpio_in", IN, pins, doc="Asynchronous pin inputs"),
        Port("gpio_out", OUT, pins, doc="Pin output values"),
        Port("gpio_oe", OUT, pins, doc="Pin output enables (1 = drive)"),
    ]

    stages = [_sync_stage(i) for i in range(opts.input_sync_stages)]
    sync_signals: list[ModuleItem] = [
        Signal(stage, pins, doc=f"Input synchroniser stage {i}")
        for i, stage in enumerate(stages)
    ]

    reset = ResetSpec(
        name=AXI_RESET,
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=True,
    )
    synchroniser = AlwaysFF(
        clock=ClockSpec(AXI_CLOCK),
        reset=reset,
        reset_body=[
            Assign(Ref(stage), Const(0, width=Const(opts.num_pins))) for stage in stages
        ],
        body=[
            Comment(
                "Two-stage (or deeper) guard: gpio_in is asynchronous to aclk",
                level=CommentLevel.VERBOSE,
            ),
            Assign(Ref(stages[0]), Ref("gpio_in")),
            *[
                Assign(Ref(stages[i]), Ref(stages[i - 1]))
                for i in range(1, len(stages))
            ],
        ],
    )

    glue = _glue_assignments(stages)

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
        items=[*core.items, *sync_signals, synchroniser, *glue],
    )


def _description(opts: AxilGpioOptions) -> str:
    return f"AXI4-Lite GPIO, {opts.num_pins} pin(s)"


# --------------------------------------------------------------------------- #
# Directed testbench
# --------------------------------------------------------------------------- #


def tb_spec(opts: AxilGpioOptions) -> TbSpec:
    """Configure directions, drive outputs, then read synchronised inputs.

    Uses the same :class:`~.regblock.AxilSequencer` and
    :class:`~.regblock.RegisterModel` the standalone register block does, so
    the AXI handshake timing is described in exactly one place and a composed
    IP cannot drift from it.
    """
    regmap = register_map(opts)
    model = RegisterModel(regmap)
    seq = AxilSequencer()
    full_strb = (1 << (_DATA_WIDTH // 8)) - 1
    mask = (1 << opts.num_pins) - 1

    dir_addr = regmap.register("DIR").offset
    out_addr = regmap.register("OUT").offset
    in_addr = regmap.register("IN").offset

    # Cycle 0 — out of reset the pins must be inputs and driving zero, so the
    # block cannot fight whatever is already on the pad.
    seq.expect(0, "bvalid", 0)
    seq.expect(0, "rvalid", 0)
    seq.expect(0, "awready", 1)
    seq.expect(0, "gpio_oe", 0)
    seq.expect(0, "gpio_out", 0)
    seq.idle()

    # Enable every pin as an output, then drive a pattern onto them.
    resp = model.write(dir_addr, mask, full_strb)
    seq.write(dir_addr, mask, full_strb, resp, [("gpio_oe", mask)])

    pattern = 0xA5A5A5A5 & mask
    resp = model.write(out_addr, pattern, full_strb)
    seq.write(out_addr, pattern, full_strb, resp, [("gpio_out", pattern)])

    # Read DIR back over the bus: the register holds what was written, not
    # merely whatever the pins happen to show.
    seq.read(dir_addr, *model.read(dir_addr))

    # Drive the pins, wait out the synchroniser, then read IN. The wait is the
    # documented latency, not a guess: a pin change needs input_sync_stages
    # clocks to reach the register.
    sampled = 0x5A5A5A5A & mask
    seq.drive(gpio_in=sampled)

    # Read IN so that the capture edge lands exactly two clocks after the pins
    # changed: with two or more synchroniser stages the value has not arrived
    # yet, so IN must still read old.
    #
    # The offset matters. A read issued in the same cycle as the pin change
    # captures one edge later and reads old whether there are two stages, one,
    # or none at all — so it would pass against a design with no metastability
    # guard whatsoever. Delaying by one cycle is what makes the check
    # discriminate, and a mutation test pins that: dropping to a single stage
    # must fail this read.
    seq.idle()
    seq.read(in_addr, *model.read(in_addr))

    # ...then let it propagate fully and read the new value.
    seq.idle(opts.input_sync_stages)
    model.drive_ro("IN", "value", sampled)
    seq.read(in_addr, *model.read(in_addr))

    # A write into the bits above num_pins is reserved: SLVERR, and DIR must be
    # untouched. Skipped when the pins fill the word and nothing is reserved.
    if opts.num_pins < _DATA_WIDTH:
        reserved = 1 << opts.num_pins
        resp = model.write(dir_addr, reserved, full_strb)
        seq.write(dir_addr, reserved, full_strb, resp, [("gpio_oe", mask)])

    items: list[AssertionItem] = [
        ResetKnownValue(name="bvalid_idle_after_reset", signal="bvalid", value=0, width=1),
        ResetKnownValue(name="rvalid_idle_after_reset", signal="rvalid", value=0, width=1),
        ResetKnownValue(
            name="pins_not_driven_after_reset",
            signal="gpio_oe",
            value=0,
            width=opts.num_pins,
        ),
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


def bundles(opts: AxilGpioOptions) -> list[PortBundle]:  # noqa: ARG001
    """The AXI target port. The pins are this IP's own face, not a protocol."""
    return [
        PortBundle(
            name="s_axil",
            protocol="axi4-lite",
            role="target",
            clock=AXI_CLOCK,
            reset=AXI_RESET,
            description="AXI4-Lite target serving DIR/OUT/IN.",
            ports=[BundlePort(signal=sig, role_name=sig) for sig in axil_ports()],
        )
    ]


def port_groups(opts: AxilGpioOptions) -> list[PortGroup]:  # noqa: ARG001
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
            name="Pins",
            ports=["gpio_in", "gpio_out", "gpio_oe"],
            description=(
                "Pad-facing signals. There is no bidirectional net: the output "
                "enable is separate so the integrator instantiates the tri-state "
                "buffer."
            ),
        ),
    ]


def explain(opts: AxilGpioOptions) -> ExplanationDoc:
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
    signals += [
        SignalDoc(
            name="gpio_in",
            direction="input",
            description=(
                f"Asynchronous pin inputs; synchronised through "
                f"{opts.input_sync_stages} flip-flops before reaching IN."
            ),
        ),
        SignalDoc(
            name="gpio_out",
            direction="output",
            description="Pin output values, straight from the OUT register.",
        ),
        SignalDoc(
            name="gpio_oe",
            direction="output",
            description="Pin output enables, straight from the DIR register.",
        ),
    ]

    return ExplanationDoc(
        purpose=(
            f"An AXI4-Lite GPIO controller for {opts.num_pins} pin(s). The AXI "
            "frontend is the same register-block generator the standalone "
            "axil-regblock IP uses, spliced into this module rather than "
            "instantiated, so the result is one flat module."
        ),
        configuration=[
            f"Pins: {opts.num_pins}",
            f"Input synchroniser: {opts.input_sync_stages} stages",
            f"Registers: {len(regmap.registers)} "
            f"({1 << regmap.addr_width} B decoded, {regmap.span_bytes()} B used)",
            f"Reset: {opts.reset_style}, active-low (fixed by AXI4-Lite)",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The active-low {opts.reset_style} reset clears DIR and OUT, so every "
            "pin comes up as an input driving zero and the block cannot fight "
            "whatever is already on the pad. The input synchroniser clears too, so "
            "IN reads zero until the pins have been sampled."
        ),
        assumptions=[
            "gpio_in is asynchronous to aclk and is synchronised before use; a "
            "pin change takes input_sync_stages clocks to appear in IN.",
            "The integrator instantiates the tri-state buffer, driving the pad "
            "from gpio_out when gpio_oe is high.",
        ],
        limitations=[
            "No interrupt on pin change: IN must be polled.",
            "No per-pin open-drain or pull configuration.",
            "No bidirectional port — the IR has no `inout`, so direction is "
            "exposed as a separate gpio_oe output.",
            "Bits above num_pins are reserved in every register; writing one "
            "returns SLVERR (the register block's standard policy).",
        ],
    )


@dataclass(frozen=True)
class _AxilGpioIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "axil-gpio"
    name: str = "AXI4-Lite GPIO"
    description: str = (
        "AXI4-Lite GPIO controller with per-pin direction, output values and "
        "synchronised inputs; the register frontend is spliced in from the "
        "AXI4-Lite register block generator."
    )
    kind: str = "ip"
    maturity: str = "beta"
    options_model: type[AxilGpioOptions] = AxilGpioOptions

    def generate(self, opts: AxilGpioOptions) -> Module:
        return generate(opts)

    def explain(self, opts: AxilGpioOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: AxilGpioOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: AxilGpioOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: AxilGpioOptions) -> RegisterMap:
        return register_map(opts)

    def bundles(self, opts: AxilGpioOptions) -> list[PortBundle]:
        return bundles(opts)


IP = _AxilGpioIp()

__all__ = [
    "AxilGpioOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "register_map",
    "bundles",
    "IP",
]
