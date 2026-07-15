"""Testbench IR node family (P3-01 — full Phase 3 family).

A frozen-dataclass node family for directed SystemVerilog testbenches. It began
(P2-13) as a tiny "smoke" set — clock, reset, per-cycle drives, self-checking
expects — and is extended here (P3-01) with the constructs the Phase 3
verification generators need: level-sensitive waits, fork/join concurrency,
loops, conditionals, a timeout watchdog, waveform dumping, reusable tasks, and
an SVA-property stub. The P2 smoke set is preserved *source-compatible*: the
smoke-TB pipeline (``generate_tb`` -> ``render_tb``) and its golden files are
byte-identical to before.

Separation from the synthesizable IR (cross-cutting decision 2, plan §Waves):
this family shares **no** nodes with ``semicraft_core.ir`` — TB statements
(``DriveSignal``/``WaitCycles``/``ExpectSignal``/...) are their own types so the
synthesizable IR validator never sees a testbench construct and vice-versa. The
:func:`~.validate.validate_tb` T3 rule enforces the mirror direction (no IR node
may be smuggled into a TB tree). The only reference back into the synthesizable
world is by *name*: a :class:`TbModule` carries the already-styled DUT port/net
names, resolved against the rendered RTL (see ``generate_tb``), so the
testbench's connections match the RTL byte-for-byte.

Everything here targets **SystemVerilog only** (Verilator-compatible). Renderers
for the new P3-01 nodes land with P3-02; only the P2 smoke subset is rendered by
``render_tb`` today. See docs/TB_SPEC.md.

Conventions (mirrors IR_SPEC §2): frozen + slotted dataclasses; list-valued
fields accept any ``Sequence`` and are stored as ``tuple`` (immutability +
hashability); full type annotations; no defaults that hide required semantics.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__all__ = [
    # statements — P2 smoke set
    "TbComment",
    "DriveSignal",
    "Delay",
    "WaitCycles",
    "ExpectSignal",
    "Display",
    "Finish",
    # statements — P3-01 additions
    "WaitUntil",
    "ForkJoin",
    "RepeatBlock",
    "IfTb",
    "TimeoutGuard",
    "Dump",
    "CallTask",
    "Stmt",
    # module-level structural — P2 smoke set
    "Decl",
    "ClockGen",
    "DutInstance",
    "Initial",
    "TbModule",
    # module-level structural — P3-01 additions
    "ResetSeq",
    "Task",
    "AssertProperty",
    # constants
    "JOIN_KINDS",
]

# Allowed ``ForkJoin.join`` disciplines (SystemVerilog ``join``/``join_any``/
# ``join_none``). Validated by :func:`~.validate.validate_tb` rule T4.
JOIN_KINDS: frozenset[str] = frozenset({"all", "any", "none"})


# ---------------------------------------------------------------------------
# Statements — P2 smoke set (bodies of an Initial block / Task)
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
    ``repeat``). ``edge`` is ``"posedge"`` or ``"negedge"``. The edge is taken on
    the testbench clock (:attr:`TbModule.clock`), not an arbitrary net."""

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


# ---------------------------------------------------------------------------
# Statements — P3-01 additions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WaitUntil:
    """Level-sensitive wait ``wait (<condition_text>);``.

    ``condition_text`` is a pre-formed SystemVerilog boolean expression string
    (e.g. ``"done == 1'b1"``). The TB family keeps such conditions as opaque
    text for now — a first-class TB expression AST is a later phase — so the
    validator can only check that the text is non-empty, not that its identifiers
    resolve. Document this approximation with the node, not silently.
    """

    condition_text: str


