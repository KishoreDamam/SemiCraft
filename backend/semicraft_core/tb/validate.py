"""Testbench IR validation (TB_SPEC §Validation, rules T1–T8).

``validate_tb(tb)`` runs over a :class:`~.nodes.TbModule` before rendering. Like
the synthesizable :func:`semicraft_core.ir.validate.validate`, it collects **all**
violations (not just the first) and raises a single :class:`TbValidationError`
whose message enumerates them, sorted for determinism.

Two directions of the TB/RTL separation invariant (plan cross-cutting decision 2)
are enforced here and by construction:

* **TB may not contain synthesizable IR** — rule T3 walks every TB statement/item
  and rejects any ``semicraft_core.ir`` node smuggled into the tree.
* **RTL may not contain TB nodes** — the mirror direction needs no runtime check:
  ``semicraft_core.ir.validate`` operates on ``ir.nodes`` types only and never
  imports these TB types, so a TB node can never appear in an IR ``Module`` it
  validates. The types simply do not meet. This asymmetry is intentional and
  documented in TB_SPEC.

Several TB fields are *opaque text* for P3-01 (``WaitUntil.condition_text``,
``IfTb.condition_text``, ``AssertProperty.property_text``/``disable_iff``): a
first-class TB expression AST is a later phase, so the validator checks their
structural shell (non-empty, name/clock resolution) but cannot resolve the
identifiers *inside* the text. Each such approximation is noted in TB_SPEC.
"""

from __future__ import annotations

import re

from ..ir.validate import SV_KEYWORDS, VERILOG_KEYWORDS
from .nodes import (
    JOIN_KINDS,
    CallTask,
    DriveSignal,
    Dump,
    ExpectSignal,
    Finish,
    ForkJoin,
    IfTb,
    RepeatBlock,
    Stmt,
    TbModule,
    TimeoutGuard,
)

__all__ = ["validate_tb", "TbValidationError"]

# Canonical TB identifier: lower_snake_case ASCII (mirrors IR_SPEC design rule 5).
_IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class TbValidationError(Exception):
    """Raised when a :class:`~.nodes.TbModule` violates one or more T-rules.

    ``violations`` holds the sorted list of individual messages; ``str`` gives a
    single multi-line message enumerating them all.
    """

    def __init__(self, violations: list[str]) -> None:
        self.violations = sorted(violations)
        header = f"TB validation failed with {len(self.violations)} violation(s):"
        body = "\n".join(f"  - {v}" for v in self.violations)
        super().__init__(f"{header}\n{body}")


def _is_ident(name: str) -> bool:
    return bool(_IDENT_RE.match(name))


def _is_ir_node(obj: object) -> bool:
    """True if ``obj`` is a synthesizable IR node (``semicraft_core.ir`` type).

    Uses the defining module rather than an isinstance list against the IR bases
    so it catches *every* IR type (expressions, statements, module items, and
    the supporting specs like ``CaseItem``/``Header``/``Param``) without this
    module importing the whole IR node catalog.
    """
    return type(obj).__module__.startswith("semicraft_core.ir")


def _walk_stmts(stmts, where: str):
    """Yield ``(stmt, where)`` for every statement in ``stmts``, descending into
    the TB container statements (``ForkJoin``/``RepeatBlock``/``IfTb``).

    Foreign nodes (e.g. a smuggled IR node) are yielded but not descended into —
    T3 flags them by identity; the walker only knows how to open TB containers.
    """
    for s in stmts:
        yield s, where
        if isinstance(s, ForkJoin):
            for i, branch in enumerate(s.branches):
                yield from _walk_stmts(branch, f"{where} > fork branch {i}")
        elif isinstance(s, RepeatBlock):
            yield from _walk_stmts(s.stmts, f"{where} > repeat body")
        elif isinstance(s, IfTb):
            yield from _walk_stmts(s.then, f"{where} > if-then")
            if s.else_ is not None:
                yield from _walk_stmts(s.else_, f"{where} > if-else")


