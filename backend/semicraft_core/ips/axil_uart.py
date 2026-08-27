"""AXI4-Lite UART (Phase-4 P4-05b).

An 8N1 UART — 8 data bits, no parity, one stop bit — with a programmable baud
divisor, built on the register-block composition proved in P4-05a: the AXI
frontend is spliced in with ``field_ports=False`` and this module appends the
transmit and receive state machines around it.

Registers
---------

    0x00  STATUS   tx_busy   [0]     RO   transmitter is shifting
                   rx_valid  [1]     W1C  a byte is waiting in RXDATA
                   rx_overrun[2]     W1C  a byte arrived while one was waiting
                   frame_error[3]    W1C  stop bit was not high
    0x04  TXDATA   data      [7:0]   WO   writing starts a transmission
    0x08  RXDATA   data      [7:0]   RO   the received byte
    0x0C  BAUDDIV  div       [15:0]  RW   clocks per bit

Why the status flags are W1C rather than read-to-clear
------------------------------------------------------

The natural UART idiom is "reading RXDATA clears rx_valid", but the register
block has no read-side effect: its read path is a mux, with no per-register
read strobe. Rather than add one — a new access type and a new signal on every
register — the flags are **write-1-to-clear**, which the block already
implements exactly. Software reads RXDATA and then writes a 1 to the flag.
That is a real, common UART interface, not a workaround, and it kept a
frozen-ish contract from growing a feature with one user.

The transmit trigger is the register's write strobe
---------------------------------------------------

``TXDATA`` is a write-only field, so its storage holds the byte — but storage
alone cannot say *when* a write happened. The register block already computes
that: ``wr_sel_txdata`` is high for exactly one cycle per accepted write
(``regblock.write_strobe_name``). The transmitter delays it by one cycle
before starting, because ``txdata_data`` only takes the new value on the same
edge the strobe is sampled — using it immediately would transmit the
*previous* byte.

Bit timing
----------

``tick`` fires when the baud counter reaches ``div - 1``. The transmitter
holds each bit for one full period. The receiver waits **half** a period after
detecting the start bit, so every subsequent full period lands in the middle
of a bit rather than on its edge — the usual mid-bit sampling, and the reason
a divisor below 2 is not usable (half of it would be zero).

``uart_rx`` is asynchronous by definition and passes through a two-stage
synchroniser before the receiver looks at it, the same guard the GPIO uses.
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
    Bit,
    Case,
    CaseItem,
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

_MODULE_NAME = "axil_uart"
_DATA_WIDTH = 32
_DIV_BITS = 16

# Transmit / receive FSM encodings. Plain 2-bit constants rather than an enum
# type: the same encoding then renders identically in SystemVerilog and
# Verilog-2001, and the state names live in comments beside each arm.
_IDLE, _START, _DATA, _STOP = 0, 1, 2, 3
_STATE_NAMES = {_IDLE: "IDLE", _START: "START", _DATA: "DATA", _STOP: "STOP"}


class AxilUartOptions(CommonOptions):
    """Configuration for the AXI4-Lite UART."""

    default_divisor: int = Field(
        default=4,
        ge=2,
        le=(1 << _DIV_BITS) - 1,
        description=(
            "Reset value of BAUDDIV: clocks per bit. Must be at least 2, "
            "because the receiver waits half a period to reach mid-bit. "
            "clk_hz / baud_rate gives the value for a real link; the small "
            "default keeps generated simulations short."
        ),
    )
    input_sync_stages: int = Field(
        default=2,
        ge=2,
        le=4,
        description="Flip-flop stages between the asynchronous rx pin and the receiver.",
    )
    reset_style: str = Field(
        default="sync",
        pattern="^(sync|async)$",
        description=(
            "Reset timing. The polarity is fixed active-low by AXI4-Lite."
        ),
    )


# --------------------------------------------------------------------------- #
# Register map
# --------------------------------------------------------------------------- #


def register_map(opts: AxilUartOptions) -> RegisterMap:
    return RegisterMap(
        name="UART",
        data_width=_DATA_WIDTH,
        addr_width=4,
        registers=[
            Register(
                name="STATUS",
                offset=0x0,
                description="Transmitter and receiver status.",
                fields=[
                    RegisterField(
                        name="tx_busy", lsb=0, width=1, access="ro",
                        description="The transmitter is shifting a byte out.",
                    ),
                    RegisterField(
                        name="rx_valid", lsb=1, width=1, access="w1c",
                        description="A byte is waiting in RXDATA; write 1 to clear.",
                    ),
                    RegisterField(
                        name="rx_overrun", lsb=2, width=1, access="w1c",
                        description="A byte arrived while one was still waiting.",
                    ),
                    RegisterField(
                        name="frame_error", lsb=3, width=1, access="w1c",
                        description="The stop bit was not high.",
                    ),
                ],
            ),
            Register(
                name="TXDATA",
                offset=0x4,
                description="Writing this register starts a transmission.",
                fields=[
                    RegisterField(
                        name="data", lsb=0, width=8, access="wo",
                        description="Byte to transmit; reads back as zero.",
                    )
                ],
            ),
            Register(
                name="RXDATA",
                offset=0x8,
                description="The most recently received byte.",
                fields=[
                    RegisterField(
                        name="data", lsb=0, width=8, access="ro",
                        description="Received byte; valid while STATUS.rx_valid is set.",
                    )
                ],
            ),
            Register(
                name="BAUDDIV",
                offset=0xC,
                description="Clocks per bit.",
                fields=[
                    RegisterField(
                        name="div", lsb=0, width=_DIV_BITS, access="rw",
                        reset=opts.default_divisor,
                        description="Baud divisor; at least 2.",
                    )
                ],
            ),
        ],
    )


def _f(register: str, field: str) -> str:
    """Signal name the spliced register block gives one field."""
    return f"{register.lower()}_{field}"


def _set(register: str, field: str) -> str:
    """Set-request input the register block declares for a ``w1c`` field."""
    return f"{_f(register, field)}_set"


# --------------------------------------------------------------------------- #
# RTL
# --------------------------------------------------------------------------- #


def _state(value: int) -> Const:
    return Const(value, width=Const(2), base=ConstBase.BIN)


def _one(width: int = 1) -> Const:
    return Const(1, width=Const(width), base=ConstBase.BIN)


def _zero(width: int = 1) -> Const:
    return Const(0, width=Const(width), base=ConstBase.BIN)


def _eq(a, b) -> BinOp:
    return BinOp(BinOpKind.EQ, a, b)


def _land(a, b) -> BinOp:
    return BinOp(BinOpKind.LAND, a, b)


def _not(expr) -> UnaryOp:
    return UnaryOp(UnaryOpKind.NOT_LOGICAL, expr)


def _div() -> Ref:
    return Ref(_f("BAUDDIV", "div"))


def _tick(counter: str) -> BinOp:
    """``counter == div - 1`` — one baud period elapsed."""
    return _eq(Ref(counter), BinOp(BinOpKind.SUB, _div(), _one(_DIV_BITS)))


def _half_tick(counter: str) -> BinOp:
    """``counter == (div >> 1) - 1`` — half a period, to reach mid-bit."""
    return _eq(
        Ref(counter),
        BinOp(BinOpKind.SUB, BinOp(BinOpKind.SHR, _div(), Const(1)), _one(_DIV_BITS)),
    )


def _count_or_clear(counter: str, done) -> If:
    """Advance a baud counter, restarting it when its period completes."""
    return If(
        done,
        then=[Assign(Ref(counter), _zero(_DIV_BITS))],
        else_=[Assign(Ref(counter), BinOp(BinOpKind.ADD, Ref(counter), _one(_DIV_BITS)))],
    )


def _tx_shift_out() -> list:
    """Present the low bit of the shift register, then shift it down.

    LSB first is the UART convention; getting it backwards produces a frame
    that is still well-formed, so only a check on the actual bit pattern
    catches it.
    """
    return [
        Assign(Ref("uart_tx"), Bit(Ref("tx_shift"), Const(0))),
        Assign(
            Ref("tx_shift"),
            Concat([_zero(1), Slice(Ref("tx_shift"), Const(7), Const(1))]),
        ),
    ]


def _rx_complete(sampled) -> list:
    """What happens when the stop bit's period elapses: deliver and flag."""
    return [
        Assign(Ref("rx_state"), _state(_IDLE)),
        Assign(Ref(_f("RXDATA", "data")), Ref("rx_shift")),
        # A byte arriving while one is still unread is an overrun; the new byte
        # still lands, the flag says the old one was lost.
        Assign(Ref(_set("STATUS", "rx_valid")), _one()),
        Assign(
            Ref(_set("STATUS", "rx_overrun")),
            Ref(_f("STATUS", "rx_valid")),
        ),
        # A stop bit that is not high means the frame did not line up.
        Assign(Ref(_set("STATUS", "frame_error")), _not(sampled)),
    ]


