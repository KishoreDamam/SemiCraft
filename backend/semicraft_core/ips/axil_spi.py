"""AXI4-Lite SPI master (Phase-4 P4-06).

A full-duplex, 8-bit, MSB-first SPI master on the register-block composition
from P4-05a. Writing ``TXDATA`` starts one 8-bit exchange: a byte goes out on
``mosi`` while a byte comes in on ``miso``, because that is what SPI is — there
is no separate "read" transfer.

Clock mode is a generate-time option
------------------------------------

``cpol``/``cpha`` are options, not register bits. SemiCraft generates the
module a design needs, and a runtime-selectable mode would carry both edge
behaviours in the hardware forever so that a register could pick one at boot.
The four modes differ only in the idle level and which edge samples:

    CPHA=0  sample on the leading edge, shift on the trailing edge
    CPHA=1  shift on the leading edge, sample on the trailing edge
    CPOL    the idle level of sclk, and therefore which edge is "leading"

Chip select is manual
---------------------

``CTRL.cs_assert`` drives ``cs_n`` directly rather than the transfer pulsing
it. Multi-byte transactions — the normal case for a flash or a sensor — need
chip select held across several exchanges, and a master that deasserted between
bytes could not talk to either. Software asserts, exchanges as many bytes as it
likes, then deasserts.

Bit timing
----------

``CLKDIV`` is the **half** period in ``aclk`` cycles, so a full ``sclk`` period
is ``2 * CLKDIV``. One exchange is 16 half-periods (eight bits, two edges
each). ``miso`` is sampled through a two-stage synchroniser: it is driven by
the slave off ``sclk``, which this master generates, but the round trip through
a pad and a cable is not synchronous to ``aclk`` in any useful sense.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
    Bit,
    ClockSpec,
    Comment,
    CommentLevel,
    Concat,
    Const,
    ConstBase,
    ContAssign,
    Header,
    If,
    Module,
    ModuleItem,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
    Slice,
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
    write_strobe_name,
)
from .regmap import Register, RegisterField, RegisterMap

_MODULE_NAME = "axil_spi"
_DATA_WIDTH = 32
_DIV_BITS = 16
_EDGES = 16  # eight bits, two sclk edges each


class AxilSpiOptions(CommonOptions):
    """Configuration for the AXI4-Lite SPI master."""

    cpol: Literal[0, 1] = Field(
        default=0,
        description="Clock polarity: the idle level of sclk.",
    )
    cpha: Literal[0, 1] = Field(
        default=0,
        description=(
            "Clock phase. 0 samples miso on the leading edge and shifts mosi "
            "on the trailing one; 1 is the reverse."
        ),
    )
    default_divisor: int = Field(
        default=2,
        ge=1,
        le=(1 << _DIV_BITS) - 1,
        description=(
            "Reset value of CLKDIV: aclk cycles per sclk *half* period, so the "
            "sclk period is twice this. The small default keeps generated "
            "simulations short."
        ),
    )
    input_sync_stages: int = Field(
        default=2,
        ge=2,
        le=4,
        description="Flip-flop stages between the miso pad and the sampler.",
    )
    reset_style: str = Field(
        default="sync",
        pattern="^(sync|async)$",
        description="Reset timing; the polarity is fixed active-low by AXI4-Lite.",
    )


def register_map(opts: AxilSpiOptions) -> RegisterMap:
    return RegisterMap(
        name="SPI",
        data_width=_DATA_WIDTH,
        addr_width=5,
        registers=[
            Register(
                name="STATUS", offset=0x0, description="Transfer status.",
                fields=[
                    RegisterField(
                        name="busy", lsb=0, width=1, access="ro",
                        description="An exchange is in progress.",
                    ),
                    RegisterField(
                        name="rx_valid", lsb=1, width=1, access="w1c",
                        description="RXDATA holds a received byte; write 1 to clear.",
                    ),
                ],
            ),
            Register(
                name="CTRL", offset=0x4, description="Chip select control.",
                fields=[
                    RegisterField(
                        name="cs_assert", lsb=0, width=1, access="rw",
                        description="Drive cs_n low. Held across as many exchanges as wanted.",
                    )
                ],
            ),
            Register(
                name="TXDATA", offset=0x8,
                description="Writing this register starts one 8-bit exchange.",
                fields=[
                    RegisterField(
                        name="data", lsb=0, width=8, access="wo",
                        description="Byte to shift out, MSB first; reads back as zero.",
                    )
                ],
            ),
            Register(
                name="RXDATA", offset=0xC,
                description="The byte shifted in during the last exchange.",
                fields=[
                    RegisterField(
                        name="data", lsb=0, width=8, access="ro",
                        description="Received byte; valid while STATUS.rx_valid is set.",
                    )
                ],
            ),
            Register(
                name="CLKDIV", offset=0x10, description="sclk half period in aclk cycles.",
                fields=[
                    RegisterField(
                        name="div", lsb=0, width=_DIV_BITS, access="rw",
                        reset=opts.default_divisor,
                        description="Half period; the sclk period is twice this.",
                    )
                ],
            ),
        ],
    )


def _f(register: str, field: str) -> str:
    return f"{register.lower()}_{field}"


def _set(register: str, field: str) -> str:
    return f"{_f(register, field)}_set"


# --------------------------------------------------------------------------- #
# RTL
# --------------------------------------------------------------------------- #


def _one(width: int = 1) -> Const:
    return Const(1, width=Const(width), base=ConstBase.BIN)


def _zero(width: int = 1) -> Const:
    return Const(0, width=Const(width), base=ConstBase.BIN)


def _eq(a, b) -> BinOp:
    return BinOp(BinOpKind.EQ, a, b)


def _not(expr) -> UnaryOp:
    return UnaryOp(UnaryOpKind.NOT_LOGICAL, expr)


def _shift_left(name: str):
    """``{name[6:0], 1'b0}`` — MSB-first transmission empties from the top."""
    return Concat([Slice(Ref(name), Const(6), Const(0)), _zero(1)])


def _rx_bits(opts: AxilSpiOptions) -> int:
    """How much receive history the shift register actually has to hold.

    With CPHA=0 the last sample lands on edge 14 and the byte is complete
    before the final edge, so all eight bits live in the register. With CPHA=1
    the last sample *is* the final edge and goes straight into RXDATA, so only
    seven earlier bits are ever re-read — an eighth would be written and never
    used, which the -Wall gate correctly refuses.
    """
    return 8 if opts.cpha == 0 else 7


def _shift_in(name: str, sampled, width: int):
    """``{name[width-2:0], bit}`` — MSB-first reception fills from the bottom."""
    return Concat([Slice(Ref(name), Const(width - 2), Const(0)), sampled])


def _half_tick() -> BinOp:
    return _eq(
        Ref("half_cnt"),
        BinOp(BinOpKind.SUB, Ref(_f("CLKDIV", "div")), _one(_DIV_BITS)),
    )


def _is_sample_edge(opts: AxilSpiOptions) -> BinOp:
    """Which sclk edges sample ``miso``.

    CPHA picks the parity: with CPHA=0 the *leading* edge (even, counting from
    zero) samples and the trailing one shifts; with CPHA=1 it is the reverse.
    The phase is a generate-time option, so this is a comparison against a
    constant the synthesiser folds away.
    """
    return _eq(
        Bit(Ref("edge_cnt"), Const(0)),
        Const(opts.cpha, width=Const(1), base=ConstBase.BIN),
    )


def _last_edge() -> BinOp:
    return _eq(Ref("edge_cnt"), Const(_EDGES - 1, width=Const(5)))


def _transfer_body(opts: AxilSpiOptions, sampled) -> list:
    """What one sclk edge does: toggle, then either sample or shift."""
    width = _rx_bits(opts)
    # On the final edge the byte is complete. Whether that edge is itself a
    # sampling one depends on CPHA, and CPHA is known now — so the right
    # expression is chosen here rather than muxed in hardware.
    final_rx = (
        Concat([Ref("rx_shift"), sampled]) if opts.cpha == 1 else Ref("rx_shift")
    )
    return [
        Assign(Ref("sclk_int"), _not(Ref("sclk_int"))),
        If(
            _last_edge(),
            then=[
                Assign(Ref("spi_active"), _zero()),
                Assign(Ref(_f("RXDATA", "data")), final_rx),
                Assign(Ref(_set("STATUS", "rx_valid")), _one()),
            ],
            else_=[
                If(
                    _is_sample_edge(opts),
                    then=[
                        Assign(Ref("rx_shift"), _shift_in("rx_shift", sampled, width))
                    ],
                    else_=[
                        Assign(Ref("mosi"), Bit(Ref("tx_shift"), Const(7))),
                        Assign(Ref("tx_shift"), _shift_left("tx_shift")),
                    ],
                ),
                Assign(
                    Ref("edge_cnt"),
                    BinOp(BinOpKind.ADD, Ref("edge_cnt"), _one(5)),
                ),
            ],
        ),
    ]


def _start_body(opts: AxilSpiOptions) -> list:
    """Begin an exchange.

    With CPHA=0 the first bit must already be on ``mosi`` before the leading
    edge, because that edge samples rather than shifts — so the byte is split
    here: top bit onto the wire, the rest into the shift register. With CPHA=1
    the leading edge does the shifting, so the whole byte simply loads.
    """
    common = [
        Assign(Ref("spi_active"), _one()),
        Assign(Ref("half_cnt"), _zero(_DIV_BITS)),
        Assign(Ref("edge_cnt"), _zero(5)),
        Assign(Ref("rx_shift"), _zero(_rx_bits(opts))),
    ]
    if opts.cpha == 0:
        return [
            *common,
            Assign(Ref("mosi"), Bit(Ref(_f("TXDATA", "data")), Const(7))),
            Assign(Ref("tx_shift"), _shift_left(_f("TXDATA", "data"))),
        ]
    return [*common, Assign(Ref("tx_shift"), Ref(_f("TXDATA", "data")))]


def _sync_stage(index: int) -> str:
    return f"miso_sync{index}"


def generate(opts: AxilSpiOptions) -> Module:
    """Build the SPI master IR by splicing the register block in."""
    regmap = register_map(opts)
    core = build_axil_regblock(
        _MODULE_NAME,
        regmap,
        sync_reset=opts.reset_style == "sync",
        description=_description(opts),
        field_ports=False,
    )

    ports = [
        *core.ports,
        Port("miso", IN, bit(), doc="Serial input from the slave"),
        Port("sclk", OUT, bit(), doc=f"Serial clock, idles {opts.cpol}"),
        Port("mosi", OUT, bit(), doc="Serial output to the slave, MSB first"),
        Port("cs_n", OUT, bit(), doc="Chip select, active low, driven by CTRL.cs_assert"),
    ]

    stages = [_sync_stage(i) for i in range(opts.input_sync_stages)]
    sampled = Ref(stages[-1])
    signals: list[ModuleItem] = [
        *[Signal(st, bit(), doc=f"miso synchroniser stage {i}") for i, st in enumerate(stages)],
        Signal("spi_active", bit(), doc="An exchange is in progress"),
        Signal("spi_go", bit(), doc="TXDATA write strobe, delayed one cycle"),
        Signal("sclk_int", bit(), doc="Clock before the CPOL inversion; idles low"),
        Signal("half_cnt", vec(_DIV_BITS), doc="aclk cycles within one sclk half period"),
        Signal("edge_cnt", vec(5), doc=f"sclk edges so far, 0..{_EDGES - 1}"),
        Signal("tx_shift", vec(8), doc="Transmit shift register, empties from the MSB"),
        Signal(
            "rx_shift",
            vec(_rx_bits(opts)),
            doc="Receive shift register, fills from the LSB",
        ),
    ]

    set_signal = _set("STATUS", "rx_valid")
    reset = ResetSpec(
        name=AXI_RESET,
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=True,
    )
    core_ff = AlwaysFF(
        clock=ClockSpec(AXI_CLOCK),
        reset=reset,
        reset_body=[
            Assign(Ref("spi_active"), _zero()),
            Assign(Ref("spi_go"), _zero()),
            Assign(Ref("sclk_int"), _zero()),
            Assign(Ref("mosi"), _zero()),
            Assign(Ref("half_cnt"), _zero(_DIV_BITS)),
            Assign(Ref("edge_cnt"), _zero(5)),
            Assign(Ref("tx_shift"), _zero(8)),
            Assign(Ref("rx_shift"), _zero(_rx_bits(opts))),
            Assign(Ref(_f("RXDATA", "data")), _zero(8)),
            Assign(Ref(set_signal), _zero()),
            *[Assign(Ref(st), _zero()) for st in stages],
        ],
        body=[
            Comment("One-cycle pulse: defaulted low, raised when a byte lands",
                    level=CommentLevel.VERBOSE),
            Assign(Ref(set_signal), _zero()),
            Assign(Ref(stages[0]), Ref("miso")),
            *[
                Assign(Ref(stages[i]), Ref(stages[i - 1]))
                for i in range(1, len(stages))
            ],
            # The strobe is delayed a cycle: txdata_data only takes the new byte
            # on the same edge the strobe is sampled (see docs/IPS.md).
            Assign(Ref("spi_go"), Ref(write_strobe_name("TXDATA"))),
            If(
                _not(Ref("spi_active")),
                then=[If(Ref("spi_go"), then=_start_body(opts))],
                else_=[
                    If(
                        _half_tick(),
                        then=[
                            Assign(Ref("half_cnt"), _zero(_DIV_BITS)),
                            *_transfer_body(opts, sampled),
                        ],
                        else_=[
                            Assign(
                                Ref("half_cnt"),
                                BinOp(BinOpKind.ADD, Ref("half_cnt"), _one(_DIV_BITS)),
                            )
                        ],
                    )
                ],
            ),
        ],
    )

    sclk_expr = _not(Ref("sclk_int")) if opts.cpol == 1 else Ref("sclk_int")
    glue: list[ModuleItem] = [
        ContAssign(Ref(_f("STATUS", "busy")), Ref("spi_active")),
        ContAssign(Ref("cs_n"), _not(Ref(_f("CTRL", "cs_assert")))),
        ContAssign(Ref("sclk"), sclk_expr),
    ]

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="", config_hash="", tool_version=VERSION,
            description=_description(opts),
        ),
        params=[],
        ports=ports,
        items=[*core.items, *signals, core_ff, *glue],
    )


