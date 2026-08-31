"""AXI4-Lite I2C master (Phase-4 P4-07).

An open-drain I2C master on the P4-05a register-block composition. Software
drives the bus one **primitive at a time** through a command register —
optionally a START, then one byte written or read, then optionally a STOP —
which is how a real transaction is assembled:

    addr+W, register index, STOP; then addr+R, data, NACK, STOP

Open drain, without ``inout``
-----------------------------

I2C lines are never driven high: a device either pulls low or releases. The
IR has no ``inout``, and it does not need one — the module exposes only the
pull-down enables and the sensed levels::

    scl_oe / sda_oe   1 = pull the line low
    scl_in / sda_in   the level actually on the wire

so a pad is ``line = oe ? 1'b0 : 1'bz``. Nothing here ever drives a one, which
is exactly the open-drain contract, and the wired-AND happens where it really
happens — on the wire.

Bus drivers are combinational from registered state
---------------------------------------------------

``scl_oe`` and ``sda_oe`` are continuous functions of the registered state,
phase and shift register rather than being assigned inside the FSM. An I2C bit
is four quarter-phases, and writing "on entering phase 2, release SCL" as
sequential code means every phase transition carries a little bundle of
side effects — which is where these state machines go wrong. As pure functions
of registers they still only change just after a clock edge, so there is no
glitch risk, and each line's behaviour can be read in one place.

Clock stretching
----------------

A slave may hold SCL low to buy time. After the master releases SCL the phase
counter does not advance until ``scl_in`` actually reads high, so a stretched
clock stalls the whole transfer rather than the master running ahead of a
slave that is not listening.
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
    Ternary,
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
from .verification import VerificationSpec, axil_verification

_MODULE_NAME = "axil_i2c"
_DATA_WIDTH = 32
_DIV_BITS = 16

# Transfer states. Each non-idle state runs the same four quarter-phases.
_IDLE, _START, _BIT, _ACK, _STOP, _DONE = range(6)
_STATE_BITS = 3
_PHASES = 4


class AxilI2cOptions(CommonOptions):
    """Configuration for the AXI4-Lite I2C master."""

    default_divisor: int = Field(
        default=2,
        ge=1,
        le=(1 << _DIV_BITS) - 1,
        description=(
            "Reset value of CLKDIV: aclk cycles per *quarter* bit period, so an "
            "SCL period is four times this. Quarter phases are what give SDA a "
            "setup window while SCL is low."
        ),
    )
    input_sync_stages: int = Field(
        default=2,
        ge=2,
        le=4,
        description="Flip-flop stages between the sensed bus lines and the FSM.",
    )
    reset_style: str = Field(
        default="sync",
        pattern="^(sync|async)$",
        description="Reset timing; the polarity is fixed active-low by AXI4-Lite.",
    )


def register_map(opts: AxilI2cOptions) -> RegisterMap:
    return RegisterMap(
        name="I2C",
        data_width=_DATA_WIDTH,
        addr_width=5,
        registers=[
            Register(
                name="STATUS", offset=0x0, description="Transfer status.",
                fields=[
                    RegisterField(
                        name="busy", lsb=0, width=1, access="ro",
                        description="A command is in progress.",
                    ),
                    RegisterField(
                        name="done", lsb=1, width=1, access="w1c",
                        description="The last command finished; write 1 to clear.",
                    ),
                    RegisterField(
                        name="ack_err", lsb=2, width=1, access="w1c",
                        description="The slave did not acknowledge a written byte.",
                    ),
                    RegisterField(
                        name="rx_valid", lsb=3, width=1, access="w1c",
                        description="RXDATA holds a byte read from the bus.",
                    ),
                ],
            ),
            Register(
                name="CMD", offset=0x4,
                description="Writing this register runs one bus command.",
                fields=[
                    RegisterField(
                        name="start", lsb=0, width=1, access="wo",
                        description="Emit a START condition first.",
                    ),
                    RegisterField(
                        name="write", lsb=1, width=1, access="wo",
                        description="Shift TXDATA out and read the slave's ACK.",
                    ),
                    RegisterField(
                        name="read", lsb=2, width=1, access="wo",
                        description="Shift a byte in and send the ACK bit below.",
                    ),
                    RegisterField(
                        name="ack", lsb=3, width=1, access="wo",
                        description="On a read: 1 acknowledges, 0 sends NACK (last byte).",
                    ),
                    RegisterField(
                        name="stop", lsb=4, width=1, access="wo",
                        description="Emit a STOP condition afterwards.",
                    ),
                ],
            ),
            Register(
                name="TXDATA", offset=0x8, description="Byte to write, MSB first.",
                fields=[
                    RegisterField(
                        name="data", lsb=0, width=8, access="wo",
                        description="Address+R/W byte or data byte; reads back as zero.",
                    )
                ],
            ),
            Register(
                name="RXDATA", offset=0xC, description="Byte read from the bus.",
                fields=[
                    RegisterField(
                        name="data", lsb=0, width=8, access="ro",
                        description="Received byte; valid while STATUS.rx_valid is set.",
                    )
                ],
            ),
            Register(
                name="CLKDIV", offset=0x10,
                description="Quarter bit period in aclk cycles.",
                fields=[
                    RegisterField(
                        name="div", lsb=0, width=_DIV_BITS, access="rw",
                        reset=opts.default_divisor,
                        description="Quarter period; an SCL period is four times this.",
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


def _state(value: int) -> Const:
    return Const(value, width=Const(_STATE_BITS), base=ConstBase.BIN)


def _phase(value: int) -> Const:
    return Const(value, width=Const(2), base=ConstBase.BIN)


def _eq(a, b) -> BinOp:
    return BinOp(BinOpKind.EQ, a, b)


def _or(a, b) -> BinOp:
    return BinOp(BinOpKind.LOR, a, b)


def _and(a, b) -> BinOp:
    return BinOp(BinOpKind.LAND, a, b)


def _not(expr) -> UnaryOp:
    return UnaryOp(UnaryOpKind.NOT_LOGICAL, expr)


def _in_state(value: int) -> BinOp:
    return _eq(Ref("state"), _state(value))


def _in_phase(value: int) -> BinOp:
    return _eq(Ref("phase"), _phase(value))


def scl_drive_expr():
    """When the master pulls SCL low.

    START releases SCL for the first three quarters and pulls it low in the
    last, so the SDA fall in phase 2 happens with SCL high. A data or ACK bit
    holds SCL low around the middle two quarters, giving SDA a setup window
    before the rising edge. STOP pulls low only in the first quarter, so SCL is
    already high when SDA is released.
    """
    bit_like = _or(_in_state(_BIT), _in_state(_ACK))
    return Ternary(
        bit_like,
        _or(_in_phase(0), _in_phase(3)),
        Ternary(
            _in_state(_START),
            _in_phase(3),
            Ternary(_in_state(_STOP), _in_phase(0), _zero()),
        ),
    )


def sda_drive_expr():
    """When the master pulls SDA low.

    A written bit pulls low for a zero and releases for a one — never drives a
    high, which is the whole point of open drain. A read releases SDA so the
    slave can drive it, and the ACK quarter afterwards is the one place the
    master answers: ``CMD.ack`` low means NACK, which is how a master ends a
    read.
    """
    writing = Ref(_f("CMD", "write"))
    return Ternary(
        _in_state(_START),
        _or(_in_phase(2), _in_phase(3)),
        Ternary(
            _in_state(_BIT),
            Ternary(writing, _not(Bit(Ref("tx_shift"), Const(7))), _zero()),
            Ternary(
                _in_state(_ACK),
                # On a write the slave answers, so release. On a read the
                # master answers with CMD.ack.
                Ternary(writing, _zero(), Ref(_f("CMD", "ack"))),
                Ternary(_in_state(_STOP), _not(_in_phase(3)), _zero()),
            ),
        ),
    )


def _quarter_elapsed() -> BinOp:
    """``q_cnt`` has reached the end of a quarter period."""
    return _eq(
        Ref("q_cnt"),
        BinOp(BinOpKind.SUB, Ref(_f("CLKDIV", "div")), _one(_DIV_BITS)),
    )


def _advance_expr() -> BinOp:
    """A quarter has elapsed — and, in phase 2, SCL has actually gone high.

    That second term is clock stretching: the master released SCL, but a slave
    holding it low means the bit has not happened yet.
    """
    return _and(_quarter_elapsed(), _or(_not(_in_phase(2)), Ref("scl_sensed")))


def _next_state_after_phase3(opts: AxilI2cOptions) -> list:  # noqa: ARG001
    """Where each state goes once its fourth quarter completes."""
    transfers = _or(Ref(_f("CMD", "write")), Ref(_f("CMD", "read")))
    after_bit = Ternary(
        _eq(Ref("bit_cnt"), Const(7, width=Const(3))),
        _state(_ACK),
        _state(_BIT),
    )
    after_start = Ternary(
        transfers,
        _state(_BIT),
        Ternary(Ref(_f("CMD", "stop")), _state(_STOP), _state(_DONE)),
    )
    after_ack = Ternary(Ref(_f("CMD", "stop")), _state(_STOP), _state(_DONE))
    return [
        Assign(Ref("phase"), _phase(0)),
        If(
            _in_state(_START),
            then=[Assign(Ref("state"), after_start)],
            else_=[
                If(
                    _in_state(_BIT),
                    then=[
                        Assign(Ref("state"), after_bit),
                        Assign(
                            Ref("bit_cnt"),
                            BinOp(BinOpKind.ADD, Ref("bit_cnt"), _one(3)),
                        ),
                        # Shifting on the way out of the fourth quarter keeps
                        # the outgoing bit stable for the whole SCL high time.
                        Assign(
                            Ref("tx_shift"),
                            Concat([Slice(Ref("tx_shift"), Const(6), Const(0)), _zero(1)]),
                        ),
                    ],
                    else_=[
                        If(
                            _in_state(_ACK),
                            then=[Assign(Ref("state"), after_ack)],
                            else_=[Assign(Ref("state"), _state(_DONE))],
                        )
                    ],
                )
            ],
        ),
    ]


def _sample_at_phase2() -> list:
    """What the master reads while SCL is high.

    A read shifts the sensed SDA in. A write reads the slave's acknowledgement
    in the ACK quarter — SDA still high there means nobody pulled it down.

    The ``phase == 2`` guard is the whole point and was missing at first: this
    runs on every quarter's advance, so without it a read shifted in four
    samples per bit instead of one. The write path hid the bug — its only
    sample is the ACK, and the slave holds SDA low across all four ACK
    quarters, so sampling four times gave the same answer. Only the read
    transaction exposed it.
    """
    return [
        If(
            _in_phase(2),
            then=[
                If(
                    _and(_in_state(_BIT), Ref(_f("CMD", "read"))),
                    then=[
                        Assign(
                            Ref("rx_shift"),
                            Concat(
                                [
                                    Slice(Ref("rx_shift"), Const(6), Const(0)),
                                    Ref("sda_sensed"),
                                ]
                            ),
                        )
                    ],
                ),
                If(
                    _and(_in_state(_ACK), Ref(_f("CMD", "write"))),
                    then=[Assign(Ref(_set("STATUS", "ack_err")), Ref("sda_sensed"))],
                ),
            ],
        )
    ]


def _sync_stage(line: str, index: int) -> str:
    return f"{line}_sync{index}"


def generate(opts: AxilI2cOptions) -> Module:
    """Build the I2C master IR by splicing the register block in."""
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
        Port("scl_in", IN, bit(), doc="Level sensed on SCL (low while a slave stretches)"),
        Port("sda_in", IN, bit(), doc="Level sensed on SDA"),
        Port("scl_oe", OUT, bit(), doc="Pull SCL low; the line is never driven high"),
        Port("sda_oe", OUT, bit(), doc="Pull SDA low; the line is never driven high"),
    ]

    scl_stages = [_sync_stage("scl", i) for i in range(opts.input_sync_stages)]
    sda_stages = [_sync_stage("sda", i) for i in range(opts.input_sync_stages)]
    signals: list[ModuleItem] = [
        *[Signal(s, bit(), doc="SCL synchroniser") for s in scl_stages],
        *[Signal(s, bit(), doc="SDA synchroniser") for s in sda_stages],
        Signal("state", vec(_STATE_BITS),
               doc="0 IDLE, 1 START, 2 BIT, 3 ACK, 4 STOP, 5 DONE"),
        Signal("phase", vec(2), doc="Quarter of the bit period, 0..3"),
        Signal("q_cnt", vec(_DIV_BITS), doc="aclk cycles within one quarter"),
        Signal("bit_cnt", vec(3), doc="Bits transferred so far"),
        Signal("tx_shift", vec(8), doc="Outgoing byte, empties from the MSB"),
        Signal("rx_shift", vec(8), doc="Incoming byte, fills from the LSB"),
        Signal("cmd_go", bit(), doc="CMD write strobe, delayed one cycle"),
        Signal("scl_sensed", bit(), doc="Synchronised SCL"),
        Signal("sda_sensed", bit(), doc="Synchronised SDA"),
    ]

    set_signals = [
        _set("STATUS", "done"),
        _set("STATUS", "ack_err"),
        _set("STATUS", "rx_valid"),
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
            Assign(Ref("state"), _state(_IDLE)),
            Assign(Ref("phase"), _phase(0)),
            Assign(Ref("q_cnt"), _zero(_DIV_BITS)),
            Assign(Ref("bit_cnt"), _zero(3)),
            Assign(Ref("tx_shift"), _zero(8)),
            Assign(Ref("rx_shift"), _zero(8)),
            Assign(Ref("cmd_go"), _zero()),
            Assign(Ref(_f("RXDATA", "data")), _zero(8)),
            *[Assign(Ref(name), _zero()) for name in set_signals],
            # The bus is released out of reset: both lines idle high, which is
            # the only state a master may leave a shared bus in.
            *[Assign(Ref(s), _one()) for s in scl_stages + sda_stages],
        ],
        body=[
            Comment("One-cycle pulses, defaulted low and raised below",
                    level=CommentLevel.VERBOSE),
            *[Assign(Ref(name), _zero()) for name in set_signals],
            Comment("Both bus lines are asynchronous: other devices drive them",
                    level=CommentLevel.VERBOSE),
            Assign(Ref(scl_stages[0]), Ref("scl_in")),
            *[
                Assign(Ref(scl_stages[i]), Ref(scl_stages[i - 1]))
                for i in range(1, len(scl_stages))
            ],
            Assign(Ref(sda_stages[0]), Ref("sda_in")),
            *[
                Assign(Ref(sda_stages[i]), Ref(sda_stages[i - 1]))
                for i in range(1, len(sda_stages))
            ],
            # The strobe is delayed a cycle so the CMD and TXDATA fields have
            # taken their new values (see docs/IPS.md).
            Assign(Ref("cmd_go"), Ref(write_strobe_name("CMD"))),
            If(
                _in_state(_IDLE),
                then=[
                    If(
                        Ref("cmd_go"),
                        then=[
                            Assign(Ref("q_cnt"), _zero(_DIV_BITS)),
                            Assign(Ref("phase"), _phase(0)),
                            Assign(Ref("bit_cnt"), _zero(3)),
                            Assign(Ref("rx_shift"), _zero(8)),
                            Assign(Ref("tx_shift"), Ref(_f("TXDATA", "data"))),
                            Assign(
                                Ref("state"),
                                Ternary(
                                    Ref(_f("CMD", "start")),
                                    _state(_START),
                                    Ternary(
                                        _or(
                                            Ref(_f("CMD", "write")),
                                            Ref(_f("CMD", "read")),
                                        ),
                                        _state(_BIT),
                                        Ternary(
                                            Ref(_f("CMD", "stop")),
                                            _state(_STOP),
                                            _state(_DONE),
                                        ),
                                    ),
                                ),
                            ),
                        ],
                    )
                ],
                else_=[
                    If(
                        _in_state(_DONE),
                        then=[
                            Assign(Ref("state"), _state(_IDLE)),
                            Assign(Ref(_set("STATUS", "done")), _one()),
                            If(
                                Ref(_f("CMD", "read")),
                                then=[
                                    Assign(Ref(_f("RXDATA", "data")), Ref("rx_shift")),
                                    Assign(Ref(_set("STATUS", "rx_valid")), _one()),
                                ],
                            ),
                        ],
                        else_=[
                            If(
                                _advance_expr(),
                                then=[
                                    Assign(Ref("q_cnt"), _zero(_DIV_BITS)),
                                    *_sample_at_phase2(),
                                    If(
                                        _in_phase(3),
                                        then=_next_state_after_phase3(opts),
                                        else_=[
                                            Assign(
                                                Ref("phase"),
                                                BinOp(
                                                    BinOpKind.ADD,
                                                    Ref("phase"),
                                                    _phase(1),
                                                ),
                                            )
                                        ],
                                    ),
                                ],
                                else_=[
                                    # Saturate rather than keep counting: while
                                    # a slave stretches the clock the quarter
                                    # has already elapsed, and a free-running
                                    # counter would wrap all the way round
                                    # before the advance condition came true
                                    # again. Only reachable with stretching,
                                    # which is why the testbench stretches.
                                    If(
                                        _not(_quarter_elapsed()),
                                        then=[
                                            Assign(
                                                Ref("q_cnt"),
                                                BinOp(
                                                    BinOpKind.ADD,
                                                    Ref("q_cnt"),
                                                    _one(_DIV_BITS),
                                                ),
                                            )
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            ),
        ],
    )
    glue: list[ModuleItem] = [
        ContAssign(Ref("scl_sensed"), Ref(scl_stages[-1])),
        ContAssign(Ref("sda_sensed"), Ref(sda_stages[-1])),
        ContAssign(Ref(_f("STATUS", "busy")), _not(_in_state(_IDLE))),
        ContAssign(Ref("scl_oe"), scl_drive_expr()),
        ContAssign(Ref("sda_oe"), sda_drive_expr()),
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


def _description(opts: AxilI2cOptions) -> str:
    return f"AXI4-Lite I2C master, quarter-period divisor {opts.default_divisor}"


# --------------------------------------------------------------------------- #
# Directed testbench
# --------------------------------------------------------------------------- #
#
# Timing, derived from the FSM above.
#
# `AxilSequencer.write` drives at cycle c; the CMD strobe lands at c+1, cmd_go
# at c+2, and the FSM leaves IDLE at edge c+3 — call that A. From there every
# quarter lasts `div` cycles, so global quarter q occupies
# [A + q*div, A + (q+1)*div - 1], and the FSM samples the bus at the end of a
# quarter, i.e. at cycle A + (q+1)*div - 1.
#
# A stretched clock shifts everything after it by the stall length, which is
# why the plan below maps quarters to cycles through one function instead of
# scattering arithmetic through the checks.

_CMD_START, _CMD_WRITE, _CMD_READ, _CMD_ACK, _CMD_STOP = (1, 2, 4, 8, 16)


def _quarter_plan(cmd: int) -> list[tuple[int, int]]:
    """The (state, phase) the FSM is in for each global quarter of a command."""
    plan: list[tuple[int, int]] = []
    if cmd & _CMD_START:
        plan += [(_START, p) for p in range(_PHASES)]
    if cmd & (_CMD_WRITE | _CMD_READ):
        for _ in range(8):
            plan += [(_BIT, p) for p in range(_PHASES)]
        plan += [(_ACK, p) for p in range(_PHASES)]
    if cmd & _CMD_STOP:
        plan += [(_STOP, p) for p in range(_PHASES)]
    return plan


def _expected_drive(state: int, phase: int, cmd: int, byte: int, index: int) -> tuple[int, int]:
    """``(scl_oe, sda_oe)`` the drivers produce — the same rules as the RTL,
    written independently so a disagreement shows up as a failing check."""
    if state in (_BIT, _ACK):
        scl = int(phase in (0, 3))
    elif state == _START:
        scl = int(phase == 3)
    elif state == _STOP:
        scl = int(phase == 0)
    else:
        scl = 0

    if state == _START:
        sda = int(phase >= 2)
    elif state == _BIT:
        sda = 0 if cmd & _CMD_READ else int(not ((byte >> (7 - index)) & 1))
    elif state == _ACK:
        sda = 0 if cmd & _CMD_WRITE else int(bool(cmd & _CMD_ACK))
    elif state == _STOP:
        sda = int(phase != 3)
    else:
        sda = 0
    return scl, sda


class _Bus:
    """Maps global quarters to cycles, allowing for a stretched clock.

    All the arithmetic lives here so a stretch shifts every later check by the
    stall length automatically, instead of the offset being written out at each
    call site and quietly forgotten at one of them.
    """

    def __init__(self, active: int, div: int, stretch_at: int | None, stall: int) -> None:
        self.active = active
        self.div = div
        self.stretch_at = stretch_at
        self.stall = stall

    def start_of(self, quarter: int) -> int:
        delay = self.stall if self.stretch_at is not None and quarter > self.stretch_at else 0
        return self.active + quarter * self.div + delay

    def sample_of(self, quarter: int) -> int:
        """The cycle whose value the FSM latches when leaving ``quarter``."""
        return self.start_of(quarter + 1) - 1

    def end(self, quarters: int) -> int:
        return self.start_of(quarters)


def tb_spec(opts: AxilI2cOptions) -> TbSpec:
    """Write a byte with a stretched clock, then read one back.

    The bus lines are modelled the way a real one behaves: the testbench only
    drives ``sda_in`` at the moments the master is *not* driving SDA, because
    everywhere else the wired-AND is the master's own output and the value the
    testbench supplies would be meaningless. ``scl_in`` is held high except for
    a deliberate stall, which is a bus with no other master on it.
    """
    regmap = register_map(opts)
    model = RegisterModel(regmap)
    seq = AxilSequencer()
    full_strb = (1 << (_DATA_WIDTH // 8)) - 1
    div = opts.default_divisor
    stages = opts.input_sync_stages

    status = regmap.register("STATUS").offset
    cmd_addr = regmap.register("CMD").offset
    txdata = regmap.register("TXDATA").offset
    rxdata = regmap.register("RXDATA").offset

    # Cycle 0 — the master must be off the bus: both lines released.
    seq.expect(0, "scl_oe", 0)
    seq.expect(0, "sda_oe", 0)
    seq.expect(0, "bvalid", 0)
    seq.drive(scl_in=1, sda_in=1)
    seq.idle()

    # ---- write transaction, with the slave stretching the clock -----------
    tx_byte = 0x4B  # not a bit-palindrome, so bit order is observable
    resp = model.write(txdata, tx_byte, full_strb)
    seq.write(txdata, tx_byte, full_strb, resp, [])

    cmd = _CMD_START | _CMD_WRITE | _CMD_STOP
    plan = _quarter_plan(cmd)
    request = seq.cycle
    resp = model.write(cmd_addr, cmd, full_strb)
    seq.write(cmd_addr, cmd, full_strb, resp, [])
    active = request + 3

    # Stretch during the first data bit's high phase. The stall has to outlast
    # the synchroniser or the master would never see the line low at all.
    stretch_quarter = 6  # first BIT, phase 2
    stall = max(2 * div, stages + 2)
    bus = _Bus(active, div, stretch_quarter, stall)

    # Hold SCL low across that quarter, early enough for the synchroniser.
    seq.cycle = max(bus.start_of(stretch_quarter) - stages, 0)
    seq.drive(scl_in=0)
    seq.cycle = bus.start_of(stretch_quarter) + stall - stages
    seq.drive(scl_in=1)

    bit_index = -1
    for quarter, (state, phase) in enumerate(plan):
        if state == _BIT and phase == 0:
            bit_index += 1
        scl, sda = _expected_drive(state, phase, cmd, tx_byte, max(bit_index, 0))
        at = bus.start_of(quarter)
        seq.expect(at, "scl_oe", scl)
        seq.expect(at, "sda_oe", sda)

    # The slave acknowledges: pull SDA low across the ACK quarters. The master
    # has released SDA there, so this is the only thing driving the line.
    ack_quarter = next(q for q, (s, _p) in enumerate(plan) if s == _ACK)
    seq.cycle = max(bus.start_of(ack_quarter) - stages, 0)
    seq.drive(sda_in=0)
    seq.cycle = bus.start_of(ack_quarter + _PHASES)
    seq.drive(sda_in=1)

    # DONE is entered one quarter past the plan, pulses its flag the cycle
    # after that, and the register block latches it one more cycle on — three
    # separate edges, which is why this is not simply "the transfer is over".
    seq.cycle = bus.end(len(plan)) + 3
    model.hardware_set("STATUS", "done", 1)
    model.drive_ro("STATUS", "busy", 0)
    seq.read(status, *model.read(status))

    clear = model.read(status)[0]
    resp = model.write(status, clear, full_strb)
    seq.write(status, clear, full_strb, resp, [])

    # ---- read transaction, ending in a NACK --------------------------------
    # A master NACKs the last byte of a read; CMD.ack stays clear, so the
    # master releases SDA in the ACK quarter instead of pulling it low.
    rx_byte = 0x2D
    read_cmd = _CMD_START | _CMD_READ | _CMD_STOP
    read_plan = _quarter_plan(read_cmd)
    request = seq.cycle
    resp = model.write(cmd_addr, read_cmd, full_strb)
    seq.write(cmd_addr, read_cmd, full_strb, resp, [])
    read_bus = _Bus(request + 3, div, None, 0)

    # The slave drives each bit. Placing the drive `stages` before the bit's
    # first quarter means the synchronised value changes exactly at that
    # quarter — after the previous bit was sampled, and settled well before
    # this one is.
    first_bit = next(q for q, (st, ph) in enumerate(read_plan) if st == _BIT and ph == 0)
    for index in range(8):
        level = (rx_byte >> (7 - index)) & 1  # MSB first
        seq.cycle = max(read_bus.start_of(first_bit + 4 * index) - stages, 0)
        seq.drive(sda_in=level)

    # The master drives SDA again in the ACK quarter, so release the line.
    read_ack = next(q for q, (st, _p) in enumerate(read_plan) if st == _ACK)
    seq.cycle = max(read_bus.start_of(read_ack) - stages, 0)
    seq.drive(sda_in=1)

    # NACK means the master leaves SDA released through the ACK quarters.
    for quarter in range(read_ack, read_ack + _PHASES):
        state, phase = read_plan[quarter]
        scl, sda = _expected_drive(state, phase, read_cmd, 0, 0)
        seq.expect(read_bus.start_of(quarter), "scl_oe", scl)
        seq.expect(read_bus.start_of(quarter), "sda_oe", sda)

    seq.cycle = read_bus.end(len(read_plan)) + 3
    model.hardware_set("STATUS", "done", 1)
    model.hardware_set("STATUS", "rx_valid", 1)
    model.drive_ro("RXDATA", "data", rx_byte)
    seq.read(status, *model.read(status))
    seq.read(rxdata, *model.read(rxdata))

    items: list[AssertionItem] = [
        ResetKnownValue(name="scl_released_after_reset", signal="scl_oe", value=0, width=1),
        ResetKnownValue(name="sda_released_after_reset", signal="sda_oe", value=0, width=1),
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


def bundles(opts: AxilI2cOptions) -> list[PortBundle]:  # noqa: ARG001
    return [
        PortBundle(
            name="s_axil", protocol="axi4-lite", role="target",
            clock=AXI_CLOCK, reset=AXI_RESET,
            description="AXI4-Lite target serving the I2C registers.",
            ports=[BundlePort(signal=sig, role_name=sig) for sig in axil_ports()],
        ),
        PortBundle(
            name="i2c", protocol="i2c", role="initiator",
            clock=AXI_CLOCK, reset=AXI_RESET,
            description=(
                "Open-drain I2C bus: pull-down enables and sensed levels, with "
                "no driven highs and no bidirectional net."
            ),
            ports=[
                BundlePort(signal="scl_oe", role_name="scl_oe"),
                BundlePort(signal="scl_in", role_name="scl_in"),
                BundlePort(signal="sda_oe", role_name="sda_oe"),
                BundlePort(signal="sda_in", role_name="sda_in"),
            ],
        ),
    ]


def port_groups(opts: AxilI2cOptions) -> list[PortGroup]:  # noqa: ARG001
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
            name="I2C bus", ports=["scl_in", "sda_in", "scl_oe", "sda_oe"],
            description=(
                "Open-drain bus (bundle `i2c`). A pad is `line = oe ? 1'b0 : 1'bz`."
            ),
        ),
    ]


def explain(opts: AxilI2cOptions) -> ExplanationDoc:
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
            name="scl_in", direction="input",
            description="Level sensed on SCL; low while a slave stretches the clock.",
        ),
        SignalDoc(
            name="sda_in", direction="input", description="Level sensed on SDA.",
        ),
        SignalDoc(
            name="scl_oe", direction="output",
            description="Pull SCL low. The line is never driven high.",
        ),
        SignalDoc(
            name="sda_oe", direction="output",
            description="Pull SDA low. The line is never driven high.",
        ),
    ]

    return ExplanationDoc(
        purpose=(
            "An open-drain AXI4-Lite I2C master. Software runs the bus one "
            "primitive at a time through CMD — optionally a START, then one "
            "byte written or read, then optionally a STOP — which is how a real "
            "transaction is assembled. The AXI frontend is the register-block "
            "generator spliced into this module."
        ),
        configuration=[
            f"Quarter-period divisor: {opts.default_divisor} aclk cycles "
            f"(an SCL period is four times this; CLKDIV is writable at run time)",
            f"Input synchroniser: {opts.input_sync_stages} stages on both lines",
            f"Registers: {len(regmap.registers)} "
            f"({1 << regmap.addr_width} B decoded, {regmap.span_bytes()} B used)",
            f"Reset: {opts.reset_style}, active-low (fixed by AXI4-Lite)",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The active-low {opts.reset_style} reset returns the FSM to idle and "
            "releases both pull-downs, so the master comes up off a shared bus "
            "rather than holding it. The synchronisers reset high, which is the "
            "idle level of an open-drain line."
        ),
        assumptions=[
            "A pad turns each enable into an open-drain driver: "
            "`line = oe ? 1'b0 : 1'bz`, with an external pull-up.",
            "Both bus lines are asynchronous to aclk — other devices drive them — "
            "so each is synchronised before the FSM looks at it.",
            "Software assembles transactions from CMD primitives and observes "
            "STATUS.ack_err after each written byte.",
            "CLKDIV is at least 1; a quarter period of zero has no meaning.",
        ],
        limitations=[
            "Single master: no bus arbitration and no lost-arbitration detection, "
            "so this must be the only master on the bus.",
            "No repeated START as a distinct primitive — issue a STOP and a fresh "
            "START, which works with most devices but is not identical on the wire.",
            "No 10-bit addressing and no general-call handling; the address is "
            "just the first byte software writes.",
            "No SMBus timeout, no PEC, no clock-low timeout — a slave that "
            "stretches forever stalls the master forever.",
            "No slave mode.",
        ],
    )


def verification_spec(opts: AxilI2cOptions) -> VerificationSpec:  # noqa: ARG001
    """The shared AXI4-Lite monitor + liveness/stability checker.

    Every AXI IP splices in the same register-block frontend, so they all have
    the same bus face and the same bus properties; the scaffold is written once
    in ``ips/verification.py`` rather than seven times here.
    """
    return axil_verification(_MODULE_NAME)


@dataclass(frozen=True)
class _AxilI2cIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "axil-i2c"
    name: str = "AXI4-Lite I2C Master"
    description: str = (
        "Open-drain I2C master with START/STOP primitives, byte transfers with "
        "ACK/NACK and clock-stretch support; AXI4-Lite register frontend "
        "spliced in from the register-block generator."
    )
    kind: str = "ip"
    maturity: str = "beta"
    options_model: type[AxilI2cOptions] = AxilI2cOptions

    def generate(self, opts: AxilI2cOptions) -> Module:
        return generate(opts)

    def explain(self, opts: AxilI2cOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: AxilI2cOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: AxilI2cOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: AxilI2cOptions) -> RegisterMap:
        return register_map(opts)

    def bundles(self, opts: AxilI2cOptions) -> list[PortBundle]:
        return bundles(opts)

    def verification_spec(self, opts: AxilI2cOptions) -> VerificationSpec:
        return verification_spec(opts)


IP = _AxilI2cIp()

__all__ = [
    "AxilI2cOptions", "generate", "explain", "port_groups", "tb_spec",
    "register_map", "bundles", "IP",
]
