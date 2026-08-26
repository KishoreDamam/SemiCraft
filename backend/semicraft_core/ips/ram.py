"""Synchronous RAM IP (Phase-4 P4-04).

Single-port or simple-dual-port synchronous RAM over the IR ``Memory`` node
(IR_SPEC §10.2), which the synchronous FIFO first proved out in P4-03a.

No reset — deliberately
-----------------------

The module has **no reset port at all**, so it extends ``CommonOptions``
rather than ``ClockedOptions``. Storage must not be reset (clearing a deep
memory costs a great deal of logic for no observable behaviour), and resetting
only the output register is what most commonly blocks block-RAM inference in
FPGA synthesis. A RAM with a bare clock is the shape every vendor's inference
template expects.

The consequence is that ``dout`` holds no defined value until the first
completed read, which is why the generated testbench never checks it before
one. That is real behaviour, stated in the datasheet, not an omission.

Read-during-write returns OLD data
----------------------------------

Both the write and the read are non-blocking assignments in one clocked
process::

    if (we) mem[waddr] <= din;
    if (re) dout <= mem[raddr];

so a read of the address being written in the same cycle sees the value that
was already there — READ_FIRST / read-before-write semantics. This is the one
behaviour of a RAM that is easy to get wrong and impossible to guess from the
port list, so the testbench pins it with a directed check rather than leaving
it to the reader.

Depth is a power of two
-----------------------

The address port is ``$clog2(depth)`` bits. A non-power-of-two depth would
leave part of the address space undecoded, and reads from it would return
simulator-dependent values (X in a four-state simulator, zero in Verilator) —
untestable behaviour that would differ between the sim the user runs and the
one this project's gate runs. Rejected at validation instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

from ..ir.build import IN, OUT, bit, mem, vec
from ..ir.nodes import (
    AlwaysFF,
    Assign,
    Bit,
    ClockSpec,
    Comment,
    CommentLevel,
    Header,
    If,
    Module,
    ModuleItem,
    Port,
    Ref,
)
from ..modules.contract import Check, PortGroup, TbSpec
from ..snippets.contract import CommonOptions, ExplanationDoc, SignalDoc
from ..version import VERSION
from .bundles import BundlePort, PortBundle
from .regmap import RegisterMap

_MODULE_NAME = "sync_ram"


# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #


class RamOptions(CommonOptions):
    """Configuration for the synchronous RAM.

    Extends :class:`CommonOptions`, not ``ClockedOptions``: this module has no
    reset (see the module docstring), so reset style and polarity would be
    options with nothing to configure.
    """

    width: int = Field(default=8, ge=1, le=64, description="Data width in bits.")
    depth: int = Field(
        default=256,
        ge=2,
        le=65536,
        description=(
            "Number of words; must be a power of two so the whole address "
            "space decodes to real storage."
        ),
    )
    port_mode: Literal["single", "simple_dual"] = Field(
        default="single",
        description=(
            "'single' shares one address between the write and read ports; "
            "'simple_dual' gives the write and read ports independent "
            "addresses (one write port, one read port, one clock)."
        ),
    )
    read_enable: bool = Field(
        default=True,
        description=(
            "Gate the read with an `re` input. When false the output register "
            "reloads every cycle and there is no `re` port."
        ),
    )

    @model_validator(mode="after")
    def _depth_is_a_power_of_two(self) -> RamOptions:
        if self.depth & (self.depth - 1):
            raise ValueError(
                f"depth must be a power of two, got {self.depth}; the nearest "
                f"legal values are {1 << (self.depth.bit_length() - 1)} and "
                f"{1 << self.depth.bit_length()}"
            )
        return self

    @property
    def addr_bits(self) -> int:
        """Bits in the address port ($clog2(depth))."""
        return (self.depth - 1).bit_length()

    @property
    def write_addr(self) -> str:
        return "addr" if self.port_mode == "single" else "waddr"

    @property
    def read_addr(self) -> str:
        return "addr" if self.port_mode == "single" else "raddr"


# --------------------------------------------------------------------------- #
# RTL
# --------------------------------------------------------------------------- #


def _write_stmt(opts: RamOptions):
    """``if (we) mem[<write addr>] <= din;``"""
    return If(
        Ref("we"),
        then=[Assign(Bit(Ref("mem"), Ref(opts.write_addr)), Ref("din"))],
    )


def _read_stmt(opts: RamOptions):
    """``dout <= mem[<read addr>]``, gated by ``re`` when that port exists."""
    load = Assign(Ref("dout"), Bit(Ref("mem"), Ref(opts.read_addr)))
    if not opts.read_enable:
        return load
    return If(Ref("re"), then=[load])


def generate(opts: RamOptions) -> Module:
    """Build the RAM IR (pure)."""
    aw = opts.addr_bits
    ports: list[Port] = [Port("clk", IN, bit(), doc="Clock; the only timing input")]

    if opts.port_mode == "single":
        ports.append(
            Port("addr", IN, vec(aw), doc="Shared read/write address")
        )
    else:
        ports.append(Port("waddr", IN, vec(aw), doc="Write address"))
    ports.append(Port("we", IN, bit(), doc="Write enable"))
    ports.append(Port("din", IN, vec(opts.width), doc="Write data"))
    if opts.port_mode == "simple_dual":
        ports.append(Port("raddr", IN, vec(aw), doc="Read address"))
    if opts.read_enable:
        ports.append(Port("re", IN, bit(), doc="Read enable; dout holds when low"))
    ports.append(
        Port("dout", OUT, vec(opts.width), doc="Registered read data, valid the next cycle")
    )

    items: list[ModuleItem] = [
        mem("mem", opts.width, opts.depth, doc="Storage array; never reset"),
        AlwaysFF(
            clock=ClockSpec("clk"),
            reset=None,  # see the module docstring: no reset, by design
            reset_body=[],
            body=[
                Comment(
                    "Write and read are both non-blocking, so a same-address "
                    "read-during-write returns the OLD contents",
                    level=CommentLevel.VERBOSE,
                ),
                _write_stmt(opts),
                _read_stmt(opts),
            ],
        ),
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
        items=items,
    )


def _description(opts: RamOptions) -> str:
    mode = "single-port" if opts.port_mode == "single" else "simple dual-port"
    return f"{opts.depth} x {opts.width}-bit {mode} synchronous RAM"


# --------------------------------------------------------------------------- #
# Directed testbench
# --------------------------------------------------------------------------- #


class _Sequencer:
    """Vectors + checks; a vector driven at cycle ``c`` lands at edge ``c+1``."""

    def __init__(self) -> None:
        self.vectors: list[dict[str, int]] = []
        self.checks: list[Check] = []
        self.cycle = 0

    def drive(self, **signals: int) -> None:
        while len(self.vectors) <= self.cycle:
            self.vectors.append({})
        self.vectors[self.cycle].update(signals)

    def expect(self, signal: str, value: int) -> None:
        self.checks.append(Check(cycle=self.cycle, signal=signal, expected=value))

    def advance(self, cycles: int = 1) -> None:
        self.cycle += cycles
        while len(self.vectors) <= self.cycle:
            self.vectors.append({})


def _addr_drives(opts: RamOptions, *, write: int | None = None, read: int | None = None) -> dict:
    """Address drives for whichever address ports this configuration has."""
    if opts.port_mode == "single":
        value = write if write is not None else read
        return {} if value is None else {"addr": value}
    out: dict[str, int] = {}
    if write is not None:
        out["waddr"] = write
    if read is not None:
        out["raddr"] = read
    return out


def _test_addresses(opts: RamOptions) -> list[int]:
    """Low, next, and the top of the array — deduplicated for a tiny depth.

    A depth-2 RAM has only addresses 0 and 1, so a fixed three-address plan
    would write two different values to the same location and then check for
    the first one.
    """
    return sorted({0, 1, opts.depth - 1})


def tb_spec(opts: RamOptions) -> TbSpec:
    """Write distinct words, read them back, then prove read-before-write.

    ``dout`` is never checked before the first completed read: the RAM has no
    reset, so until then it holds whatever the simulator initialised it to —
    X in a four-state simulator, zero in Verilator. Checking it would encode
    one simulator's convention as a requirement.
    """
    mask = (1 << opts.width) - 1
    addrs = _test_addresses(opts)
    values = [((i + 1) * 0x11) & mask for i in range(len(addrs))]
    # Guaranteed different from values[0] at any width, so the rewrite check
    # cannot pass against a RAM that ignored it.
    rewritten = values[0] ^ mask

    seq = _Sequencer()
    read_gate = {"re": 1} if opts.read_enable else {}
    read_off = {"re": 0} if opts.read_enable else {}

    # Phase 1 — fill the chosen addresses.
    for addr, value in zip(addrs, values, strict=True):
        seq.drive(we=1, din=value, **_addr_drives(opts, write=addr), **read_off)
        seq.advance()

    # Phase 2 — read them back in order. The read issued at cycle c is
    # observable at c+1, so each check trails its address by one cycle.
    seq.drive(we=0, **_addr_drives(opts, read=addrs[0]), **read_gate)
    seq.advance()
    for i, value in enumerate(values):
        seq.expect("dout", value)
        if i + 1 < len(addrs):
            seq.drive(**_addr_drives(opts, read=addrs[i + 1]))
        seq.advance()

    # Phase 3 — read and write the same address in the same cycle. Both are
    # non-blocking, so the read must return the OLD contents.
    seq.drive(
        we=1,
        din=rewritten,
        **_addr_drives(opts, write=addrs[0], read=addrs[0]),
        **read_gate,
    )
    seq.advance()
    seq.expect("dout", values[0])  # old data, not `rewritten`
    seq.drive(we=0, **_addr_drives(opts, read=addrs[0]), **read_gate)
    seq.advance()
    seq.expect("dout", rewritten)  # ...and the write did land

    # Phase 4 — with the read gated off, dout must hold rather than reload.
    if opts.read_enable:
        seq.drive(**_addr_drives(opts, read=addrs[-1]), re=0)
        seq.advance()
        seq.expect("dout", rewritten)
    seq.advance()

    # No assertion_spec: with no reset there is no reset-value property to
    # assert, and every other property of a RAM is data-dependent — which is
    # exactly what the directed checks above cover. Attaching a property that
    # merely usually holds would be worse than attaching none (same reasoning
    # as pwm, P3-05b).
    return TbSpec(
        clock="clk",
        reset=None,
        reset_cycles=0,
        vectors=seq.vectors,
        checks=seq.checks,
    )


# --------------------------------------------------------------------------- #
# IP metadata
# --------------------------------------------------------------------------- #


def register_map(opts: RamOptions) -> RegisterMap | None:  # noqa: ARG001
    """None — a RAM has no software-visible control registers."""
    return None


def bundles(opts: RamOptions) -> list[PortBundle]:
    """One bundle per physical port, which depends on ``port_mode``.

    Single-port mode shares one address between reads and writes, so it is one
    bundle: a port may belong to at most one bundle, and splitting it would
    have to put ``addr`` in two.
    """
    if opts.port_mode == "single":
        ports = [
            BundlePort(signal="addr", role_name="addr"),
            BundlePort(signal="we", role_name="we"),
            BundlePort(signal="din", role_name="wdata"),
            BundlePort(signal="dout", role_name="rdata"),
        ]
        if opts.read_enable:
            ports.insert(3, BundlePort(signal="re", role_name="re"))
        return [
            PortBundle(
                name="mem",
                protocol="sram-single",
                role="target",
                clock="clk",
                description="Shared-address memory port.",
                ports=ports,
            )
        ]

    read_ports = [BundlePort(signal="raddr", role_name="addr")]
    if opts.read_enable:
        read_ports.append(BundlePort(signal="re", role_name="re"))
    read_ports.append(BundlePort(signal="dout", role_name="rdata"))
    return [
        PortBundle(
            name="wr",
            protocol="sram-write",
            role="target",
            clock="clk",
            description="Write port.",
            ports=[
                BundlePort(signal="waddr", role_name="addr"),
                BundlePort(signal="we", role_name="we"),
                BundlePort(signal="din", role_name="wdata"),
            ],
        ),
        PortBundle(
            name="rd",
            protocol="sram-read",
            role="target",
            clock="clk",
            description="Read port.",
            ports=read_ports,
        ),
    ]


def port_groups(opts: RamOptions) -> list[PortGroup]:
    write_ports = [opts.write_addr, "we", "din"]
    read_ports = [] if opts.port_mode == "single" else ["raddr"]
    if opts.read_enable:
        read_ports.append("re")
    read_ports.append("dout")
    return [
        PortGroup(
            name="Clocking",
            ports=["clk"],
            description="Single clock; the RAM has no reset (see Limitations).",
        ),
        PortGroup(
            name="Write port",
            ports=write_ports,
            description="Write address, enable and data.",
        ),
        PortGroup(
            name="Read port",
            ports=read_ports,
            description=(
                "Registered read; shares the write address in single-port mode."
            ),
        ),
    ]


def explain(opts: RamOptions) -> ExplanationDoc:
    aw = opts.addr_bits
    dual = opts.port_mode == "simple_dual"
    signals = [SignalDoc(name="clk", direction="input", description="Clock.")]
    if dual:
        signals.append(
            SignalDoc(name="waddr", direction="input", description=f"Write address ({aw} bits).")
        )
    else:
        signals.append(
            SignalDoc(
                name="addr",
                direction="input",
                description=f"Shared read/write address ({aw} bits).",
            )
        )
    signals.append(SignalDoc(name="we", direction="input", description="Write enable."))
    signals.append(SignalDoc(name="din", direction="input", description="Write data."))
    if dual:
        signals.append(
            SignalDoc(name="raddr", direction="input", description=f"Read address ({aw} bits).")
        )
    if opts.read_enable:
        signals.append(
            SignalDoc(
                name="re",
                direction="input",
                description="Read enable; dout holds its value while low.",
            )
        )
    signals.append(
        SignalDoc(
            name="dout",
            direction="output",
            description="Registered read data, valid the cycle after the read.",
        )
    )
    signals.append(
        SignalDoc(
            name="mem",
            direction="internal",
            description=f"Storage array, {opts.depth} x {opts.width} bits; never reset.",
        )
    )

    return ExplanationDoc(
        purpose=(
            f"A {opts.depth}-word by {opts.width}-bit synchronous RAM in "
            f"{'simple dual-port' if dual else 'single-port'} configuration. "
            "Reads are registered, and a read of the address being written in "
            "the same cycle returns the previous contents."
        ),
        configuration=[
            f"Width: {opts.width} bits",
            f"Depth: {opts.depth} words (power of two; {aw}-bit address)",
            f"Port mode: {'simple dual-port' if dual else 'single-port'}",
            f"Read enable: {'yes' if opts.read_enable else 'no (dout reloads every cycle)'}",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            "There is no reset. Storage must not be cleared, and resetting only "
            "the output register is what most often blocks block-RAM inference, "
            "so the module has a bare clock. dout therefore holds no defined "
            "value until the first completed read."
        ),
        assumptions=[
            "One clock drives both ports; this is not a dual-clock memory.",
            "Depth is a power of two, so every address decodes to real storage.",
            "The consumer treats dout as valid one cycle after the read it "
            "issued, not in the same cycle.",
        ],
        limitations=[
            "Read-during-write at the same address returns the OLD contents "
            "(READ_FIRST). If write-first behaviour is wanted, the reader must "
            "bypass the write data externally.",
            "No reset, so dout is undefined until the first read completes — "
            "X in a four-state simulator, zero in Verilator.",
            "No byte write enables: a write updates the whole word.",
            "True dual-port (two independent read/write ports, or two clocks) "
            "is not offered; simple dual-port means one write and one read port "
            "on a single clock.",
            "No initialisation: the array powers up undefined. A ROM with "
            "defined contents needs memory initialisation, which the IR does "
            "not yet express.",
        ],
    )


@dataclass(frozen=True)
class _RamIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "sync-ram"
    name: str = "Synchronous RAM"
    description: str = (
        "Single-port or simple dual-port synchronous RAM with registered reads "
        "and read-before-write semantics; no reset, for block-RAM inference."
    )
    kind: str = "ip"
    maturity: str = "stable"
    options_model: type[RamOptions] = RamOptions

    def generate(self, opts: RamOptions) -> Module:
        return generate(opts)

    def explain(self, opts: RamOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: RamOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: RamOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: RamOptions) -> RegisterMap | None:
        return register_map(opts)

    def bundles(self, opts: RamOptions) -> list[PortBundle]:
        return bundles(opts)


IP = _RamIp()

__all__ = [
    "RamOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "register_map",
    "bundles",
    "IP",
]