@dataclass(frozen=True, slots=True)
class ForkJoin:
    """Concurrent ``fork ... join[_any|_none]`` block.

    ``branches`` is a tuple of parallel branches, each an ordered tuple of
    statements run in its own thread. ``join`` selects the join discipline:
    ``"all"`` -> ``join``, ``"any"`` -> ``join_any``, ``"none"`` -> ``join_none``
    (see :data:`JOIN_KINDS`).
    """

    branches: tuple[tuple[Stmt, ...], ...]
    join: str

    def __init__(
        self, branches: Sequence[Sequence[Stmt]], join: str
    ) -> None:
        object.__setattr__(
            self, "branches", tuple(tuple(branch) for branch in branches)
        )
        object.__setattr__(self, "join", join)


@dataclass(frozen=True, slots=True)
class RepeatBlock:
    """Bounded loop ``repeat (count) begin <stmts> end``."""

    count: int
    stmts: tuple[Stmt, ...]

    def __init__(self, count: int, stmts: Sequence[Stmt]) -> None:
        object.__setattr__(self, "count", count)
        object.__setattr__(self, "stmts", tuple(stmts))


@dataclass(frozen=True, slots=True)
class IfTb:
    """Conditional ``if (<condition_text>) begin ... end [else begin ... end]``.

    ``condition_text`` is opaque SV boolean text (see :class:`WaitUntil`).
    ``else_`` is ``None`` when there is no else arm.
    """

    condition_text: str
    then: tuple[Stmt, ...]
    else_: tuple[Stmt, ...] | None

    def __init__(
        self,
        condition_text: str,
        then: Sequence[Stmt],
        else_: Sequence[Stmt] | None = None,
    ) -> None:
        object.__setattr__(self, "condition_text", condition_text)
        object.__setattr__(self, "then", tuple(then))
        object.__setattr__(
            self, "else_", None if else_ is None else tuple(else_)
        )


@dataclass(frozen=True, slots=True)
class TimeoutGuard:
    """Watchdog: a forked thread that ``$fatal``s after ``cycles`` clock edges.

    Renders (P3-02) as a ``fork``-ed branch that ``repeat (cycles) @(posedge
    clk); $fatal(1, message);`` — a hung DUT fails loudly instead of stalling the
    simulator. ``cycles`` must be > 0 (validated, T4).
    """

    cycles: int
    message: str


@dataclass(frozen=True, slots=True)
class Dump:
    """Waveform dump ``$dumpfile("<file>"); $dumpvars(<levels>, <top>);``.

    ``file`` must be a safe *relative* filename (no path separators, no ``..`` —
    validated, T7). ``levels`` is the ``$dumpvars`` hierarchy depth (``0`` = all
    levels below the dumped scope).
    """

    file: str
    levels: int = 0


@dataclass(frozen=True, slots=True)
class CallTask:
    """Invoke a named :class:`Task`: ``<name>();``.

    ``name`` must resolve to a declared :class:`Task` on the enclosing
    :class:`TbModule`; recursive task cycles are rejected (validated, T5).
    """

    name: str


# The statement union accepted inside an :class:`Initial` block, a :class:`Task`
# body, a :class:`ForkJoin` branch, a :class:`RepeatBlock`, or an :class:`IfTb`
# arm. Every member is a TB-owned type — never a ``semicraft_core.ir`` node
# (enforced by validate_tb T3).
Stmt = (
    TbComment
    | DriveSignal
    | Delay
    | WaitCycles
    | ExpectSignal
    | Display
    | Finish
    | WaitUntil
    | ForkJoin
    | RepeatBlock
    | IfTb
    | TimeoutGuard
    | Dump
    | CallTask
)


# ---------------------------------------------------------------------------
# Structural nodes — P2 smoke set
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


# ---------------------------------------------------------------------------
# Structural nodes — P3-01 additions
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResetSeq:
    """Declarative reset sequence for a testbench.

    Formalizes the assert/hold/deassert dance ``generate_tb`` inlines today as
    raw ``DriveSignal``/``WaitCycles`` statements: assert ``signal`` at time 0,
    hold it for ``cycles`` clock edges, then deassert. ``active_low`` selects the
    asserted level (``0`` asserted / ``1`` deasserted when true). Adoption by
    ``generate_tb`` is deferred to P3-02/04 — it may only switch to ``ResetSeq``
    if the rendered text stays byte-identical.
    """

    signal: str
    active_low: bool
    cycles: int


