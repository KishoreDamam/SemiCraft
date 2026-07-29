"""Declarative spec model for the checker/monitor/scoreboard generator (P3-06).

A tiny frozen-dataclass model describing *which* directed SystemVerilog
verification scaffolds to emit — a passive bundle **monitor**, a procedural
**checker** (reset-value / stability / latency), and an expected-value
**scoreboard** (class + optional wrapper module). Directed, not UVM (PRD
non-goal): no ``uvm_*`` base classes, no factory, no ``config_db``, no
phasing — plain SystemVerilog.

Design (mirrors ``semicraft_core/assertions/spec.py`` and ``tb/nodes.py``):
every type is a **frozen + slotted** dataclass with full type annotations;
sequence-valued fields accept any ``Sequence`` and are stored as ``tuple``
(immutability + hashability). Signal names are taken **verbatim** — already
styled by the caller — this model never rewrites identifiers.

Documented approximation (consistent with TB_SPEC §5's opaque-text fields):
qualifiers, expressions, and item types on these specs (``qualifier``,
``push_expr``, ``item_type``, ...) are raw SystemVerilog text. The generator
does not parse them, so it cannot verify that identifiers used *inside* such
text are actually declared as ports — the caller must list every referenced
signal on the relevant ``fields``/``ports`` sequence, or the emitted scaffold
will not compile. See ``docs/CHECKERS.md``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

__all__ = [
    "Signal",
    "ResetPolarity",
    "MonitorSpec",
    "ResetValueCheck",
    "StabilityCheck",
    "LatencyCheck",
    "CheckerItem",
    "CheckerSpec",
    "ScoreboardWrapper",
    "ScoreboardSpec",
]


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Signal:
    """One DUT-facing net exposed as an ``input logic`` port on a scaffold.

    ``name`` is the already-styled signal name (taken verbatim). ``width``
    sizes the port declaration: ``input logic [width-1:0] name`` when
    ``width > 1``, bare ``input logic name`` when ``width == 1`` (default).
    """

    name: str
    width: int = 1


@dataclass(frozen=True, slots=True)
class ResetPolarity:
    """Reset net + asserted polarity for procedural checker guards.

    Deliberately narrower than ``assertions.spec.ResetContext``: procedural
    checks (plain ``always @(posedge clk) if (...) $error(...);``) evaluate
    once per clock edge regardless of whether the reset that drives them is
    synchronous or asynchronous, so there is no ``sync`` field to carry here
    (see ``docs/CHECKERS.md`` for the procedural-vs-SVA distinction).
    """

    signal: str
    active_low: bool


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MonitorSpec:
    """Passive transaction-monitor recipe.

    Emits an SV ``module`` (:func:`~semicraft_core.checkers.generate.generate_monitor`)
    that samples ``fields`` on ``posedge clock`` — under ``qualifier`` when
    given — and ``$display``s a formatted transaction record. Passive: the
    generated module drives no signal, only reads.

    - ``name`` — the generated module name.
    - ``clock`` — the bare clock net name (verbatim).
    - ``fields`` — the sampled/printed signal bundle, in declaration and
      print order.
    - ``qualifier`` — an optional opaque boolean expression (e.g.
      ``"valid && ready"``) gating the sample/print; ``None`` samples/prints
      unconditionally every clock edge. Every identifier the qualifier text
      uses must already appear in ``fields`` (or be a module-global net) —
      this generator never parses the qualifier (documented approximation).
    """

    name: str
    clock: str
    fields: tuple[Signal, ...]
    qualifier: str | None = None

    def __init__(
        self,
        name: str,
        clock: str,
        fields: Sequence[Signal],
        qualifier: str | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "clock", clock)
        object.__setattr__(self, "fields", tuple(fields))
        object.__setattr__(self, "qualifier", qualifier)


# ---------------------------------------------------------------------------
# Checker items
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResetValueCheck:
    """``signal`` takes a known value on reset deassertion (procedural).

    Distinct from ``assertions.spec.ResetKnownValue``: that family emits a
    concurrent SVA property (``$rose(rst_n) |-> signal == width'dvalue``);
    this one compiles to a plain ``always @(posedge clock)`` block that
    edge-detects reset deassertion off a one-cycle-delayed shadow of the
    reset net and ``$error``s procedurally. Requires
    :attr:`CheckerSpec.reset`; :func:`~.generate.generate_checker` raises
    :class:`ValueError` if the spec has no reset. Never guarded (like its SVA
    counterpart) — it is the check *about* reset, so gating it on reset would
    defeat its purpose.
    """

    name: str
    signal: str
    value: int
    width: int


@dataclass(frozen=True, slots=True)
class StabilityCheck:
    """``signal`` is unchanged one cycle after ``enable`` was deasserted (procedural).

    Procedural analogue of ``assertions.spec.Stability``'s
    ``!enable |=> $stable(signal)``: one-cycle-delayed shadow registers of
    both ``enable`` and ``signal`` are compared against their current values
    each clock edge. ``width`` sizes the ``signal`` shadow register (this
    family needs it explicitly — SVA's ``$stable`` never did).

    ``guarded`` (default ``True``) skips the check while the spec's reset is
    *currently* asserted. This is a weaker approximation than SVA
    ``disable iff``, which disables the assertion's entire evaluation window
    (including the sample that feeds ``$stable``'s "previous" value) rather
    than just gating the current check — see ``docs/CHECKERS.md``.
    """

    name: str
    signal: str
    enable: str
    width: int
    guarded: bool = True


@dataclass(frozen=True, slots=True)
class LatencyCheck:
    """``response`` must arrive within ``max_cycles`` cycles of ``request`` (procedural).

    Compiles to a small pending/wait-counter state machine: ``request``
    (while nothing is already pending) arms a countdown; ``response`` clears
    it; if the counter reaches ``max_cycles`` before ``response`` arrives,
    ``$error`` fires and the pending state resets. Only one outstanding
    request is tracked — a second ``request`` while one is already pending is
    not separately queued (documented approximation, see
    ``docs/CHECKERS.md``). ``guarded`` (default ``True``) resets the
    pending/wait state while the spec's reset is asserted; ``max_cycles``
    must be positive (validated by :func:`~.generate.generate_checker`).
    """

    name: str
    request: str
    response: str
    max_cycles: int
    guarded: bool = True


# The checker item union accepted by :class:`CheckerSpec`. Each member maps to
# exactly one procedural ``always`` block (plus, for :class:`StabilityCheck`
# and :class:`LatencyCheck`, the shadow/state registers it needs).
CheckerItem = ResetValueCheck | StabilityCheck | LatencyCheck


@dataclass(frozen=True, slots=True)
class CheckerSpec:
    """A module's procedural protocol-check recipe.

    Emits an SV ``module`` holding directed, *procedural* checks
    (``always @(posedge clk) if (...) $error(...);``) — distinct from the
    P3-05 concurrent-SVA (``assert property``) path; the two generators are
    not interchangeable, see ``docs/CHECKERS.md``.

    - ``name`` — the generated module name.
    - ``clock`` — the bare clock net name (verbatim); becomes an
      ``input logic`` port.
    - ``reset`` — optional :class:`ResetPolarity`; becomes an ``input logic``
      port when present. Required by :class:`ResetValueCheck` items and used
      to gate ``guarded`` items.
    - ``ports`` — extra signals (beyond clock/reset) the checks refer to;
      every identifier a check's fields name must appear here (documented
      approximation — this generator never parses check-referenced text).
    - ``checks`` — ordered check items; each renders as an independent
      ``always @(posedge clock)`` block, in this order. Check names must be
      unique within the spec (they seed generated register names);
      :func:`~.generate.generate_checker` raises :class:`ValueError` on a
      collision.
    """

    name: str
    clock: str
    ports: tuple[Signal, ...]
    checks: tuple[CheckerItem, ...]
    reset: ResetPolarity | None = None

    def __init__(
        self,
        name: str,
        clock: str,
        ports: Sequence[Signal],
        checks: Sequence[CheckerItem],
        reset: ResetPolarity | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "clock", clock)
        object.__setattr__(self, "ports", tuple(ports))
        object.__setattr__(self, "checks", tuple(checks))
        object.__setattr__(self, "reset", reset)


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScoreboardWrapper:
    """Thin convenience module wrapping a scoreboard class instance.

    See :func:`~.generate.generate_scoreboard`'s docstring for the
    class-vs-module split rationale. ``push_signal``/``compare_signal`` are
    opaque boolean qualifiers gating ``push_expected``/``compare`` calls each
    clock edge; ``push_expr``/``compare_expr`` are opaque SV expressions of
    the class's ``item_type`` yielding the value pushed/compared. ``ports``
    lists every *extra* signal referenced by the four opaque-text fields that
    is not already an implicit port (``clock``, ``push_signal``, and
    ``compare_signal`` are always ports; a field consisting of a bare signal
    name that is already one of those three does not need repeating).
    """

    module_name: str
    clock: str
    push_signal: str
    push_expr: str
    compare_signal: str
    compare_expr: str
    ports: tuple[Signal, ...] = ()

    def __init__(
        self,
        module_name: str,
        clock: str,
        push_signal: str,
        push_expr: str,
        compare_signal: str,
        compare_expr: str,
        ports: Sequence[Signal] = (),
    ) -> None:
        object.__setattr__(self, "module_name", module_name)
        object.__setattr__(self, "clock", clock)
        object.__setattr__(self, "push_signal", push_signal)
        object.__setattr__(self, "push_expr", push_expr)
        object.__setattr__(self, "compare_signal", compare_signal)
        object.__setattr__(self, "compare_expr", compare_expr)
        object.__setattr__(self, "ports", tuple(ports))


@dataclass(frozen=True, slots=True)
class ScoreboardSpec:
    """Expected-value scoreboard recipe: an SV class + optional wrapper module.

    - ``name`` — the generated class name.
    - ``item_type`` — the opaque SV type of one queue element (e.g.
      ``"logic [7:0]"``, ``"int unsigned"``), taken verbatim. The class's
      ``$display``/``$error`` calls format items with ``%0d``, so
      ``item_type`` should be numeric or numeric-compatible (documented
      approximation — a struct/class ``item_type`` will not format sensibly,
      see ``docs/CHECKERS.md``).
    - ``wrapper`` — optional :class:`ScoreboardWrapper`; when given, an
      additional directed module instantiating the class and driving
      ``push_expected``/``compare`` from clock-edge qualifiers is emitted
      alongside the class.
    """

    name: str
    item_type: str
    wrapper: ScoreboardWrapper | None = None
