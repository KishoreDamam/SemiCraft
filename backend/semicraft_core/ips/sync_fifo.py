"""Synchronous FIFO IP (Phase-4 P4-03a).

A single-clock FIFO over an unpacked-array memory. Two things make it a
useful second IP beyond "the catalog needs a FIFO":

1. It is the **first consumer of the IR ``Memory`` node**. That node has been
   spec'd (IR_SPEC §10.2) and unit-tested since IR v0.2 but no generator ever
   emitted one, so the whole render path for it was untried in a real module.
2. It exercises the two ``IpDef`` branches the AXI register block did not:
   ``register_map`` returning ``None`` (an IP with no software-visible
   registers), and **two bundles sharing one clock** — which is the case the
   "clocks are referenced, not owned" rule in ``bundles.py`` exists for.

Pointer scheme
--------------

Depth is a power of two and the read/write pointers carry one **extra**
most-significant bit, so full and empty are distinguishable without a separate
counter:

    empty = wptr == rptr                       (all bits equal)
    full  = wptr[AW] != rptr[AW] && wptr[AW-1:0] == rptr[AW-1:0]
    count = wptr - rptr                        (exact, 0..DEPTH)

The wrap bit is what makes ``count`` correct across a wrap without any
saturating logic: two's-complement subtraction on ``AW+1`` bits yields the
true occupancy for every reachable pointer pair.

Read timing
-----------

Reads are **registered**: ``rd_data`` presents the popped word on the cycle
*after* ``rd_en`` is accepted. This is the plain (non-first-word-fall-through)
FIFO. FWFT is a different read contract, not an option flag — mixing them
behind a boolean is how a FIFO ends up with a datasheet that describes neither
mode exactly. It is listed as a limitation.

Overflow and underflow are ignored, not flagged: a write while ``full`` and a
read while ``empty`` leave the FIFO untouched. There is no error output, and
the testbench pins that behaviour in both directions.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field, model_validator

from ..assertions.spec import (
    AssertionItem,
    AssertionSpec,
    ResetContext,
    ResetKnownValue,
)
from ..ir.build import IN, OUT, bit, mem, vec
from ..ir.nodes import (
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    Bit,
    ClockSpec,
    Comment,
    CommentLevel,
    Const,
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
from ..modules.contract import Check, PortGroup, TbSpec
from ..snippets.contract import ClockedOptions, ExplanationDoc, SignalDoc
from ..version import VERSION
from .bundles import BundlePort, PortBundle
from .regmap import RegisterMap

_MODULE_NAME = "sync_fifo"


# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #


class SyncFifoOptions(ClockedOptions):
    """Configuration for the synchronous FIFO."""

    width: int = Field(
        default=8, ge=1, le=64, description="Data width in bits."
    )
    depth: int = Field(
        default=8,
        ge=2,
        le=4096,
        description=(
            "Number of entries; must be a power of two so the wrap-bit pointer "
            "scheme gives exact full/empty/count without extra logic."
        ),
    )
    count_output: bool = Field(
        default=True,
        description="Expose a `count` output carrying the current occupancy.",
    )

    @model_validator(mode="after")
    def _depth_is_a_power_of_two(self) -> SyncFifoOptions:
        if self.depth & (self.depth - 1):
            raise ValueError(
                f"depth must be a power of two, got {self.depth}; the nearest "
                f"legal values are {1 << (self.depth.bit_length() - 1)} and "
                f"{1 << self.depth.bit_length()}"
            )
        return self

    @property
    def addr_bits(self) -> int:
        """Bits needed to index the memory ($clog2(depth))."""
        return (self.depth - 1).bit_length()


# --------------------------------------------------------------------------- #
# RTL
# --------------------------------------------------------------------------- #


def _index(pointer: str, addr_bits: int):
    """The memory-index part of a pointer: everything below the wrap bit."""
    return Slice(Ref(pointer), Const(addr_bits - 1), Const(0))


def _empty_expr():
    """``wptr == rptr`` — equal pointers *including* the wrap bit."""
    return BinOp(BinOpKind.EQ, Ref("wptr"), Ref("rptr"))


def _full_expr(addr_bits: int):
    """``wptr[AW] != rptr[AW] && wptr[AW-1:0] == rptr[AW-1:0]``.

    The wrap bit is what separates full from empty: equal pointers with equal
    wrap bits mean empty; equal *indices* with differing wrap bits mean the
    writer has lapped the reader exactly once, i.e. full.
    """
    wrap_differs = BinOp(
        BinOpKind.NE,
        Bit(Ref("wptr"), Const(addr_bits)),
        Bit(Ref("rptr"), Const(addr_bits)),
    )
    index_equal = BinOp(BinOpKind.EQ, _index("wptr", addr_bits), _index("rptr", addr_bits))
    return BinOp(BinOpKind.LAND, wrap_differs, index_equal)


def generate(opts: SyncFifoOptions) -> Module:
    """Build the FIFO IR (pure)."""
    aw = opts.addr_bits
    ptr_type = vec(aw + 1)

    ports: list[Port] = [
        Port("clk", IN, bit(), doc="Clock; both ports are synchronous to it"),
        Port("rst", IN, bit(), doc=_reset_doc(opts)),
        Port("wr_en", IN, bit(), doc="Write enable; ignored while full"),
        Port("wr_data", IN, vec(opts.width), doc="Write data"),
        Port("full", OUT, bit(), doc="No space remains; writes are ignored"),
        Port("rd_en", IN, bit(), doc="Read enable; ignored while empty"),
        Port("rd_data", OUT, vec(opts.width), doc="Read data, valid the cycle after rd_en"),
        Port("empty", OUT, bit(), doc="No entries remain; reads are ignored"),
    ]
    if opts.count_output:
        ports.append(
            Port("count", OUT, vec(aw + 1), doc=f"Current occupancy, 0..{opts.depth}")
        )

    items: list[ModuleItem] = [
        mem("mem", opts.width, opts.depth, doc="Storage array"),
        Signal("wptr", ptr_type, doc="Write pointer with wrap bit"),
        Signal("rptr", ptr_type, doc="Read pointer with wrap bit"),
        ContAssign(Ref("empty"), _empty_expr()),
        ContAssign(Ref("full"), _full_expr(aw)),
    ]
    if opts.count_output:
        items.append(
            ContAssign(Ref("count"), BinOp(BinOpKind.SUB, Ref("wptr"), Ref("rptr")))
        )

    body: list = [
        Comment("Accept a write unless full; the wrap bit advances naturally",
                level=CommentLevel.VERBOSE),
        If(
            BinOp(BinOpKind.LAND, Ref("wr_en"), _not(Ref("full"))),
            then=[
                Assign(Bit(Ref("mem"), _index("wptr", aw)), Ref("wr_data")),
                Assign(Ref("wptr"), BinOp(BinOpKind.ADD, Ref("wptr"), Const(1))),
            ],
        ),
        Comment("Accept a read unless empty; rd_data is registered",
                level=CommentLevel.VERBOSE),
        If(
            BinOp(BinOpKind.LAND, Ref("rd_en"), _not(Ref("empty"))),
            then=[
                Assign(Ref("rd_data"), Bit(Ref("mem"), _index("rptr", aw))),
                Assign(Ref("rptr"), BinOp(BinOpKind.ADD, Ref("rptr"), Const(1))),
            ],
        ),
    ]

    items.append(
        AlwaysFF(
            clock=ClockSpec("clk"),
            reset=_reset_spec(opts),
            reset_body=[
                Assign(Ref("wptr"), Const(0, width=Const(aw + 1))),
                Assign(Ref("rptr"), Const(0, width=Const(aw + 1))),
                Assign(Ref("rd_data"), Const(0, width=Const(opts.width))),
            ],
            body=body,
        )
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
        items=items,
    )


def _not(expr):
    return UnaryOp(UnaryOpKind.NOT_LOGICAL, expr)


def _reset_spec(opts: SyncFifoOptions) -> ResetSpec:
    return ResetSpec(
        name="rst",
        kind=ResetKind.SYNC if opts.reset_style == "sync" else ResetKind.ASYNC,
        active_low=opts.reset_polarity == "active_low",
    )


def _reset_doc(opts: SyncFifoOptions) -> str:
    style = "Async" if opts.reset_style == "async" else "Sync"
    pol = "low" if opts.reset_polarity == "active_low" else "high"
    return f"{style} reset, active-{pol}; empties the FIFO"


def _description(opts: SyncFifoOptions) -> str:
    return f"{opts.depth}-entry x {opts.width}-bit synchronous FIFO"


# --------------------------------------------------------------------------- #
# Reference model + directed testbench
# --------------------------------------------------------------------------- #


class _FifoModel:
    """A Python FIFO with the same accept/ignore rules as the RTL.

    Expected values are derived from this, never read back out of a
    simulation — the discipline recorded in PROGRESS.md after a module's
    checks were once fitted to a buggy sim and froze the bug in as truth.
    """

    def __init__(self, depth: int, width: int) -> None:
        self.depth = depth
        self.mask = (1 << width) - 1
        self.items: list[int] = []
        self.rd_data = 0

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def full(self) -> int:
        return int(len(self.items) == self.depth)

    @property
    def empty(self) -> int:
        return int(not self.items)

    def push(self, value: int) -> None:
        """A write while full is ignored — no error, no overwrite."""
        if not self.full:
            self.items.append(value & self.mask)

    def pop(self) -> None:
        """A read while empty is ignored, and leaves ``rd_data`` unchanged."""
        if self.items:
            self.rd_data = self.items.pop(0)


class _Sequencer:
    """Vectors + checks with the cycle arithmetic in one place.

    A driven vector at cycle ``c`` is applied by the edge into ``c+1``, so
    every expectation sits one cycle after the stimulus that causes it.
    Cycles with neither drives nor checks are left empty on purpose:
    ``generate_tb`` coalesces runs of them into a single ``repeat (N)``, which
    is what keeps a 4096-deep FIFO's testbench a few hundred lines instead of
    tens of thousands.
    """

    def __init__(self) -> None:
        self.vectors: list[dict[str, int]] = []
        self.checks: list[Check] = []
        self.cycle = 0

    def drive(self, **signals: int) -> None:
        while len(self.vectors) <= self.cycle:
            self.vectors.append({})
        self.vectors[self.cycle].update(signals)

    def expect(self, signal: str, value: int, *, at: int | None = None) -> None:
        self.checks.append(
            Check(cycle=self.cycle if at is None else at, signal=signal, expected=value)
        )

    def advance(self, cycles: int = 1) -> None:
        self.cycle += cycles
        while len(self.vectors) <= self.cycle:
            self.vectors.append({})


def _state_checks(seq: _Sequencer, model: _FifoModel, opts: SyncFifoOptions) -> None:
    seq.expect("empty", model.empty)
    seq.expect("full", model.full)
    if opts.count_output:
        seq.expect("count", model.count)


def tb_spec(opts: SyncFifoOptions) -> TbSpec:
    """Ordered readback, fill to full, overflow, drain, underflow.

    Every phase is compact at any depth: the fill and drain hold their enable
    for one driven cycle and then idle, so the vector table stays a handful of
    entries whether the FIFO holds 2 words or 4096.
    """
    mask = (1 << opts.width) - 1
    model = _FifoModel(opts.depth, opts.width)
    seq = _Sequencer()

    # Distinct, non-zero payloads so a readback check cannot pass against a
    # FIFO that returns its reset value. Capped by the width so they stay
    # distinct on a narrow bus.
    n_ordered = min(opts.depth, 4, mask)
    values = [i + 1 for i in range(n_ordered)]

    # Cycle 0 — post-reset state, before anything is driven.
    _state_checks(seq, model, opts)
    seq.expect("rd_data", 0)
    seq.advance()

    # Phase 1 — push distinct values, then read them back in order.
    for value in values:
        seq.drive(wr_en=1, wr_data=value)
        model.push(value)
        seq.advance()
    seq.drive(wr_en=0, rd_en=1)
    _state_checks(seq, model, opts)  # all pushes have landed
    seq.advance()
    for _ in values:
        model.pop()
        seq.expect("rd_data", model.rd_data)
        _state_checks(seq, model, opts)
        seq.advance()
    seq.drive(rd_en=0)

    # Phase 2 — fill to full in one driven cycle plus idle time, then keep
    # writing to prove an overflow is ignored rather than wrapping.
    fill = mask
    seq.drive(wr_en=1, wr_data=fill)
    for _ in range(opts.depth):
        model.push(fill)
    seq.advance(opts.depth)
    _state_checks(seq, model, opts)
    seq.advance(2)  # two more cycles of wr_en against a full FIFO
    model.push(fill)  # ignored by the model, exactly as by the RTL
    model.push(fill)
    _state_checks(seq, model, opts)
    seq.drive(wr_en=0)
    seq.advance()

    # Phase 3 — drain, then keep reading to prove an underflow is ignored and
    # leaves rd_data holding the last word.
    seq.drive(rd_en=1)
    for _ in range(opts.depth):
        model.pop()
    seq.advance(opts.depth)
    _state_checks(seq, model, opts)
    seq.expect("rd_data", model.rd_data)
    seq.advance(2)
    model.pop()  # ignored
    model.pop()
    _state_checks(seq, model, opts)
    seq.expect("rd_data", model.rd_data)
    seq.drive(rd_en=0)
    seq.advance()

    items: list[AssertionItem] = [
        ResetKnownValue(name="rd_data_reset_value", signal="rd_data", value=0, width=opts.width),
        ResetKnownValue(name="empty_after_reset", signal="empty", value=1, width=1),
        ResetKnownValue(name="not_full_after_reset", signal="full", value=0, width=1),
    ]
    if opts.count_output:
        items.append(
            ResetKnownValue(
                name="count_zero_after_reset",
                signal="count",
                value=0,
                width=opts.addr_bits + 1,
            )
        )

    return TbSpec(
        clock="clk",
        reset="rst",
        reset_cycles=2,
        vectors=seq.vectors,
        checks=seq.checks,
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


# --------------------------------------------------------------------------- #
# IP metadata
# --------------------------------------------------------------------------- #


def register_map(opts: SyncFifoOptions) -> RegisterMap | None:  # noqa: ARG001
    """None: a FIFO has no software-visible registers.

    This is the ``RegisterMap | None`` branch of the ``IpDef`` contract. It
    exists precisely so a datapath IP is not forced to invent a register map,
    and the AXI register block could not demonstrate it.
    """
    return None


def bundles(opts: SyncFifoOptions) -> list[PortBundle]:  # noqa: ARG001
    """The write and read ports, as two bundles **sharing one clock**.

    That sharing is the case ``bundles.py``'s "clocks are referenced, not
    owned" rule exists for: a port may belong to at most one bundle, so if the
    clock were a member, two bundles in one clock domain would be illegal.
    """
    return [
        PortBundle(
            name="wr",
            protocol="fifo-write",
            role="target",
            clock="clk",
            reset="rst",
            description="Write port; the producer drives en/data and observes full.",
            ports=[
                BundlePort(signal="wr_en", role_name="en"),
                BundlePort(signal="wr_data", role_name="data"),
                BundlePort(signal="full", role_name="full"),
            ],
        ),
        PortBundle(
            name="rd",
            protocol="fifo-read",
            role="target",
            clock="clk",
            reset="rst",
            description="Read port; the consumer drives en and observes data/empty.",
            ports=[
                BundlePort(signal="rd_en", role_name="en"),
                BundlePort(signal="rd_data", role_name="data"),
                BundlePort(signal="empty", role_name="empty"),
            ],
        ),
    ]


def port_groups(opts: SyncFifoOptions) -> list[PortGroup]:
    reset_name = "rst" + ("_n" if opts.reset_polarity == "active_low" else "")
    status = ["empty"]
    if opts.count_output:
        status.append("count")
    return [
        PortGroup(
            name="Clocking",
            ports=["clk", reset_name],
            description="Single clock domain; reset empties the FIFO.",
        ),
        PortGroup(
            name="Write port",
            ports=["wr_en", "wr_data", "full"],
            description="Producer side (bundle `wr`); writes while full are ignored.",
        ),
        PortGroup(
            name="Read port",
            ports=["rd_en", "rd_data", *status],
            description="Consumer side (bundle `rd`); reads while empty are ignored.",
        ),
    ]


def explain(opts: SyncFifoOptions) -> ExplanationDoc:
    reset_name = "rst" + ("_n" if opts.reset_polarity == "active_low" else "")
    aw = opts.addr_bits
    signals = [
        SignalDoc(name="clk", direction="input", description="Clock for both ports."),
        SignalDoc(name=reset_name, direction="input", description=_reset_doc(opts) + "."),
        SignalDoc(
            name="wr_en",
            direction="input",
            description="Write enable; the word is accepted unless full.",
        ),
        SignalDoc(name="wr_data", direction="input", description="Write data."),
        SignalDoc(
            name="full",
            direction="output",
            description="High when all entries are occupied; writes are then ignored.",
        ),
        SignalDoc(
            name="rd_en",
            direction="input",
            description="Read enable; a word is popped unless empty.",
        ),
        SignalDoc(
            name="rd_data",
            direction="output",
            description="Registered read data, valid the cycle after an accepted rd_en.",
        ),
        SignalDoc(
            name="empty",
            direction="output",
            description="High when no entries remain; reads are then ignored.",
        ),
    ]
    if opts.count_output:
        signals.append(
            SignalDoc(
                name="count",
                direction="output",
                description=f"Current occupancy, 0..{opts.depth} ({aw + 1} bits).",
            )
        )
    signals.append(
        SignalDoc(
            name="wptr",
            direction="internal",
            description=f"Write pointer, {aw + 1} bits: {aw} index bits plus a wrap bit.",
        )
    )
    signals.append(
        SignalDoc(
            name="rptr",
            direction="internal",
            description=f"Read pointer, {aw + 1} bits: {aw} index bits plus a wrap bit.",
        )
    )

    return ExplanationDoc(
        purpose=(
            f"A {opts.depth}-entry, {opts.width}-bit synchronous FIFO. Read and "
            "write pointers carry an extra wrap bit, so full and empty are "
            "distinguishable and the occupancy count is exact without any "
            "separate counter or saturating logic."
        ),
        configuration=[
            f"Width: {opts.width} bits",
            f"Depth: {opts.depth} entries (power of two; {aw}-bit index + wrap bit)",
            f"Count output: {'yes' if opts.count_output else 'no'}",
            f"Reset: {opts.reset_style}, "
            f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'}",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The {opts.reset_style} "
            f"{'active-low' if opts.reset_polarity == 'active_low' else 'active-high'} "
            "reset returns both pointers to zero, so the FIFO reads empty and not "
            "full immediately. The storage array is deliberately not cleared — "
            "stale entries are unreachable while empty, and clearing a deep memory "
            "on reset costs logic for no observable difference."
        ),
        assumptions=[
            "One clock drives both ports; this is not a clock-domain-crossing "
            "FIFO (see the limitations).",
            "Depth is a power of two, which is what makes the wrap-bit pointer "
            "comparison exact.",
            "The producer honours full and the consumer honours empty; the FIFO "
            "ignores violations rather than signalling them.",
        ],
        limitations=[
            "Reads are registered (plain FIFO), so rd_data is valid the cycle "
            "after rd_en. There is no first-word-fall-through mode: FWFT is a "
            "different read contract, not a flag, and offering both behind one "
            "boolean produces a datasheet that describes neither exactly.",
            "Overflow and underflow are ignored silently — a write while full "
            "and a read while empty leave the FIFO untouched, with no error "
            "output to detect that it happened.",
            "Single clock domain only. Crossing clocks needs the gray-pointer "
            "asynchronous FIFO, which is a separate IP.",
            "No almost-full / almost-empty thresholds.",
        ],
    )


@dataclass(frozen=True)
class _SyncFifoIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "sync-fifo"
    name: str = "Synchronous FIFO"
    description: str = (
        "Single-clock FIFO with wrap-bit pointers giving exact full/empty and "
        "an occupancy count; registered reads, overflow and underflow ignored."
    )
    kind: str = "ip"
    maturity: str = "stable"
    options_model: type[SyncFifoOptions] = SyncFifoOptions

    def generate(self, opts: SyncFifoOptions) -> Module:
        return generate(opts)

    def explain(self, opts: SyncFifoOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: SyncFifoOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: SyncFifoOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: SyncFifoOptions) -> RegisterMap | None:
        return register_map(opts)

    def bundles(self, opts: SyncFifoOptions) -> list[PortBundle]:
        return bundles(opts)


IP = _SyncFifoIp()

__all__ = [
    "SyncFifoOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "register_map",
    "bundles",
    "IP",
]