@dataclass(frozen=True, slots=True)
class Task:
    """A named, reusable stimulus sequence: ``task <name>; ... endtask``.

    Invoked from an :class:`Initial`, another :class:`Task`, or any nested block
    via :class:`CallTask`. ``name`` must be a canonical lower_snake_case
    identifier, unique among tasks (validated, T1); recursive task cycles are
    rejected (T5).
    """

    name: str
    stmts: tuple[Stmt, ...]

    def __init__(self, name: str, stmts: Sequence[Stmt]) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "stmts", tuple(stmts))


@dataclass(frozen=True, slots=True)
class AssertProperty:
    """SVA concurrent-assertion **stub**: property expressed as opaque text.

    ``property_text`` is a raw SystemVerilog property expression (e.g.
    ``"req |-> ##[1:3] ack"``); a first-class property AST is a later phase
    (plan P3-05 and beyond), so for P3-01 the TB family carries the property as a
    string and only checks that it is non-empty. ``clock`` names the sampling
    clock (must resolve to a :class:`Decl` or the :class:`ClockGen` signal, T8);
    ``disable_iff`` is an optional reset-guard expression (``disable iff (...)``),
    ``None`` when absent. ``name`` is the assertion label, unique per TB (T8).

    Documented approximation: because ``property_text``/``disable_iff`` are
    opaque, the validator cannot check that the identifiers *inside* them
    resolve — only structural fields (name uniqueness, non-empty text, clock
    resolution) are validated.
    """

    name: str
    property_text: str
    clock: str
    disable_iff: str | None


@dataclass(frozen=True, slots=True)
class TbModule:
    """Root testbench node.

    - ``name`` — testbench module name (``<dut>_tb``).
    - ``decls`` — one :class:`Decl` per DUT port (the driven/observed nets).
    - ``clock`` — the free-running clock generator.
    - ``dut`` — the DUT instantiation (references the RTL module's ports).
    - ``initial`` — the stimulus + self-checking process.
    - ``banner`` — pre-rendered header comment lines (mirrors the RTL banner).
    - ``tasks`` — reusable :class:`Task` sequences (P3-01; default empty).
    - ``asserts`` — :class:`AssertProperty` stubs (P3-01; default empty).
    - ``reset_seq`` — optional declarative :class:`ResetSeq` (P3-01; default
      ``None``). The P2 smoke TB still inlines reset as drives/waits.

    The P3-01 fields are additive with defaults, so P2 constructions (the smoke
    TB) build unchanged and render byte-identically.
    """

    name: str
    decls: tuple[Decl, ...]
    clock: ClockGen
    dut: DutInstance
    initial: Initial
    banner: tuple[str, ...] = ()
    tasks: tuple[Task, ...] = ()
    asserts: tuple[AssertProperty, ...] = ()
    reset_seq: ResetSeq | None = None

    def __init__(
        self,
        name: str,
        decls: Sequence[Decl],
        clock: ClockGen,
        dut: DutInstance,
        initial: Initial,
        banner: Sequence[str] = (),
        tasks: Sequence[Task] = (),
        asserts: Sequence[AssertProperty] = (),
        reset_seq: ResetSeq | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "decls", tuple(decls))
        object.__setattr__(self, "clock", clock)
        object.__setattr__(self, "dut", dut)
        object.__setattr__(self, "initial", initial)
        object.__setattr__(self, "banner", tuple(banner))
        object.__setattr__(self, "tasks", tuple(tasks))
        object.__setattr__(self, "asserts", tuple(asserts))
        object.__setattr__(self, "reset_seq", reset_seq)