def _description(opts: AxilSpiOptions) -> str:
    return f"AXI4-Lite SPI master, mode {opts.cpol}{opts.cpha}"


# --------------------------------------------------------------------------- #
# Directed testbench
# --------------------------------------------------------------------------- #
#
# Timing, derived from the FSM above rather than observed from a run.
#
# `AxilSequencer.write` drives at cycle c; the strobe lands at c+1, `spi_go` at
# c+2, and the FSM goes ACTIVE at edge c+3 — call that A. From there the half
# counter runs, so sclk edge k happens at cycle A + (k+1)*div, and the exchange
# ends after edge 15 at A + 16*div.
#
# mosi holds bit (7-j) across two edges. With CPHA=0 the first bit is placed at
# A (before the leading edge) and each *trailing* edge advances it, so bit
# (7-j) is on the wire from A + 2j*div. With CPHA=1 the *leading* edge does the
# shifting, so the same bit appears one half period later, from
# A + (2j+1)*div.
#
# The design samples `miso` through the synchroniser, reading it at the cycle
# *before* an edge fires: sample edge k reads the synchronised line as of
# A + (k+1)*div - 1. A driven level therefore has to be in place
# `input_sync_stages` cycles before that.


def _mosi_bit_cycle(opts: AxilSpiOptions, index: int, active: int, div: int) -> int:
    """Cycle at which data bit ``index`` (0 = first out, the MSB) is on mosi."""
    offset = 2 * index * div if opts.cpha == 0 else (2 * index + 1) * div
    return active + offset + 1


