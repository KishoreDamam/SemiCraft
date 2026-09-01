"""A reference ``IpDef`` used to exercise the P4-01 contract end to end.

Deliberately **test-only**, not a catalog item. P4-01 ships the IP *contract*;
the first real IP is P4-02's AXI4-Lite register block, and shipping a
throwaway CSR block in the catalog first would mean golden files and a
datasheet for something P4-02 immediately supersedes.

But a contract with no implementor is exactly the "documented, never
executed" pattern this project keeps finding defects in — a register map
nothing renders, a bundle nothing cross-checks. So the contract is verified
by a real IP that goes through the entire pipeline: IR generation, both
language renderers, the datasheet with its register-map and bus-interface
sections, the smoke testbench, SVA, and (where Verilator exists) a compile
and run.

What it is
----------

A tiny memory-mapped control/status block on a "native-csr" bus — address,
write strobe, write data, read strobe, read data — with two registers::

    0x0  CTRL    enable [0]   RW, reset 1  -> ctrl_enable output
                 mode   [2:1] RW, reset 0  -> ctrl_mode output
    0x4  STATUS  busy   [0]   RO           <- status_busy input

``status_register=False`` drops STATUS and its ``status_busy`` port, so the
register map, the port list and the read decode all shrink together — which
is what makes the option worth having here: it proves ``register_map(opts)``
is genuinely a function of the options, not a constant.

The hardware-side ports (``ctrl_enable``, ``ctrl_mode``, ``status_busy``)
belong to **no** bundle. That is the interesting case for
``check_bundles_against_module``: bundles describe the bus face of an IP, not
every port it has.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field
from semicraft_core.assertions.spec import (
    AssertionItem,
    AssertionSpec,
    ResetContext,
    ResetKnownValue,
)
from semicraft_core.ips.bundles import BundlePort, PortBundle
from semicraft_core.ips.regmap import Register, RegisterField, RegisterMap
from semicraft_core.ir.build import IN, OUT, bit, vec
from semicraft_core.ir.nodes import (
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
    Header,
    If,
    Module,
    Port,
    Ref,
    Repl,
    ResetKind,
    ResetSpec,
    Slice,
)
from semicraft_core.modules.contract import Check, PortGroup, TbSpec
from semicraft_core.snippets.contract import ClockedOptions, ExplanationDoc, SignalDoc
from semicraft_core.version import VERSION

_MODULE_NAME = "csr_block"
_ADDR_WIDTH = 4
_DATA_WIDTH = 32

CTRL_OFFSET = 0x0
STATUS_OFFSET = 0x4


class ReferenceIpOptions(ClockedOptions):
    """Options for the reference CSR block."""

    status_register: bool = Field(
        default=True,
        description=(
            "Include the read-only STATUS register (and its status_busy input). "
            "When false the register map has one register and the read decode "
            "returns zero for offset 0x4."
        ),
    )


# ---------------------------------------------------------------------------
# RTL
# ---------------------------------------------------------------------------


def _addr_const(value: int) -> Const:
    """A sized hex address literal (``4'h4``) — sized so Verilator's width
    checks stay quiet when it is compared against the 4-bit ``addr`` port."""
    return Const(value, width=Const(_ADDR_WIDTH), base=ConstBase.HEX)


def _zeros(n: int) -> Repl:
    """``{n{1'b0}}`` — the reserved high bits of a read-data word."""
    return Repl(Const(n), Const(0, width=Const(1), base=ConstBase.BIN))


def generate(opts: ReferenceIpOptions) -> Module:
    """Build the CSR block IR (pure)."""
    reset = ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )

    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock"),
        Port("rst", IN, bit(), doc="Reset"),
        Port("addr", IN, vec(_ADDR_WIDTH), doc="Byte address within the register map"),
        Port("wr_en", IN, bit(), doc="Write strobe; wdata is captured on the next edge"),
        Port("wdata", IN, vec(_DATA_WIDTH), doc="Write data"),
        Port("rd_en", IN, bit(), doc="Read strobe; rdata is valid the cycle after"),
        Port("rdata", OUT, vec(_DATA_WIDTH), doc="Registered read data"),
        Port("ctrl_enable", OUT, bit(), doc="CTRL.enable field value"),
        Port("ctrl_mode", OUT, vec(2), doc="CTRL.mode field value"),
    ]
    if opts.status_register:
        ports.append(
            Port("status_busy", IN, bit(), doc="Hardware status sampled into STATUS.busy")
        )

    # Write decode: only CTRL is writable, so a single `if` rather than a case
    # (a one-arm case would need a no-op default the IR has no statement for).
    write = If(
        Ref("wr_en"),
        then=[
            If(
                BinOp(BinOpKind.EQ, Ref("addr"), _addr_const(CTRL_OFFSET)),
                then=[
                    Assign(Ref("ctrl_enable"), Bit(Ref("wdata"), Const(0))),
                    Assign(Ref("ctrl_mode"), Slice(Ref("wdata"), Const(2), Const(1))),
                ],
            )
        ],
    )

    ctrl_read = Concat([_zeros(_DATA_WIDTH - 3), Ref("ctrl_mode"), Ref("ctrl_enable")])
    read_items = [CaseItem([_addr_const(CTRL_OFFSET)], [Assign(Ref("rdata"), ctrl_read)])]
    if opts.status_register:
        status_read = Concat([_zeros(_DATA_WIDTH - 1), Ref("status_busy")])
        read_items.append(
            CaseItem([_addr_const(STATUS_OFFSET)], [Assign(Ref("rdata"), status_read)])
        )

    read = If(
        Ref("rd_en"),
        then=[
            Case(
                Ref("addr"),
                items=read_items,
                # Unmapped offsets read as zero — the reserved-reads-zero rule
                # the register-map model documents, made real in the decode.
                default=[Assign(Ref("rdata"), Const(0, width=Const(_DATA_WIDTH)))],
            )
        ],
    )

    always = AlwaysFF(
        clock=ClockSpec("clk"),
        reset=reset,
        reset_body=[
            Assign(Ref("ctrl_enable"), Const(1, width=Const(1))),
            Assign(Ref("ctrl_mode"), Const(0, width=Const(2))),
            Assign(Ref("rdata"), Const(0, width=Const(_DATA_WIDTH))),
        ],
        body=[
            Comment("Write decode: CTRL only", level=CommentLevel.VERBOSE),
            write,
            Comment("Read decode: registered rdata, unmapped reads as zero",
                    level=CommentLevel.VERBOSE),
            read,
        ],
    )

    return Module(
        name=_MODULE_NAME,
        header=Header(
            license="",
            config_hash="",
            tool_version=VERSION,
            description="Reference control/status register block",
        ),
        params=[],
        ports=ports,
        items=[always],
    )


# ---------------------------------------------------------------------------
# IP metadata
# ---------------------------------------------------------------------------


def register_map(opts: ReferenceIpOptions) -> RegisterMap:
    """The software-visible layout; STATUS is present only when configured."""
    registers = [
        Register(
            name="CTRL",
            offset=CTRL_OFFSET,
            description="Control register.",
            fields=[
                RegisterField(
                    name="enable",
                    lsb=0,
                    width=1,
                    access="rw",
                    reset=1,
                    description="Drives the ctrl_enable output; set out of reset.",
                ),
                RegisterField(
                    name="mode",
                    lsb=1,
                    width=2,
                    access="rw",
                    reset=0,
                    description="Drives the 2-bit ctrl_mode output.",
                ),
            ],
        )
    ]
    if opts.status_register:
        registers.append(
            Register(
                name="STATUS",
                offset=STATUS_OFFSET,
                description="Status register (read-only).",
                fields=[
                    RegisterField(
                        name="busy",
                        lsb=0,
                        width=1,
                        access="ro",
                        description="Reflects the status_busy input.",
                    )
                ],
            )
        )
    return RegisterMap(
        name="CSR",
        data_width=_DATA_WIDTH,
        addr_width=_ADDR_WIDTH,
        registers=registers,
    )


def bundles(opts: ReferenceIpOptions) -> list[PortBundle]:  # noqa: ARG001 - fixed bus
    """The single bus-side bundle.

    ``ctrl_enable``/``ctrl_mode``/``status_busy`` are intentionally absent: they
    are the hardware face of the IP, not part of any protocol.
    """
    return [
        PortBundle(
            name="s_csr",
            protocol="native-csr",
            role="target",
            clock="clk",
            reset="rst",
            description="Single-cycle register access port.",
            ports=[
                BundlePort(signal="addr", role_name="addr"),
                BundlePort(signal="wr_en", role_name="wr_en"),
                BundlePort(signal="wdata", role_name="wdata"),
                BundlePort(signal="rd_en", role_name="rd_en"),
                BundlePort(signal="rdata", role_name="rdata"),
            ],
        )
    ]


def port_groups(opts: ReferenceIpOptions) -> list[PortGroup]:
    """Datasheet grouping: clocking, the bus, and the hardware face."""
    reset_name = "rst" + ("_n" if opts.reset_polarity == "active_low" else "")
    hardware = ["ctrl_enable", "ctrl_mode"]
    if opts.status_register:
        hardware.append("status_busy")
    return [
        PortGroup(
            name="Clocking",
            ports=["clk", reset_name],
            description="Single clock domain; all registers reset together.",
        ),
        PortGroup(
            name="Register bus",
            ports=["addr", "wr_en", "wdata", "rd_en", "rdata"],
            description="Native single-cycle CSR access port (bundle `s_csr`).",
        ),
        PortGroup(
            name="Hardware face",
            ports=hardware,
            description="Field values driven to, and status sampled from, the design.",
        ),
    ]


# ---------------------------------------------------------------------------
# Smoke-TB recipe
# ---------------------------------------------------------------------------


def tb_spec(opts: ReferenceIpOptions) -> TbSpec:
    """Write CTRL, read it back, read STATUS, then read an unmapped offset.

    Cycle indices follow TB_SPEC §6a: a vector driven at cycle ``c`` is sampled
    by the rising edge between cycle ``c`` and cycle ``c+1``, so every check
    below sits one cycle after the stimulus that causes it. The expected values
    are derived from the decode above, never read back out of a simulation.
    """
    vectors: list[dict[str, int]] = [
        {"rd_en": 1, "addr": CTRL_OFFSET},          # c0: start a CTRL read
        {"wr_en": 1, "rd_en": 0, "wdata": 0b100},   # c1: write mode=2, enable=0
        {"wr_en": 0, "rd_en": 1},                   # c2: read CTRL back
        {"addr": STATUS_OFFSET},                    # c3: read STATUS
        {"addr": 0x8},                              # c4: read an unmapped offset
        {"rd_en": 0},                               # c5: idle
    ]
    if opts.status_register:
        vectors[3] = {**vectors[3], "status_busy": 1}

    # STATUS.busy reads 1 when the register exists; without it 0x4 is unmapped
    # and the default arm returns zero.
    status_read = 1 if opts.status_register else 0

    checks = [
        # c0: nothing has clocked yet — reset values.
        Check(cycle=0, signal="rdata", expected=0),
        Check(cycle=0, signal="ctrl_enable", expected=1),
        Check(cycle=0, signal="ctrl_mode", expected=0),
        # c1: the c0 read landed: {mode=0, enable=1} == 0x1.
        Check(cycle=1, signal="rdata", expected=0b001),
        # c2: the c1 write landed.
        Check(cycle=2, signal="ctrl_enable", expected=0),
        Check(cycle=2, signal="ctrl_mode", expected=2),
        # c3: the c2 read-back landed: {mode=2, enable=0} == 0x4.
        Check(cycle=3, signal="rdata", expected=0b100),
        # c4: the c3 STATUS read landed.
        Check(cycle=4, signal="rdata", expected=status_read),
        # c5: the c4 unmapped read landed — default arm, zero.
        Check(cycle=5, signal="rdata", expected=0),
    ]

    items: list[AssertionItem] = [
        ResetKnownValue(name="rdata_reset_value", signal="rdata", value=0, width=_DATA_WIDTH),
        ResetKnownValue(name="ctrl_enable_reset_value", signal="ctrl_enable", value=1, width=1),
        ResetKnownValue(name="ctrl_mode_reset_value", signal="ctrl_mode", value=0, width=2),
    ]

    return TbSpec(
        clock="clk",
        reset="rst",
        reset_cycles=2,
        vectors=vectors,
        checks=checks,
        assertion_spec=AssertionSpec(
            clock="clk",
            items=items,
            reset=ResetContext(
                signal="rst",
                active_low=opts.reset_polarity == "active_low",
                sync=opts.reset_style == "sync",
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


def explain(opts: ReferenceIpOptions) -> ExplanationDoc:
    reset_name = "rst" + ("_n" if opts.reset_polarity == "active_low" else "")
    signals = [
        SignalDoc(name="clk", direction="input", description="Clock."),
        SignalDoc(name=reset_name, direction="input", description="Reset."),
        SignalDoc(name="addr", direction="input", description="Byte address."),
        SignalDoc(name="wr_en", direction="input", description="Write strobe."),
        SignalDoc(name="wdata", direction="input", description="Write data."),
        SignalDoc(name="rd_en", direction="input", description="Read strobe."),
        SignalDoc(name="rdata", direction="output", description="Registered read data."),
        SignalDoc(
            name="ctrl_enable", direction="output", description="CTRL.enable field value."
        ),
        SignalDoc(name="ctrl_mode", direction="output", description="CTRL.mode field value."),
    ]
    if opts.status_register:
        signals.append(
            SignalDoc(
                name="status_busy",
                direction="input",
                description="Sampled into STATUS.busy on a read.",
            )
        )
    return ExplanationDoc(
        purpose=(
            "A minimal memory-mapped control/status register block, used as the "
            "reference implementation of the P4-01 IpDef contract."
        ),
        configuration=[
            f"Data width: {_DATA_WIDTH} bits",
            f"Address width: {_ADDR_WIDTH} bits ({1 << _ADDR_WIDTH} B decoded)",
            f"STATUS register: {'yes' if opts.status_register else 'no'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The {'active-low' if opts.reset_polarity == 'active_low' else 'active-high'} "
            f"{opts.reset_style} reset restores CTRL to its reset value "
            f"(enable=1, mode=0) and clears rdata to zero."
        ),
        assumptions=[
            "Single clock domain; the bus and the hardware face share clk.",
            "Reads are registered: rdata is valid the cycle after rd_en.",
        ],
        limitations=[
            "No byte strobes: a write updates every writable field of the register.",
            "No bus error response for unmapped offsets — they read as zero.",
        ],
    )


# ---------------------------------------------------------------------------
# IpDef instance
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ReferenceIp:
    """Satisfies :class:`semicraft_core.ips.contract.IpDef` structurally."""

    id: str = "reference-csr"
    name: str = "Reference CSR Block"
    description: str = "Reference IP exercising the P4-01 IpDef contract."
    kind: str = "ip"
    maturity: str = "beta"
    options_model: type[ReferenceIpOptions] = ReferenceIpOptions

    def generate(self, opts: ReferenceIpOptions) -> Module:
        return generate(opts)

    def explain(self, opts: ReferenceIpOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: ReferenceIpOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: ReferenceIpOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: ReferenceIpOptions) -> RegisterMap:
        return register_map(opts)

    def bundles(self, opts: ReferenceIpOptions) -> list[PortBundle]:
        return bundles(opts)


REFERENCE_IP = _ReferenceIp()

__all__ = [
    "ReferenceIpOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "register_map",
    "bundles",
    "REFERENCE_IP",
    "CTRL_OFFSET",
    "STATUS_OFFSET",
]