def _tx_logic() -> list:
    """Transmit FSM: start bit, eight data bits LSB first, stop bit."""
    tick = _tick("tx_cnt")
    shift_out = _tx_shift_out()
    return [
        Comment("Transmitter", level=CommentLevel.VERBOSE),
        # One-cycle delay on the write strobe: txdata_data only takes the new
        # byte on the same edge the strobe is sampled.
        Assign(Ref("tx_go"), Ref(write_strobe_name("TXDATA"))),
        Case(
            Ref("tx_state"),
            items=[
                CaseItem(
                    [_state(_IDLE)],
                    [
                        Assign(Ref("uart_tx"), _one()),
                        If(
                            Ref("tx_go"),
                            then=[
                                Assign(Ref("tx_state"), _state(_START)),
                                Assign(Ref("tx_cnt"), _zero(_DIV_BITS)),
                                Assign(Ref("tx_shift"), Ref(_f("TXDATA", "data"))),
                                Assign(Ref("tx_bit"), _zero(3)),
                                Assign(Ref("uart_tx"), _zero()),  # start bit
                            ],
                        ),
                    ],
                ),
                CaseItem(
                    [_state(_START)],
                    [
                        _count_or_clear("tx_cnt", tick),
                        If(tick, then=[Assign(Ref("tx_state"), _state(_DATA)), *shift_out]),
                    ],
                ),
                CaseItem(
                    [_state(_DATA)],
                    [
                        _count_or_clear("tx_cnt", tick),
                        If(
                            tick,
                            then=[
                                If(
                                    _eq(Ref("tx_bit"), Const(7, width=Const(3))),
                                    then=[
                                        Assign(Ref("tx_state"), _state(_STOP)),
                                        Assign(Ref("uart_tx"), _one()),  # stop bit
                                    ],
                                    else_=[
                                        Assign(
                                            Ref("tx_bit"),
                                            BinOp(BinOpKind.ADD, Ref("tx_bit"), _one(3)),
                                        ),
                                        *shift_out,
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
                CaseItem(
                    [_state(_STOP)],
                    [
                        _count_or_clear("tx_cnt", tick),
                        If(tick, then=[Assign(Ref("tx_state"), _state(_IDLE))]),
                    ],
                ),
            ],
            # Unreachable — a 2-bit state has exactly these four encodings — but
            # a recovery arm is what keeps an FSM that somehow lands out of
            # range from staying there, and the IR requires a default on a
            # non-enum case anyway.
            default=[Assign(Ref("tx_state"), _state(_IDLE))],
        ),
    ]


def _rx_logic(last_sync: str) -> list:
    """Receive FSM: detect the start bit, then sample every bit at mid-bit."""
    tick = _tick("rx_cnt")
    half = _half_tick("rx_cnt")
    sampled = Ref(last_sync)
    return [
        Comment("Receiver", level=CommentLevel.VERBOSE),
        Case(
            Ref("rx_state"),
            items=[
                CaseItem(
                    [_state(_IDLE)],
                    [
                        If(
                            _not(sampled),  # line pulled low: a start bit
                            then=[
                                Assign(Ref("rx_state"), _state(_START)),
                                Assign(Ref("rx_cnt"), _zero(_DIV_BITS)),
                            ],
                        )
                    ],
                ),
                CaseItem(
                    [_state(_START)],
                    [
                        _count_or_clear("rx_cnt", half),
                        If(
                            half,
                            then=[
                                # Half a period in, we are mid start bit. If the
                                # line has recovered it was a glitch, not a frame.
                                If(
                                    sampled,
                                    then=[Assign(Ref("rx_state"), _state(_IDLE))],
                                    else_=[
                                        Assign(Ref("rx_state"), _state(_DATA)),
                                        Assign(Ref("rx_bit"), _zero(3)),
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
                CaseItem(
                    [_state(_DATA)],
                    [
                        _count_or_clear("rx_cnt", tick),
                        If(
                            tick,
                            then=[
                                Assign(
                                    Ref("rx_shift"),
                                    Concat([sampled, Slice(Ref("rx_shift"), Const(7), Const(1))]),
                                ),
                                If(
                                    _eq(Ref("rx_bit"), Const(7, width=Const(3))),
                                    then=[Assign(Ref("rx_state"), _state(_STOP))],
                                    else_=[
                                        Assign(
                                            Ref("rx_bit"),
                                            BinOp(BinOpKind.ADD, Ref("rx_bit"), _one(3)),
                                        )
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                CaseItem(
                    [_state(_STOP)],
                    [
                        _count_or_clear("rx_cnt", tick),
                        If(tick, then=_rx_complete(sampled)),
                    ],
                ),
            ],
            default=[Assign(Ref("rx_state"), _state(_IDLE))],
        ),
    ]


def _sync_stage(index: int) -> str:
    return f"rx_sync{index}"


def generate(opts: AxilUartOptions) -> Module:
    """Build the UART IR by splicing the register block into this module."""
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
        Port("uart_rx", IN, bit(), doc="Serial input, asynchronous; idles high"),
        Port("uart_tx", OUT, bit(), doc="Serial output; idles high"),
    ]

    stages = [_sync_stage(i) for i in range(opts.input_sync_stages)]
    signals: list[ModuleItem] = [
        *[Signal(st, bit(), doc=f"rx synchroniser stage {i}") for i, st in enumerate(stages)],
        Signal("tx_state", vec(2), doc="Transmit FSM: 0 IDLE, 1 START, 2 DATA, 3 STOP"),
        Signal("tx_cnt", vec(_DIV_BITS), doc="Transmit baud counter"),
        Signal("tx_shift", vec(8), doc="Transmit shift register, empties LSB first"),
        Signal("tx_bit", vec(3), doc="Transmit bit index"),
        Signal("tx_go", bit(), doc="TXDATA write strobe, delayed one cycle"),
        Signal("rx_state", vec(2), doc="Receive FSM: 0 IDLE, 1 START, 2 DATA, 3 STOP"),
        Signal("rx_cnt", vec(_DIV_BITS), doc="Receive baud counter"),
        Signal("rx_shift", vec(8), doc="Receive shift register, fills from the MSB"),
        Signal("rx_bit", vec(3), doc="Receive bit index"),
    ]

    set_signals = [
        _set("STATUS", "rx_valid"),
        _set("STATUS", "rx_overrun"),
        _set("STATUS", "frame_error"),
    ]

    reset = ResetSpec(
        name=AXI_RESET,
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=True,
    )
    core_ff = AlwaysFF(
        clock=ClockSpec(AXI_CLOCK),
        reset=reset,
        reset_body=[
            # The serial line and the synchroniser idle HIGH: coming out of
            # reset with them low would look exactly like a start bit.
            Assign(Ref("uart_tx"), _one()),
            *[Assign(Ref(st), _one()) for st in stages],
            Assign(Ref("tx_state"), _state(_IDLE)),
            Assign(Ref("tx_cnt"), _zero(_DIV_BITS)),
            Assign(Ref("tx_shift"), _zero(8)),
            Assign(Ref("tx_bit"), _zero(3)),
            Assign(Ref("tx_go"), _zero()),
            Assign(Ref("rx_state"), _state(_IDLE)),
            Assign(Ref("rx_cnt"), _zero(_DIV_BITS)),
            Assign(Ref("rx_shift"), _zero(8)),
            Assign(Ref("rx_bit"), _zero(3)),
            Assign(Ref(_f("RXDATA", "data")), _zero(8)),
            *[Assign(Ref(name), _zero()) for name in set_signals],
        ],
        body=[
            Comment(
                "Set requests are one-cycle pulses: defaulted low here and "
                "raised below, so a later assignment in the same block wins",
                level=CommentLevel.VERBOSE,
            ),
            *[Assign(Ref(name), _zero()) for name in set_signals],
            Comment("Synchronise the asynchronous rx line before sampling it",
                    level=CommentLevel.VERBOSE),
            Assign(Ref(stages[0]), Ref("uart_rx")),
            *[
                Assign(Ref(stages[i]), Ref(stages[i - 1]))
                for i in range(1, len(stages))
            ],
            *_tx_logic(),
            *_rx_logic(stages[-1]),
        ],
    )

    glue: list[ModuleItem] = [
        # tx_busy is a read-only field, so the peripheral drives it.
        ContAssign(
            Ref(_f("STATUS", "tx_busy")),
            BinOp(BinOpKind.NE, Ref("tx_state"), _state(_IDLE)),
        )
    ]

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
        items=[*core.items, *signals, core_ff, *glue],
    )


def _description(opts: AxilUartOptions) -> str:
    return f"AXI4-Lite UART, 8N1, reset divisor {opts.default_divisor}"


# --------------------------------------------------------------------------- #
# Directed testbench
# --------------------------------------------------------------------------- #
#
# Bit timing, derived from the FSMs above rather than observed from a run:
#
# Transmit. `AxilSequencer.write` drives the request at cycle c; both channels
# are captured at edge c+1, so `wr_sel_txdata` is high during cycle c+1 and
# `tx_go` during c+2. The FSM leaves IDLE at edge c+3, which is where the
# start bit begins — call it S. Each bit then holds for one full divisor, so
# bit k (0 = start, 1..8 = data LSB first, 9 = stop) occupies cycles
# [S + k*div, S + (k+1)*div - 1], and the line returns to idle at S + 10*div.
#
# Receive. A frame driven onto the pin at cycle R reaches the FSM
# `input_sync_stages` cycles later; the receiver then waits half a divisor to
# reach mid-bit and samples every full divisor after that, finishing around
# R + stages + 1 + div/2 + 9*div. The testbench waits R + 10*div + stages + 4,
# which clears that for every legal divisor with margin to spare — the exact
# completion cycle is not worth pinning when the observable is a status flag.


def _tx_frame_bits(byte: int) -> list[int]:
    """The ten line levels of an 8N1 frame: start, data LSB first, stop."""
    return [0, *[(byte >> i) & 1 for i in range(8)], 1]


def tb_spec(opts: AxilUartOptions) -> TbSpec:
    """Transmit a byte and watch the line, then drive a frame in and read it."""
    regmap = register_map(opts)
    model = RegisterModel(regmap)
    seq = AxilSequencer()
    full_strb = (1 << (_DATA_WIDTH // 8)) - 1
    div = opts.default_divisor
    stages = opts.input_sync_stages

    status = regmap.register("STATUS").offset
    txdata = regmap.register("TXDATA").offset
    rxdata = regmap.register("RXDATA").offset
    bauddiv = regmap.register("BAUDDIV").offset

    # Cycle 0 — the line idles high and nothing is asserted.
    seq.expect(0, "uart_tx", 1)
    seq.expect(0, "bvalid", 0)
    seq.expect(0, "rvalid", 0)
    seq.drive(uart_rx=1)
    seq.idle()

    # The divisor reset value is readable, so software can discover the link
    # rate the block came up with.
    seq.read(bauddiv, *model.read(bauddiv))

    # ---- transmit ---------------------------------------------------------
    # Deliberately not a bit-palindrome: 0xA5 and 0x3C both read the same
    # backwards, so an MSB-first shift bug would transmit an identical frame
    # and the checks would pass against reversed hardware.
    tx_byte = 0x4B
    request = seq.cycle
    resp = model.write(txdata, tx_byte, full_strb)
    seq.write(txdata, tx_byte, full_strb, resp, [])
    start = request + 3

    # One cycle into each bit period: far from both edges, so a half-period
    # timing error shows up rather than sitting exactly on a boundary.
    for index, level in enumerate(_tx_frame_bits(tx_byte)):
        seq.expect(start + index * div + 1, "uart_tx", level)

    # STATUS must report the transmitter busy while it shifts.
    model.drive_ro("STATUS", "tx_busy", 1)
    seq.read(status, *model.read(status))

    # ...and idle again once the stop bit has been held for a full period.
    seq.cycle = max(seq.cycle, start + 10 * div)
    seq.expect(seq.cycle, "uart_tx", 1)
    model.drive_ro("STATUS", "tx_busy", 0)
    seq.read(status, *model.read(status))

    # ---- receive ----------------------------------------------------------
    rx_byte = 0x2D  # likewise not a palindrome
    frame_start = seq.cycle
    for index, level in enumerate(_tx_frame_bits(rx_byte)):
        seq.cycle = frame_start + index * div
        seq.drive(uart_rx=level)
    seq.cycle = frame_start + 10 * div + stages + 4

    model.hardware_set("STATUS", "rx_valid", 1)
    model.drive_ro("RXDATA", "data", rx_byte)
    seq.read(status, *model.read(status))
    seq.read(rxdata, *model.read(rxdata))

    # Clear the flag the way software does — write 1 to it — and confirm it
    # went. This is the read-to-clear substitute the register block's access
    # types support directly.
    clear = 1 << regmap.register("STATUS").field("rx_valid").lsb
    resp = model.write(status, clear, full_strb)
    seq.write(status, clear, full_strb, resp, [])
    seq.read(status, *model.read(status))

    items: list[AssertionItem] = [
        ResetKnownValue(name="tx_idles_high_after_reset", signal="uart_tx", value=1, width=1),
        ResetKnownValue(name="bvalid_idle_after_reset", signal="bvalid", value=0, width=1),
        ResetKnownValue(name="rvalid_idle_after_reset", signal="rvalid", value=0, width=1),
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


def bundles(opts: AxilUartOptions) -> list[PortBundle]:  # noqa: ARG001
    """The AXI target port, and the serial link as its own bundle.

    The serial pair is a genuine two-signal interface a composer can wire —
    one UART's ``tx`` to another's ``rx`` — so it earns a bundle, unlike the
    GPIO's pins, which fan out to a pad ring rather than to another IP.
    """
    return [
        PortBundle(
            name="s_axil",
            protocol="axi4-lite",
            role="target",
            clock=AXI_CLOCK,
            reset=AXI_RESET,
            description="AXI4-Lite target serving the UART registers.",
            ports=[BundlePort(signal=sig, role_name=sig) for sig in axil_ports()],
        ),
        PortBundle(
            name="serial",
            protocol="uart",
            role="initiator",
            clock=AXI_CLOCK,
            reset=AXI_RESET,
            description="Asynchronous serial link; both lines idle high.",
            ports=[
                BundlePort(signal="uart_tx", role_name="tx"),
                BundlePort(signal="uart_rx", role_name="rx"),
            ],
        ),
    ]


def port_groups(opts: AxilUartOptions) -> list[PortGroup]:  # noqa: ARG001
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
            name="Serial",
            ports=["uart_rx", "uart_tx"],
            description="Asynchronous serial link (bundle `serial`); both lines idle high.",
        ),
    ]


def explain(opts: AxilUartOptions) -> ExplanationDoc:
    regmap = register_map(opts)
    signals = [
        SignalDoc(name=AXI_CLOCK, direction="input", description="AXI clock."),
        SignalDoc(
            name=f"{AXI_RESET}_n",
            direction="input",
            description="AXI reset, active-low (the spec calls it ARESETn).",
        ),
    ]
    reads = {"awready", "wready", "bresp", "bvalid", "arready", "rdata", "rresp", "rvalid"}
    signals += [
        SignalDoc(
            name=sig,
            direction="output" if sig in reads else "input",
            description="AXI4-Lite signal; see the register block's datasheet.",
        )
        for sig in axil_ports()
    ]
    signals += [
        SignalDoc(
            name="uart_rx",
            direction="input",
            description=(
                f"Serial input, asynchronous; synchronised through "
                f"{opts.input_sync_stages} flip-flops before sampling. Idles high."
            ),
        ),
        SignalDoc(
            name="uart_tx",
            direction="output",
            description="Serial output; idles high, low during a start bit.",
        ),
    ]

    return ExplanationDoc(
        purpose=(
            "An AXI4-Lite UART in 8N1 framing — 8 data bits, no parity, one "
            "stop bit — with a programmable baud divisor. The AXI frontend is "
            "the register-block generator spliced into this module, so the "
            "register map the datasheet documents is the one the decode is "
            "built from."
        ),
        configuration=[
            f"Reset baud divisor: {opts.default_divisor} clocks per bit "
            f"(BAUDDIV is writable at run time)",
            f"Input synchroniser: {opts.input_sync_stages} stages",
            "Framing: 8N1 (fixed)",
            f"Registers: {len(regmap.registers)} "
            f"({1 << regmap.addr_width} B decoded, {regmap.span_bytes()} B used)",
            f"Reset: {opts.reset_style}, active-low (fixed by AXI4-Lite)",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The active-low {opts.reset_style} reset returns both state machines to "
            "idle and drives uart_tx high. The receive synchroniser resets high too: "
            "coming out of reset with it low would look exactly like a start bit and "
            "the receiver would frame on noise. BAUDDIV returns to its reset divisor."
        ),
        assumptions=[
            "uart_rx is asynchronous and is synchronised before sampling.",
            "BAUDDIV is at least 2: the receiver waits half a divisor to reach "
            "mid-bit, and half of one is zero.",
            "Software writes TXDATA only while STATUS.tx_busy is clear; a write "
            "during a transmission is ignored rather than queued.",
            "Both ends agree on the line rate; there is no auto-baud.",
        ],
        limitations=[
            "8N1 only: no parity, no 5/6/7-bit words, no two-stop-bit mode.",
            "No FIFOs — one byte deep each way. A second byte arriving before "
            "software reads RXDATA sets STATUS.rx_overrun and the older byte is "
            "lost.",
            "Status flags are write-1-to-clear rather than read-to-clear: the "
            "register block has no read-side effect, and adding one for a single "
            "user was not worth a new access type.",
            "No hardware flow control (RTS/CTS) and no break detection.",
            "A framing error sets STATUS.frame_error but the byte is still "
            "delivered; the receiver does not resynchronise mid-frame.",
        ],
    )


@dataclass(frozen=True)
class _AxilUartIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "axil-uart"
    name: str = "AXI4-Lite UART"
    description: str = (
        "8N1 UART with a programmable baud divisor, transmit and receive state "
        "machines, and an AXI4-Lite register frontend spliced in from the "
        "register-block generator."
    )
    kind: str = "ip"
    maturity: str = "beta"
    options_model: type[AxilUartOptions] = AxilUartOptions

    def generate(self, opts: AxilUartOptions) -> Module:
        return generate(opts)

    def explain(self, opts: AxilUartOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: AxilUartOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: AxilUartOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: AxilUartOptions) -> RegisterMap:
        return register_map(opts)

    def bundles(self, opts: AxilUartOptions) -> list[PortBundle]:
        return bundles(opts)


IP = _AxilUartIp()

__all__ = [
    "AxilUartOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "register_map",
    "bundles",
    "IP",
]