def _sample_read_cycle(index: int, active: int, div: int, cpha: int) -> int:
    """Cycle at which the FSM reads the synchronised miso for sample ``index``."""
    edge = 2 * index + cpha
    return active + (edge + 1) * div - 1


def tb_spec(opts: AxilSpiOptions) -> TbSpec:
    """Exchange a byte: check the driven bits, the clock, and the byte read in."""
    regmap = register_map(opts)
    model = RegisterModel(regmap)
    seq = AxilSequencer()
    full_strb = (1 << (_DATA_WIDTH // 8)) - 1
    div = opts.default_divisor
    stages = opts.input_sync_stages

    status = regmap.register("STATUS").offset
    ctrl = regmap.register("CTRL").offset
    txdata = regmap.register("TXDATA").offset
    rxdata = regmap.register("RXDATA").offset

    # Cycle 0 — idle: the clock sits at CPOL, chip select is released.
    seq.expect(0, "sclk", opts.cpol)
    seq.expect(0, "cs_n", 1)
    seq.expect(0, "bvalid", 0)

    # Chip select is manual, so software asserts it and holds it.
    resp = model.write(ctrl, 1, full_strb)
    seq.write(ctrl, 1, full_strb, resp, [("cs_n", 0)])

    # A byte that is not a bit-palindrome, so an LSB-first shift bug cannot
    # produce the same waveform (the UART's lesson, P4-05b).
    tx_byte = 0x4B
    rx_byte = 0x2D

    # miso can only carry a per-bit pattern if a level can settle through the
    # synchroniser inside one half period. When it cannot — a very fast clock
    # against a deep synchroniser — the line is held at a constant instead and
    # the expected byte follows from that, rather than the testbench pretending
    # to a resolution the configuration does not have.
    per_bit = 2 * div >= stages + 2
    if not per_bit:
        rx_byte = 0xFF

    # Drive the idle level from cycle 0 so the synchroniser has settled long
    # before the first sample. In the constant-line fallback this is the only
    # miso drive there is, and driving it at the transfer start instead was one
    # sample too late on a fast clock.
    seq.drive(miso=0 if per_bit else 1)
    seq.idle()

    request = seq.cycle
    resp = model.write(txdata, tx_byte, full_strb)
    seq.write(txdata, tx_byte, full_strb, resp, [])
    active = request + 3

    # Drive miso ahead of each sample so the synchroniser has settled.
    if per_bit:
        for index in range(8):
            level = (rx_byte >> (7 - index)) & 1  # MSB first
            at = _sample_read_cycle(index, active, div, opts.cpha) - stages
            seq.cycle = max(at, 0)
            seq.drive(miso=level)
    else:
        seq.cycle = active
        seq.drive(miso=1)

    # The byte goes out MSB first, one bit per full sclk period.
    for index in range(8):
        level = (tx_byte >> (7 - index)) & 1
        seq.expect(_mosi_bit_cycle(opts, index, active, div), "mosi", level)

    # The clock really toggles: check the first cycle of each of the first two
    # half periods. Not one cycle *into* them — with a divisor of 1 a half
    # period is a single cycle and "+1" would land in the next one, which is
    # how this check first read the wrong level.
    seq.expect(active + div, "sclk", 1 - opts.cpol)
    seq.expect(active + 2 * div, "sclk", opts.cpol)

    # After the sixteenth edge the exchange is over and the clock is back at
    # its idle level.
    clock_idle = active + _EDGES * div
    seq.expect(clock_idle, "sclk", opts.cpol)

    # STATUS.rx_valid is readable one cycle later than that. The completing
    # edge raises the *set request*, and the register block latches it in its
    # own always block, so the flag crosses a clock edge on the way. Reading at
    # clock_idle finds it still clear — which is exactly what happened when
    # this was collapsed into a single "transfer done" cycle.
    seq.cycle = max(seq.cycle, clock_idle + 1)

    model.hardware_set("STATUS", "rx_valid", 1)
    model.drive_ro("STATUS", "busy", 0)
    model.drive_ro("RXDATA", "data", rx_byte)
    seq.read(status, *model.read(status))
    seq.read(rxdata, *model.read(rxdata))

    # Clear the flag the way software does, and release chip select.
    clear = 1 << regmap.register("STATUS").field("rx_valid").lsb
    resp = model.write(status, clear, full_strb)
    seq.write(status, clear, full_strb, resp, [])
    seq.read(status, *model.read(status))
    resp = model.write(ctrl, 0, full_strb)
    seq.write(ctrl, 0, full_strb, resp, [("cs_n", 1)])

    items: list[AssertionItem] = [
        ResetKnownValue(name="cs_released_after_reset", signal="cs_n", value=1, width=1),
        ResetKnownValue(
            name="sclk_idles_at_cpol_after_reset", signal="sclk", value=opts.cpol, width=1
        ),
        ResetKnownValue(name="bvalid_idle_after_reset", signal="bvalid", value=0, width=1),
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


def bundles(opts: AxilSpiOptions) -> list[PortBundle]:  # noqa: ARG001
    return [
        PortBundle(
            name="s_axil", protocol="axi4-lite", role="target",
            clock=AXI_CLOCK, reset=AXI_RESET,
            description="AXI4-Lite target serving the SPI registers.",
            ports=[BundlePort(signal=sig, role_name=sig) for sig in axil_ports()],
        ),
        PortBundle(
            name="spi", protocol="spi", role="initiator",
            clock=AXI_CLOCK, reset=AXI_RESET,
            description="SPI link; this IP drives the clock and chip select.",
            ports=[
                BundlePort(signal="sclk", role_name="sclk"),
                BundlePort(signal="mosi", role_name="mosi"),
                BundlePort(signal="miso", role_name="miso"),
                BundlePort(signal="cs_n", role_name="cs_n"),
            ],
        ),
    ]


def port_groups(opts: AxilSpiOptions) -> list[PortGroup]:  # noqa: ARG001
    return [
        PortGroup(
            name="Clocking", ports=[AXI_CLOCK, f"{AXI_RESET}_n"],
            description="Single AXI clock domain; reset is active-low per the spec.",
        ),
        PortGroup(
            name="AXI4-Lite slave", ports=list(axil_ports()),
            description="AXI4-Lite target port (bundle `s_axil`).",
        ),
        PortGroup(
            name="SPI link", ports=["sclk", "mosi", "miso", "cs_n"],
            description="Master-side SPI signals (bundle `spi`).",
        ),
    ]


def explain(opts: AxilSpiOptions) -> ExplanationDoc:
    regmap = register_map(opts)
    reads = {"awready", "wready", "bresp", "bvalid", "arready", "rdata", "rresp", "rvalid"}
    signals = [
        SignalDoc(name=AXI_CLOCK, direction="input", description="AXI clock."),
        SignalDoc(
            name=f"{AXI_RESET}_n", direction="input",
            description="AXI reset, active-low (the spec calls it ARESETn).",
        ),
        *[
            SignalDoc(
                name=sig,
                direction="output" if sig in reads else "input",
                description="AXI4-Lite signal; see the register block's datasheet.",
            )
            for sig in axil_ports()
        ],
        SignalDoc(
            name="sclk", direction="output",
            description=f"Serial clock; idles at {opts.cpol} (CPOL).",
        ),
        SignalDoc(
            name="mosi", direction="output",
            description="Data to the slave, MSB first.",
        ),
        SignalDoc(
            name="miso", direction="input",
            description=(
                f"Data from the slave, sampled through "
                f"{opts.input_sync_stages} synchroniser flops."
            ),
        ),
        SignalDoc(
            name="cs_n", direction="output",
            description="Chip select, active low; driven directly by CTRL.cs_assert.",
        ),
    ]

    return ExplanationDoc(
        purpose=(
            f"An AXI4-Lite SPI master in mode {opts.cpol}{opts.cpha}. Writing "
            "TXDATA performs one full-duplex 8-bit exchange: a byte goes out on "
            "mosi while a byte comes in on miso. The AXI frontend is the "
            "register-block generator spliced into this module."
        ),
        configuration=[
            f"SPI mode: {opts.cpol}{opts.cpha} (CPOL={opts.cpol}, CPHA={opts.cpha})",
            f"Reset clock divisor: {opts.default_divisor} aclk cycles per sclk "
            f"half period (CLKDIV is writable at run time)",
            f"Input synchroniser: {opts.input_sync_stages} stages",
            f"Registers: {len(regmap.registers)} "
            f"({1 << regmap.addr_width} B decoded, {regmap.span_bytes()} B used)",
            f"Reset: {opts.reset_style}, active-low (fixed by AXI4-Lite)",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The active-low {opts.reset_style} reset returns the transfer FSM to idle, "
            f"puts sclk back to its idle level ({opts.cpol}) and releases cs_n, so the "
            "master cannot be left driving a slave's bus after a reset. CLKDIV returns "
            "to its reset divisor and CTRL.cs_assert clears."
        ),
        assumptions=[
            "The slave uses the same mode; CPOL/CPHA are fixed at generate time.",
            "Software holds CTRL.cs_assert across a multi-byte transaction and "
            "releases it afterwards — the exchange itself never touches cs_n.",
            "miso is sampled through a synchroniser, so it need not be "
            "phase-aligned to aclk.",
            "Software writes TXDATA only while STATUS.busy is clear.",
        ],
        limitations=[
            "8-bit transfers only, MSB first: no configurable word length and "
            "no LSB-first mode.",
            "CPOL/CPHA are generate-time options, not register bits — a runtime "
            "mode switch would carry both edge behaviours in hardware forever.",
            "Single chip select. Multiple slaves need external decoding of cs_n.",
            "No FIFOs: one byte in flight each way, and STATUS.rx_valid must be "
            "cleared between exchanges.",
            "No interrupt output; STATUS must be polled.",
        ],
    )


@dataclass(frozen=True)
class _AxilSpiIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "axil-spi"
    name: str = "AXI4-Lite SPI Master"
    description: str = (
        "Full-duplex 8-bit SPI master with a programmable clock divider and "
        "manual chip select; CPOL/CPHA fixed at generate time, AXI4-Lite "
        "register frontend spliced in from the register-block generator."
    )
    kind: str = "ip"
    maturity: str = "beta"
    options_model: type[AxilSpiOptions] = AxilSpiOptions

    def generate(self, opts: AxilSpiOptions) -> Module:
        return generate(opts)

    def explain(self, opts: AxilSpiOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: AxilSpiOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: AxilSpiOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: AxilSpiOptions) -> RegisterMap:
        return register_map(opts)

    def bundles(self, opts: AxilSpiOptions) -> list[PortBundle]:
        return bundles(opts)


IP = _AxilSpiIp()

__all__ = [
    "AxilSpiOptions", "generate", "explain", "port_groups", "tb_spec",
    "register_map", "bundles", "IP",
]