def _contains_finish(s: Stmt) -> bool:
    """True if ``s`` is a ``Finish`` or a TB container holding one (any depth)."""
    if isinstance(s, Finish):
        return True
    if isinstance(s, ForkJoin):
        return any(_contains_finish(x) for branch in s.branches for x in branch)
    if isinstance(s, RepeatBlock):
        return any(_contains_finish(x) for x in s.stmts)
    if isinstance(s, IfTb):
        if any(_contains_finish(x) for x in s.then):
            return True
        return s.else_ is not None and any(_contains_finish(x) for x in s.else_)
    return False


def _find_task_cycle(adj: dict[str, set[str]], nodes: list[str]) -> list[str] | None:
    """Return the first task-call cycle (as a path ``a -> ... -> a``), else None.

    Deterministic: nodes and successors are visited in sorted order.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = dict.fromkeys(nodes, WHITE)
    stack: list[str] = []

    def dfs(u: str) -> list[str] | None:
        color[u] = GRAY
        stack.append(u)
        for w in sorted(adj.get(u, ())):
            if color.get(w) == GRAY:
                return stack[stack.index(w):] + [w]
            if color.get(w) == WHITE:
                found = dfs(w)
                if found is not None:
                    return found
        stack.pop()
        color[u] = BLACK
        return None

    for n in sorted(nodes):
        if color[n] == WHITE:
            found = dfs(n)
            if found is not None:
                return found
    return None


def _safe_dump_name(name: str) -> bool:
    """True if ``name`` is a safe *relative* filename (T7)."""
    if not name:
        return False
    if "/" in name or "\\" in name or ".." in name or ":" in name:
        return False
    return True


def validate_tb(
    tb: TbModule, extra_reserved: frozenset[str] = frozenset()
) -> None:
    """Validate ``tb`` against TB_SPEC rules T1–T8.

    Raise :class:`TbValidationError` listing *all* violations, or return ``None``
    if the testbench is well-formed. ``extra_reserved`` supplements the built-in
    SV+Verilog keyword sets for the T1 identifier reserved-word check.
    """
    v: list[str] = []
    reserved = SV_KEYWORDS | VERILOG_KEYWORDS | extra_reserved

    decl_names = [d.name for d in tb.decls]
    task_names = [t.name for t in tb.tasks]
    clock_signal = tb.clock.signal
    declared_signals = set(decl_names) | {clock_signal}

    # Every statement in the whole TB (main Initial + every Task body), with a
    # human-readable location for messages.
    walked: list[tuple[Stmt, str]] = list(_walk_stmts(tb.initial.stmts, "initial"))
    for t in tb.tasks:
        walked.extend(_walk_stmts(t.stmts, f"task {t.name!r}"))

    # --- T1: identifiers, uniqueness, DUT-instance collision ----------------
    for name in decl_names:
        if not _is_ident(name):
            v.append(f"[T1] declaration name is not lower_snake_case: {name!r}")
        if name in reserved:
            v.append(f"[T1] declaration name collides with a reserved word: {name!r}")
    for name in task_names:
        if not _is_ident(name):
            v.append(f"[T1] task name is not lower_snake_case: {name!r}")
        if name in reserved:
            v.append(f"[T1] task name collides with a reserved word: {name!r}")
    for names, kind in ((decl_names, "declaration"), (task_names, "task")):
        counts: dict[str, int] = {}
        for name in names:
            counts[name] = counts.get(name, 0) + 1
        for name, c in counts.items():
            if c > 1:
                v.append(f"[T1] duplicate {kind} name: {name!r}")
    inst = tb.dut.instance
    if not _is_ident(inst):
        v.append(f"[T1] DUT instance name is not lower_snake_case: {inst!r}")
    if inst in set(decl_names):
        v.append(f"[T1] DUT instance name {inst!r} collides with a declared net")
    if inst in set(task_names):
        v.append(f"[T1] DUT instance name {inst!r} collides with a task name")

    # --- T2: driven/expected signals resolve to a Decl (or the clock) --------
    # WaitCycles carries no per-node signal — it implicitly waits on the TB clock
    # (render_tb emits `@(edge clk)`), so there is nothing to resolve for it.
    for s, where in walked:
        if isinstance(s, (DriveSignal, ExpectSignal)) and s.signal not in declared_signals:
            v.append(
                f"[T2] {type(s).__name__} references undeclared signal "
                f"{s.signal!r} in {where}"
            )

    # --- T3: no synthesizable IR node anywhere in the TB tree ----------------
    for s, where in walked:
        if _is_ir_node(s):
            v.append(
                f"[T3] synthesizable IR node {type(s).__module__}."
                f"{type(s).__name__} found in TB statements ({where}); "
                f"TB and RTL node families must not mix"
            )

    # --- T4: fork/join shape; timeout watchdog cycles ------------------------
    for s, where in walked:
        if isinstance(s, ForkJoin):
            if not s.branches:
                v.append(f"[T4] ForkJoin has no branches in {where}")
            for i, branch in enumerate(s.branches):
                if not branch:
                    v.append(f"[T4] ForkJoin branch {i} is empty in {where}")
            if s.join not in JOIN_KINDS:
                v.append(
                    f"[T4] ForkJoin join {s.join!r} not one of "
                    f"{sorted(JOIN_KINDS)} in {where}"
                )
        elif isinstance(s, TimeoutGuard) and s.cycles <= 0:
            v.append(
                f"[T4] TimeoutGuard cycles must be > 0, got {s.cycles} in {where}"
            )

    # --- T5: CallTask resolves; no recursive task cycles ---------------------
    task_set = set(task_names)
    for s, where in walked:
        if isinstance(s, CallTask) and s.name not in task_set:
            v.append(f"[T5] CallTask to undeclared task {s.name!r} in {where}")
    # Call graph among declared tasks only (unresolved calls already flagged).
    adj: dict[str, set[str]] = {name: set() for name in task_names}
    for t in tb.tasks:
        for s, _where in _walk_stmts(t.stmts, ""):
            if isinstance(s, CallTask) and s.name in task_set:
                adj[t.name].add(s.name)
    cycle = _find_task_cycle(adj, task_names)
    if cycle is not None:
        v.append(f"[T5] recursive task cycle: {' -> '.join(cycle)}")

    # --- T6: exactly one $finish reachable at the top of the main Initial ----
    # Approximation (documented in TB_SPEC): we require the main Initial to
    # contain at least one $finish, its last top-level statement to be (or to
    # contain) a $finish, and at most one $finish directly at the top level.
    # This does not prove reachability along every control path (an IfTb with a
    # $finish in only one arm still passes), only that the sim can terminate.
    finish_count = sum(1 for s, _w in _walk_stmts(tb.initial.stmts, "") if isinstance(s, Finish))
    top_level_finishes = [s for s in tb.initial.stmts if isinstance(s, Finish)]
    if finish_count == 0:
        v.append("[T6] main Initial has no $finish (simulation would not terminate)")
    else:
        if len(top_level_finishes) > 1:
            v.append(
                "[T6] main Initial has multiple top-level $finish "
                "(statements after the first are dead)"
            )
        if not tb.initial.stmts or not _contains_finish(tb.initial.stmts[-1]):
            v.append(
                "[T6] last statement of main Initial is not a $finish "
                "(and does not contain one)"
            )

    # --- T7: Dump file is a safe relative filename ---------------------------
    for s, where in walked:
        if isinstance(s, Dump) and not _safe_dump_name(s.file):
            v.append(
                f"[T7] Dump file {s.file!r} is not a safe relative filename "
                f"(no path separators, no '..', no ':') in {where}"
            )

    # --- T8: AssertProperty names unique; text non-empty; clock resolves -----
    assert_name_counts: dict[str, int] = {}
    for a in tb.asserts:
        assert_name_counts[a.name] = assert_name_counts.get(a.name, 0) + 1
    for name, c in assert_name_counts.items():
        if c > 1:
            v.append(f"[T8] duplicate AssertProperty name: {name!r}")
    for a in tb.asserts:
        if not a.property_text.strip():
            v.append(f"[T8] AssertProperty {a.name!r} has empty property_text")
        if a.clock not in declared_signals:
            v.append(
                f"[T8] AssertProperty {a.name!r} clock {a.clock!r} does not "
                f"resolve to a declared net or the clock signal"
            )

    if v:
        raise TbValidationError(v)
