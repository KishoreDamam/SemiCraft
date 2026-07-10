"""Smoke-testbench node family — STUB (P2-13; full family lands P3 per P3-01).

A deliberately tiny, frozen-dataclass node family that is *just* enough to
express the directed smoke testbenches P2-13 emits: a clock generator, a reset
sequence, per-cycle input drives, and self-checking expected-value assertions.

Separation from the synthesizable IR (cross-cutting decision 2, plan §Waves):
this family shares **no** nodes with ``semicraft_core.ir`` — TB statements
(``DriveSignal``/``WaitCycles``/``ExpectSignal``/...) are their own types so the
synthesizable IR validator never sees a testbench construct and vice-versa. The
only reference back into the synthesizable world is by *name*: a :class:`TbModule`
carries the already-styled DUT port/net names, resolved against the rendered RTL
(see ``generate_tb``), so the testbench's connections match the RTL byte-for-byte.

Everything here renders to **SystemVerilog only** (Verilator-compatible); the
full multi-language TB family is out of scope until Phase 3 (see docs/TB_SPEC.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "TbComment",
    "DriveSignal",
    "Delay",
    "WaitCycles",
    "ExpectSignal",
    "Display",
    "Finish",
    "Stmt",
    "Decl",
    "ClockGen",
    "DutInstance",
    "Initial",
    "TbModule",
]


# ---------------------------------------------------------------------------
# Statements (body of an Initial block)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TbComment:
    """A ``// text`` comment line inside the stimulus process."""

    text: str


@dataclass(frozen=True, slots=True)
class DriveSignal:
    """Blocking assignment ``signal = <width>'d<value>;`` driving a DUT input.

    ``signal`` is the already-styled net name (matches the rendered RTL port);
    ``width`` is the concrete bit width used to size the literal.
    """

    signal: str
    value: int
    width: int


@dataclass(frozen=True, slots=True)
class Delay:
    """A ``#<ns>;`` delay (lets combinational logic settle before a check)."""

    ns: int


@dataclass(frozen=True, slots=True)
class WaitCycles:
    """Wait ``n`` clock edges: ``repeat (n) @(<edge> clk);`` (``n==1`` drops the
    ``repeat``). ``edge`` is ``"posedge"`` or ``"negedge"``."""

    n: int
    edge: str = "posedge"


@dataclass(frozen=True, slots=True)
class ExpectSignal:
    """A self-checking assertion: ``if (signal !== <width>'d<expected>) $fatal(...)``.

    ``!==`` (case inequality) so an ``x``/``z`` on the sampled net fails loudly.
    ``cycle_label`` is a human string (e.g. ``"cycle 2"``) used in the message.
    """

    signal: str
    expected: int
    width: int
    cycle_label: str


@dataclass(frozen=True, slots=True)
class Display:
    """A ``$display("message");`` line (the terminal SMOKE PASS banner)."""

    message: str


@dataclass(frozen=True, slots=True)
class Finish:
    """A ``$finish;`` — ends the simulation."""


# The statement union accepted inside an :class:`Initial` block.
Stmt = TbComment | DriveSignal | Delay | WaitCycles | ExpectSignal | Display | Finish


# ---------------------------------------------------------------------------
# Structural nodes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Decl:
    """One ``logic`` net declaration in the testbench: ``logic [width-1:0] name;``
    (or ``logic name;`` when ``width == 1``). ``name`` is the styled net name."""

    name: str
    width: int


@dataclass(frozen=True, slots=True)
class ClockGen:
    """Free-running clock: ``initial <signal> = 1'b0;`` + ``always #<hp> ...``.

    ``half_period_ns`` is the half period (default 5ns -> 10ns / 100MHz clock).
    """

    signal: str
    half_period_ns: int = 5


@dataclass(frozen=True, slots=True)
class DutInstance:
    """Instantiation of the DUT: ``<module> <inst> ( .<port>(<net>), ... );``.

    ``connections`` are ``(styled_port, styled_net)`` pairs in port-declaration
    order; the net name equals the port name for a smoke TB (one net per port).
    """

    module: str
    instance: str
    connections: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class Initial:
    """The single stimulus ``initial begin ... end`` process."""

    stmts: tuple[Stmt, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class TbModule:
    """Root smoke-testbench node.

    - ``name`` — testbench module name (``<dut>_tb``).
    - ``decls`` — one :class:`Decl` per DUT port (the driven/observed nets).
    - ``clock`` — the free-running clock generator.
    - ``dut`` — the DUT instantiation (references the RTL module's ports).
    - ``initial`` — the stimulus + self-checking process.
    - ``banner`` — pre-rendered header comment lines (mirrors the RTL banner).
    """

    name: str
    decls: tuple[Decl, ...]
    clock: ClockGen
    dut: DutInstance
    initial: Initial
    banner: tuple[str, ...] = ()
