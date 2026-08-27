"""AXI4-Lite timer / counter (Phase-4 P4-08).

A prescaled down-counter with a software-visible reload value, one-shot or
periodic operation, and a maskable interrupt. Built on the register-block
composition proved in P4-05a: the AXI frontend is spliced in with
``field_ports=False`` and this module appends the counter around it.

Registers
---------

    0x00  CTRL      enable      [0]   RW   run the counter
                    auto_reload [1]   RW   1 = periodic, 0 = one-shot
                    irq_enable  [2]   RW   unmask the interrupt output
    0x04  RELOAD    value             RW   value loaded at start and at expiry
    0x08  COUNT     value             RO   the live counter
    0x0C  PRESCALE  value             RW   clocks per tick, minus one
    0x10  STATUS    expired     [0]   W1C  the counter reached zero

Why a *down* counter with a terminal count of zero
---------------------------------------------------

An up-counter compared against RELOAD needs a full-width comparator on every
clock; a down-counter needs only a zero test, which is a NOR of the counter
bits. The difference is invisible at 32 bits in simulation and very visible in
a synthesised timing report, and the software interface is identical either
way. The cost is one documented off-by-one: the period is ``RELOAD + 1`` ticks,
because the counter visits zero before expiring.

Interrupt timing is a consequence of composition
------------------------------------------------

``expired`` is a ``w1c`` field, so the counter raises it through the register
block's set input rather than writing the field directly. That means the flag
becomes readable — and ``irq`` rises — **two** clocks after the counter reaches
its terminal count: one for the set request to be sampled by the register
block's own ``always_ff``, one for software to see the result. The testbench
derives that latency rather than measuring it, and the datasheet states it.

Disabling reloads, it does not pause
------------------------------------

While ``CTRL.enable`` is low the counter is continuously reloaded from RELOAD,
so enabling always starts a full period. There is no pause-and-resume: a timer
that resumes mid-period is a different (and rarer) device, and conflating the
two would make ``COUNT`` mean different things depending on history.
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
from ..ir.build import OUT, bit, vec
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
    If,
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

_MODULE_NAME = "axil_timer"
_DATA_WIDTH = 32


# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #


class AxilTimerOptions(CommonOptions):
    """Configuration for the AXI4-Lite timer.

    Extends :class:`CommonOptions`: AXI4-Lite fixes the reset active-low, so
    there is no polarity option, exactly as for the register block.
    """

    counter_width: int = Field(
        default=32,
        ge=4,
        le=_DATA_WIDTH,
        description=(
            "Width of RELOAD and COUNT. Bits above this are reserved in both, "
            "so writing one returns SLVERR."
        ),
    )
    prescale_width: int = Field(
        default=16,
        ge=1,
        le=_DATA_WIDTH,
        description=(
            "Width of PRESCALE. A tick happens every PRESCALE+1 clocks, so the "
            "period is (RELOAD+1) * (PRESCALE+1) clocks."
        ),
    )
    reset_style: str = Field(
        default="sync",
        pattern="^(sync|async)$",
        description=(
            "Reset timing for the register block and the counter. The polarity "
            "is fixed active-low by AXI4-Lite."
        ),
    )


# --------------------------------------------------------------------------- #
# Register map
# --------------------------------------------------------------------------- #


def register_map(opts: AxilTimerOptions) -> RegisterMap:
    """CTRL / RELOAD / COUNT / PRESCALE / STATUS, in that order."""
    return RegisterMap(
        name="TIMER",
        data_width=_DATA_WIDTH,
        addr_width=5,  # five 4-byte registers fit in 32 bytes
        registers=[
            Register(
                name="CTRL",
                offset=0x00,
                description="Run control and interrupt mask.",
                fields=[
                    RegisterField(
                        name="enable", lsb=0, width=1, access="rw",
                        description="1 runs the counter; 0 holds it reloaded.",
                    ),
                    RegisterField(
                        name="auto_reload", lsb=1, width=1, access="rw",
                        description="1 restarts at expiry (periodic); 0 stops (one-shot).",
                    ),
                    RegisterField(
                        name="irq_enable", lsb=2, width=1, access="rw",
                        description="1 lets STATUS.expired drive the irq output.",
                    ),
                ],
            ),
            Register(
                name="RELOAD",
                offset=0x04,
                description="Value loaded into COUNT at start and at expiry.",
                fields=[
                    RegisterField(
                        name="value", lsb=0, width=opts.counter_width, access="rw",
                        description="Terminal count; the period is RELOAD+1 ticks.",
                    )
                ],
            ),
            Register(
                name="COUNT",
                offset=0x08,
                description="The live down-counter.",
                fields=[
                    RegisterField(
                        name="value", lsb=0, width=opts.counter_width, access="ro",
                        description="Ticks remaining before the next expiry.",
                    )
                ],
            ),
            Register(
                name="PRESCALE",
                offset=0x0C,
                description="Clock divider ahead of the counter.",
                fields=[
                    RegisterField(
                        name="value", lsb=0, width=opts.prescale_width, access="rw",
                        description="Clocks per tick, minus one; 0 ticks every clock.",
                    )
                ],
            ),
            Register(
                name="STATUS",
                offset=0x10,
                description="Expiry flag; write 1 to clear.",
                fields=[
                    RegisterField(
                        name="expired", lsb=0, width=1, access="w1c",
                        description="Set when COUNT reached zero and a tick fired.",
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


def _one(width: int = 1) -> Const:
    return Const(1, width=Const(width), base=ConstBase.BIN)


def _zero(width: int = 1) -> Const:
    return Const(0, width=Const(width), base=ConstBase.BIN)


def _eq(a, b) -> BinOp:
    return BinOp(BinOpKind.EQ, a, b)


def _not(expr) -> UnaryOp:
    return UnaryOp(UnaryOpKind.NOT_LOGICAL, expr)


def _tick_condition(opts: AxilTimerOptions) -> object:  # noqa: ARG001
    """The prescaler has counted a full division: this clock is a tick."""
    return _eq(Ref("pre_cnt"), Ref(_f("PRESCALE", "value")))


def _terminal_condition(opts: AxilTimerOptions) -> object:
    """COUNT has reached its terminal value, so this tick expires the timer."""
    return _eq(Ref(_f("COUNT", "value")), _zero(opts.counter_width))


def _reload_condition(opts: AxilTimerOptions) -> object:  # noqa: ARG001
    """Whether an expiry restarts the counter (periodic) or stops it (one-shot)."""
    return Ref(_f("CTRL", "auto_reload"))


def _counter_body(opts: AxilTimerOptions) -> list:
    """The prescaler and the down-counter, as one nested ``if``.

    Structure, outermost first:

    - disabled          -> reload COUNT, clear the prescaler, re-arm
    - running, tick     -> decrement, or expire at zero
    - running, no tick  -> advance the prescaler

    ``running`` is what makes one-shot mode stop *and stay stopped*: clearing
    ``CTRL.enable`` from hardware is not an option, because ``enable`` is an
    ``rw`` field the register block owns and software alone writes.
    """
    cw, pw = opts.counter_width, opts.prescale_width
    reload_value = Ref(_f("RELOAD", "value"))
    count = Ref(_f("COUNT", "value"))

    at_expiry = [
        Assign(Ref(_set("STATUS", "expired")), _one()),
        If(
            _reload_condition(opts),
            then=[Assign(count, reload_value)],
            # One-shot: stop here. COUNT stays at zero, which is what a
            # subsequent read must show — a counter that wrapped to RELOAD
            # would look identical for one tick and then diverge.
            else_=[Assign(Ref("running"), _zero())],
        ),
    ]

    on_tick = [
        Assign(Ref("pre_cnt"), _zero(pw)),
        If(
            _terminal_condition(opts),
            then=at_expiry,
            else_=[Assign(count, BinOp(BinOpKind.SUB, count, _one(cw)))],
        ),
    ]

    return [
        Comment(
            "Set requests are one-cycle pulses: defaulted low here and raised "
            "below, so a later assignment in the same block wins",
            level=CommentLevel.VERBOSE,
        ),
        Assign(Ref(_set("STATUS", "expired")), _zero()),
        If(
            _not(Ref(_f("CTRL", "enable"))),
            then=[
                Comment(
                    "Disabled means reloaded, not paused: enabling always "
                    "starts a full period",
                    level=CommentLevel.VERBOSE,
                ),
                Assign(Ref("pre_cnt"), _zero(pw)),
                Assign(count, reload_value),
                Assign(Ref("running"), _one()),
            ],
            else_=[
                If(
                    Ref("running"),
                    then=[
                        If(
                            _tick_condition(opts),
                            then=on_tick,
                            else_=[
                                Assign(
                                    Ref("pre_cnt"),
                                    BinOp(BinOpKind.ADD, Ref("pre_cnt"), _one(pw)),
                                )
                            ],
                        )
                    ],
                )
            ],
        ),
    ]


def _glue_assignments() -> list[ModuleItem]:
    """Drive the interrupt output from the flag and its mask.

    Level-sensitive on purpose: ``irq`` stays high until software clears
    ``STATUS.expired``, so an interrupt cannot be lost between the controller
    sampling it and the handler running. A pulse would need the receiver to
    latch it, which is the interrupt controller's job, not the timer's.
    """
    return [
        ContAssign(
            Ref("irq"),
            BinOp(
                BinOpKind.LAND,
                Ref(_f("STATUS", "expired")),
                Ref(_f("CTRL", "irq_enable")),
            ),
        )
    ]


def generate(opts: AxilTimerOptions) -> Module:
    """Build the timer IR by splicing the register block into this module."""
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
        Port("irq", OUT, bit(), doc="Interrupt request, level-sensitive"),
    ]

    signals: list[ModuleItem] = [
        Signal("pre_cnt", vec(opts.prescale_width), doc="Prescaler counter"),
        Signal("running", bit(), doc="Counter is armed; cleared by a one-shot expiry"),
    ]

    counter = AlwaysFF(
        clock=ClockSpec(AXI_CLOCK),
        reset=ResetSpec(
            name=AXI_RESET,
            kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
            active_low=True,
        ),
        reset_body=[
            Assign(Ref("pre_cnt"), _zero(opts.prescale_width)),
            Assign(Ref(_f("COUNT", "value")), _zero(opts.counter_width)),
            Assign(Ref("running"), _one()),
            Assign(Ref(_set("STATUS", "expired")), _zero()),
        ],
        body=_counter_body(opts),
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
        items=[*core.items, *signals, counter, *_glue_assignments()],
    )


def _description(opts: AxilTimerOptions) -> str:
    return (
        f"AXI4-Lite timer, {opts.counter_width}-bit counter, "
        f"{opts.prescale_width}-bit prescaler"
    )


# --------------------------------------------------------------------------- #
# Directed testbench
# --------------------------------------------------------------------------- #
#
# Expiry timing, derived from the RTL above rather than observed from a run.
#
# `AxilSequencer.write` drives the CTRL request at cycle c; both channels are
# captured at edge c+1, so the field updates land at edge c+2 and `enable` is
# high from cycle c+2 onwards. Cycle c+1 still sees `enable` low, so that edge
# takes the disabled branch: COUNT <= RELOAD, pre_cnt <= 0, running <= 1. The
# counter therefore starts from a known state at cycle c+2 no matter what came
# before.
#
# From there `pre_cnt` counts 0..P over cycles c+2 .. c+2+P, so tick j is
# evaluated during cycle c+2+P+(j-1)*(P+1). Ticks 1..R decrement COUNT to zero;
# tick R+1 finds zero and expires. Two more clocks are pure composition cost:
# one for the register block to sample the set request, one for the flag to be
# visible.

_TEST_RELOAD = 3
_TEST_PRESCALE = 1


def _irq_cycle(write_cycle: int, reload: int, prescale: int) -> int:
    """Cycle on which ``irq`` rises after a CTRL write at ``write_cycle``."""
    return write_cycle + 4 + prescale + reload * (prescale + 1)


def _period(reload: int, prescale: int) -> int:
    """Clocks between one expiry and the next, in periodic mode."""
    return (reload + 1) * (prescale + 1)


def tb_spec(opts: AxilTimerOptions) -> TbSpec:
    """Run the timer periodically, then once, and pin when ``irq`` rises.

    Every expiry is checked twice: ``irq`` must be low on the cycle *before*
    the derived rise and high on it. The pair is what makes the check
    discriminating — a check for "high at cycle N" alone passes for any timer
    that fired at or before N, so a prescaler that is ignored entirely, or a
    reload value read as one bit too short, would go unnoticed.
    """
    regmap = register_map(opts)
    model = RegisterModel(regmap)
    seq = AxilSequencer()
    full_strb = (1 << (_DATA_WIDTH // 8)) - 1

    reload = min(_TEST_RELOAD, (1 << opts.counter_width) - 1)
    prescale = min(_TEST_PRESCALE, (1 << opts.prescale_width) - 1)

    ctrl = regmap.register("CTRL").offset
    reload_addr = regmap.register("RELOAD").offset
    count_addr = regmap.register("COUNT").offset
    prescale_addr = regmap.register("PRESCALE").offset
    status = regmap.register("STATUS").offset

    enable, auto_reload, irq_enable = 0b001, 0b010, 0b100

    # Cycle 0 — out of reset nothing is asserted and no interrupt is pending.
    seq.expect(0, "bvalid", 0)
    seq.expect(0, "rvalid", 0)
    seq.expect(0, "irq", 0)
    seq.idle()

    # Program the period, then confirm COUNT tracks RELOAD while disabled.
    resp = model.write(prescale_addr, prescale, full_strb)
    seq.write(prescale_addr, prescale, full_strb, resp, [("irq", 0)])
    resp = model.write(reload_addr, reload, full_strb)
    seq.write(reload_addr, reload, full_strb, resp, [("irq", 0)])
    model.drive_ro("COUNT", "value", reload)
    seq.read(count_addr, *model.read(count_addr))

    # --- periodic ---------------------------------------------------------- #
    started = seq.cycle
    value = enable | auto_reload | irq_enable
    resp = model.write(ctrl, value, full_strb)
    seq.write(ctrl, value, full_strb, resp, [("irq", 0)])

    rise = _irq_cycle(started, reload, prescale)
    seq.expect(rise - 1, "irq", 0)
    seq.expect(rise, "irq", 1)
    seq.idle(rise + 1 - seq.cycle)

    model.hardware_set("STATUS", "expired", 1)
    seq.read(status, *model.read(status))

    # Disabling clears the mask too, so irq drops even though the flag is still
    # set — the one check that separates the mask from the flag.
    resp = model.write(ctrl, 0, full_strb)
    seq.write(ctrl, 0, full_strb, resp, [("irq", 0)])

    # Only now clear the flag: the timer is stopped, so nothing can re-set it
    # between the clear and the read that proves it cleared.
    resp = model.write(status, 1, full_strb)
    seq.write(status, 1, full_strb, resp, [("irq", 0)])
    seq.read(status, *model.read(status))

    # --- one-shot ---------------------------------------------------------- #
    started = seq.cycle
    value = enable | irq_enable
    resp = model.write(ctrl, value, full_strb)
    seq.write(ctrl, value, full_strb, resp, [("irq", 0)])

    rise = _irq_cycle(started, reload, prescale)
    seq.expect(rise - 1, "irq", 0)
    seq.expect(rise, "irq", 1)
    seq.idle(rise + 1 - seq.cycle)

    model.hardware_set("STATUS", "expired", 1)
    resp = model.write(status, 1, full_strb)
    seq.write(status, 1, full_strb, resp, [("irq", 0)])

    # Three full periods with nothing happening. A timer that reloaded despite
    # auto_reload being clear would have expired again by now, so this is what
    # makes one-shot mode more than a comment.
    seq.idle(3 * _period(reload, prescale))
    model.drive_ro("COUNT", "value", 0)
    seq.read(count_addr, *model.read(count_addr))
    seq.read(status, *model.read(status))
    seq.expect(seq.cycle - 1, "irq", 0)

    # A write into CTRL's reserved bits is rejected, and leaves the timer alone.
    reserved = 1 << 3
    resp = model.write(ctrl, reserved, full_strb)
    seq.write(ctrl, reserved, full_strb, resp, [("irq", 0)])

    items: list[AssertionItem] = [
        ResetKnownValue(name="bvalid_idle_after_reset", signal="bvalid", value=0, width=1),
        ResetKnownValue(name="rvalid_idle_after_reset", signal="rvalid", value=0, width=1),
        ResetKnownValue(name="irq_idle_after_reset", signal="irq", value=0, width=1),
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


def bundles(opts: AxilTimerOptions) -> list[PortBundle]:  # noqa: ARG001
    """The AXI target port. ``irq`` is a single wire, not a protocol bundle."""
    return [
        PortBundle(
            name="s_axil",
            protocol="axi4-lite",
            role="target",
            clock=AXI_CLOCK,
            reset=AXI_RESET,
            description="AXI4-Lite target serving the timer registers.",
            ports=[BundlePort(signal=sig, role_name=sig) for sig in axil_ports()],
        )
    ]


def port_groups(opts: AxilTimerOptions) -> list[PortGroup]:  # noqa: ARG001
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
            name="Interrupt",
            ports=["irq"],
            description=(
                "Level-sensitive request, high while STATUS.expired is set and "
                "CTRL.irq_enable allows it."
            ),
        ),
    ]


def explain(opts: AxilTimerOptions) -> ExplanationDoc:
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
    signals.append(
        SignalDoc(
            name="irq",
            direction="output",
            description=(
                "Interrupt request; high while STATUS.expired is set and "
                "CTRL.irq_enable is 1. Cleared by writing 1 to STATUS.expired."
            ),
        )
    )

    return ExplanationDoc(
        purpose=(
            f"An AXI4-Lite timer with a {opts.counter_width}-bit down-counter "
            f"and a {opts.prescale_width}-bit prescaler, running one-shot or "
            "periodically and raising a maskable interrupt on expiry. The AXI "
            "frontend is the register-block generator spliced in rather than "
            "instantiated, so the result is one flat module."
        ),
        configuration=[
            f"Counter: {opts.counter_width} bits",
            f"Prescaler: {opts.prescale_width} bits",
            "Period: (RELOAD + 1) * (PRESCALE + 1) clocks",
            f"Registers: {len(regmap.registers)} "
            f"({1 << regmap.addr_width} B decoded, {regmap.span_bytes()} B used)",
            f"Reset: {opts.reset_style}, active-low (fixed by AXI4-Lite)",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The active-low {opts.reset_style} reset clears CTRL, so the timer "
            "comes up disabled with irq low, and clears RELOAD, PRESCALE and "
            "STATUS. COUNT resets to zero and is reloaded from RELOAD on the "
            "first clock, because the counter is held reloaded while disabled."
        ),
        assumptions=[
            "Software programs PRESCALE and RELOAD before setting CTRL.enable; "
            "enabling always starts a full period.",
            "The interrupt is level-sensitive and stays asserted until software "
            "writes 1 to STATUS.expired.",
        ],
        limitations=[
            "No pause and resume: clearing CTRL.enable reloads the counter "
            "rather than freezing it.",
            "No capture or compare channels, and no free-running mode — COUNT "
            "counts down to zero and is not writable.",
            "STATUS.expired does not count missed expiries: a second expiry "
            "before software clears the flag is indistinguishable from the "
            "first.",
            "irq rises two clocks after the counter reaches its terminal count "
            "(one to sample the set request, one for the flag to be readable).",
            "Bits above counter_width are reserved in RELOAD and COUNT, and "
            "bits above 2 in CTRL; writing one returns SLVERR.",
        ],
    )


@dataclass(frozen=True)
class _AxilTimerIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "axil-timer"
    name: str = "AXI4-Lite timer"
    description: str = (
        "AXI4-Lite timer with a prescaled down-counter, one-shot or periodic "
        "operation and a maskable level interrupt; the register frontend is "
        "spliced in from the AXI4-Lite register block generator."
    )
    kind: str = "ip"
    maturity: str = "beta"
    options_model: type[AxilTimerOptions] = AxilTimerOptions

    def generate(self, opts: AxilTimerOptions) -> Module:
        return generate(opts)

    def explain(self, opts: AxilTimerOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: AxilTimerOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: AxilTimerOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: AxilTimerOptions) -> RegisterMap:
        return register_map(opts)

    def bundles(self, opts: AxilTimerOptions) -> list[PortBundle]:
        return bundles(opts)


IP = _AxilTimerIp()

__all__ = [
    "AxilTimerOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "register_map",
    "bundles",
    "IP",
]
