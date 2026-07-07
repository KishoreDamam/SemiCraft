"""Pre-render IR validation (IR_SPEC §6).

``validate(module)`` runs before any rendering. Errors here are *generator*
bugs, not user errors: they fail loudly (raise :class:`IRValidationError`) and,
per the API contract, map to HTTP 500 rather than silently degrading.

The raised error lists **all** violations found, not just the first, so a
generator author sees the full picture in one run. Violation messages are
sorted before joining so the message is deterministic regardless of dict or
set iteration order (ground rule: determinism).

Implements §6 rules 1–7 plus the IR_SPEC §10 v0.2 rules 8–11:

1. Valid canonical identifiers; no duplicates among params/ports/signals/enums.
2. Every ``Ref``/``EnumRef`` resolves to a declared name.
3. Single-driver rule for each driven signal.
4. ``Assign.lhs`` is a valid lvalue; ``input`` ports are never driven.
5. ``Case`` covers all enum members or has a ``default``; non-enum needs default.
6. ``AlwaysFF`` with ``reset=None`` has empty ``reset_body``.
7. Post-style reserved-word check (SV and Verilog keyword sets).
8. ``GenFor``: genvar no-shadow; ``Ref(genvar)`` only inside its own items;
   unique labels (in the rule-1 namespace); restricted item member types.
9. ``Memory``: element-select only, sync write in ``AlwaysFF``, no ContAssign
   lhs, no whole-array ref / array-dim slice.
10. ``DataType.enum_type`` resolves to a declared ``EnumDecl`` and forces
    ``width=None``.
11. ``Memory`` names and ``GenFor`` labels join the rule-1 duplicate check.
"""

from __future__ import annotations

import re

from .nodes import (
    AlwaysComb,
    AlwaysFF,
    Assign,
    BinOp,
    Bit,
    Case,
    Comment,
    Concat,
    Const,
    ContAssign,
    DataType,
    EnumDecl,
    EnumRef,
    Expr,
    GenFor,
    If,
    Instance,
    Memory,
    Module,
    Ref,
    Repl,
    Signal,
    Slice,
    Stmt,
    Ternary,
    UnaryOp,
)

# Allowed member types inside a ``GenFor`` (IR_SPEC §10.1 / rule 8).
_GENFOR_ITEM_TYPES = (ContAssign, Instance, AlwaysFF, AlwaysComb, Comment)

# ---------------------------------------------------------------------------
# Reserved-word sets (rule 7). Renderer/style engine pass the relevant set(s).
# ---------------------------------------------------------------------------

# Verilog-2001 (IEEE 1364-2001) reserved keywords.
VERILOG_KEYWORDS: frozenset[str] = frozenset(
    {
        "always", "and", "assign", "automatic", "begin", "buf", "bufif0",
        "bufif1", "case", "casex", "casez", "cell", "cmos", "config",
        "deassign", "default", "defparam", "design", "disable", "edge",
        "else", "end", "endcase", "endconfig", "endfunction", "endgenerate",
        "endmodule", "endprimitive", "endspecify", "endtable", "endtask",
        "event", "for", "force", "forever", "fork", "function", "generate",
        "genvar", "highz0", "highz1", "if", "ifnone", "incdir", "include",
        "initial", "inout", "input", "instance", "integer", "join", "large",
        "liblist", "library", "localparam", "macromodule", "medium", "module",
        "nand", "negedge", "nmos", "nor", "noshowcancelled", "not", "notif0",
        "notif1", "or", "output", "parameter", "pmos", "posedge", "primitive",
        "pull0", "pull1", "pulldown", "pullup", "pulsestyle_onevent",
        "pulsestyle_ondetect", "rcmos", "real", "realtime", "reg", "release",
        "repeat", "rnmos", "rpmos", "rtran", "rtranif0", "rtranif1",
        "scalared", "showcancelled", "signed", "small", "specify", "specparam",
        "strong0", "strong1", "supply0", "supply1", "table", "task", "time",
        "tran", "tranif0", "tranif1", "tri", "tri0", "tri1", "triand", "trior",
        "trireg", "unsigned", "use", "uwire", "vectored", "wait", "wand",
        "weak0", "weak1", "while", "wire", "wor", "xnor", "xor",
    }
)

# SystemVerilog (IEEE 1800-2017) reserved keywords (superset of Verilog).
SV_KEYWORDS: frozenset[str] = VERILOG_KEYWORDS | frozenset(
    {
        "accept_on", "alias", "always_comb", "always_ff", "always_latch",
        "assert", "assume", "before", "bind", "bins", "binsof", "bit", "break",
        "byte", "chandle", "checker", "class", "clocking", "const", "constraint",
        "context", "continue", "cover", "covergroup", "coverpoint", "cross",
        "dist", "do", "endchecker", "endclass", "endclocking", "endgroup",
        "endinterface", "endpackage", "endprogram", "endproperty", "endsequence",
        "enum", "eventually", "expect", "export", "extends", "extern", "final",
        "first_match", "foreach", "forkjoin", "global", "iff", "ignore_bins",
        "illegal_bins", "implements", "implies", "import", "inside", "int",
        "interconnect", "interface", "intersect", "join_any", "join_none",
        "let", "local", "logic", "longint", "matches", "modport", "new",
        "nexttime", "null", "package", "packed", "priority", "program",
        "property", "protected", "pure", "rand", "randc", "randcase",
        "randsequence", "ref", "reject_on", "restrict", "return", "s_always",
        "s_eventually", "s_nexttime", "s_until", "s_until_with", "sequence",
        "shortint", "shortreal", "soft", "solve", "static", "string", "strong",
        "struct", "super", "sync_accept_on", "sync_reject_on", "tagged", "this",
        "throughout", "timeprecision", "timeunit", "type", "typedef", "union",
        "unique", "unique0", "until", "until_with", "untyped", "var", "virtual",
        "void", "wait_order", "weak", "wildcard", "with", "within",
    }
)

# Canonical IR identifier: lower_snake_case ASCII (design rule 5).
_IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Canonical parameter identifier: UPPER_SNAKE_CASE ASCII (design rule 5;
# params follow RTL convention, e.g. WIDTH, DEPTH).
_PARAM_IDENT_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class IRValidationError(Exception):
    """Raised when an IR ``Module`` violates one or more §6 rules.

    ``violations`` holds the sorted list of individual messages; ``str`` gives a
    single multi-line message enumerating them all.
    """

    def __init__(self, violations: list[str]) -> None:
        self.violations = sorted(violations)
        header = f"IR validation failed with {len(self.violations)} violation(s):"
        body = "\n".join(f"  - {v}" for v in self.violations)
        super().__init__(f"{header}\n{body}")


def _is_canonical_ident(name: str) -> bool:
    return bool(_IDENT_RE.match(name))


def _is_canonical_param_ident(name: str) -> bool:
    return bool(_PARAM_IDENT_RE.match(name))


def _iter_expr(e: Expr):
    """Yield ``e`` and all nested sub-expressions (pre-order)."""
    yield e
    if isinstance(e, UnaryOp):
        yield from _iter_expr(e.a)
    elif isinstance(e, BinOp):
        yield from _iter_expr(e.a)
        yield from _iter_expr(e.b)
    elif isinstance(e, Ternary):
        yield from _iter_expr(e.cond)
        yield from _iter_expr(e.then)
        yield from _iter_expr(e.else_)
    elif isinstance(e, Bit):
        yield from _iter_expr(e.target)
        yield from _iter_expr(e.index)
    elif isinstance(e, Slice):
        yield from _iter_expr(e.target)
        yield from _iter_expr(e.msb)
        yield from _iter_expr(e.lsb)
    elif isinstance(e, Concat):
        for p in e.parts:
            yield from _iter_expr(p)
    elif isinstance(e, Repl):
        yield from _iter_expr(e.count)
        yield from _iter_expr(e.value)
    elif isinstance(e, Const) and e.width is not None:
        yield from _iter_expr(e.width)
    # Ref, EnumRef, bare Const: leaves.


def _iter_stmts(stmts):
    """Yield every ``Stmt`` in a body, descending into ``If``/``Case``."""
    for s in stmts:
        yield s
        if isinstance(s, If):
            yield from _iter_stmts(s.then)
            for _cond, body in s.elifs:
                yield from _iter_stmts(body)
            if s.else_ is not None:
                yield from _iter_stmts(s.else_)
        elif isinstance(s, Case):
            for item in s.items:
                yield from _iter_stmts(item.body)
            if s.default is not None:
                yield from _iter_stmts(s.default)


def _stmt_exprs(s: Stmt):
    """Yield the top-level expressions directly referenced by a statement."""
    if isinstance(s, Assign):
        yield s.lhs
        yield s.rhs
    elif isinstance(s, If):
        yield s.cond
        for cond, _body in s.elifs:
            yield cond
    elif isinstance(s, Case):
        yield s.sel
        for item in s.items:
            yield from item.labels
    # Comment: no expressions.


def _lvalue_names(lhs: Expr):
    """Yield the base ``Ref`` names targeted by a valid lvalue (rule 4)."""
    if isinstance(lhs, Ref):
        yield lhs.name
    elif isinstance(lhs, (Bit, Slice)):
        yield from _lvalue_names(lhs.target)
    elif isinstance(lhs, Concat):
        for p in lhs.parts:
            yield from _lvalue_names(p)


def _is_valid_lvalue(lhs: Expr) -> bool:
    """``lhs`` restricted to Ref/Bit/Slice/Concat of those (IR_SPEC §3.2)."""
    if isinstance(lhs, Ref):
        return True
    if isinstance(lhs, (Bit, Slice)):
        return _is_valid_lvalue(lhs.target)
    if isinstance(lhs, Concat):
        return all(_is_valid_lvalue(p) for p in lhs.parts)
    return False


def validate(module: Module, extra_reserved: frozenset[str] = frozenset()) -> None:
    """Validate ``module`` against IR_SPEC §6. Raise :class:`IRValidationError`
    listing *all* violations, or return ``None`` if the module is valid.

    ``extra_reserved`` supplements the built-in SV+Verilog keyword sets for
    rule 7; the style engine passes post-transform keyword collisions here.
    """
    v: list[str] = []

    params = {p.name for p in module.params}
    ports = {p.name for p in module.ports}
    signals = {s.name for s in module.items if isinstance(s, Signal)}
    enums = {e.name for e in module.items if isinstance(e, EnumDecl)}
    enum_members = {
        e.name: set(e.members) for e in module.items if isinstance(e, EnumDecl)
    }
    memories = {m.name for m in module.items if isinstance(m, Memory)}
    genfors = [g for g in module.items if isinstance(g, GenFor)]
    genfor_labels = [g.label for g in genfors]
    genvars = {g.genvar for g in genfors}

    # A GenFor's items are validated in the *module* scope extended with that
    # loop's genvar (rule 8: Ref(genvar) resolves only inside its own items).
    # ``_effective_items`` flattens (item, enclosing_genfor) pairs so the
    # existing rule-2/3/4/5 loops see inside GenFor.items.
    def _effective_items():
        for item in module.items:
            if isinstance(item, GenFor):
                for inner in item.items:
                    yield inner, item
            else:
                yield item, None

    # --- Rule 1 (+11): identifiers valid + unique across the namespaces ------
    # Rule 11 joins Memory names and GenFor labels into the same duplicate set.
    seen: dict[str, int] = {}
    for name in (
        [p.name for p in module.params]
        + [p.name for p in module.ports]
        + [s.name for s in module.items if isinstance(s, Signal)]
        + [e.name for e in module.items if isinstance(e, EnumDecl)]
        + [m.name for m in module.items if isinstance(m, Memory)]
        + genfor_labels
    ):
        seen[name] = seen.get(name, 0) + 1
    for name, count in seen.items():
        if count > 1:
            v.append(f"[rule 1] duplicate declared name: {name!r}")
    for name in sorted(params):
        if not _is_canonical_param_ident(name):
            v.append(
                f"[rule 1] not a canonical UPPER_SNAKE_CASE parameter identifier: {name!r}"
            )
    for name in sorted(set(seen) - params):
        if not _is_canonical_ident(name):
            v.append(f"[rule 1] not a canonical lower_snake_case identifier: {name!r}")
    for g in genfors:
        if not _is_canonical_ident(g.genvar):
            v.append(
                f"[rule 1] genvar not a canonical lower_snake_case identifier: "
                f"{g.genvar!r}"
            )
    if not _is_canonical_ident(module.name):
        v.append(f"[rule 1] module name not a canonical identifier: {module.name!r}")
    # Enum member names must also be canonical identifiers.
    for edecl in (e for e in module.items if isinstance(e, EnumDecl)):
        for mem in edecl.members:
            if not _is_canonical_ident(mem):
                v.append(
                    f"[rule 1] enum {edecl.name!r} member not a canonical "
                    f"identifier: {mem!r}"
                )

    # Names a Ref may resolve to (rule 2). Memory names are deliberately absent:
    # a memory is referenceable only as a ``Bit`` target (rule 9), never as a
    # bare ``Ref``. Genvars are added per-GenFor scope below.
    resolvable = params | ports | signals

    # ``Bit`` targets whose base is a memory are allowed (element select). We
    # track the exact ``Ref`` node ids that appear as a memory ``Bit.target`` so
    # the generic rule-2 walk can skip them (they are validated by rule 9).
    def _mem_select_ref_ids(top: Expr) -> set[int]:
        """ids of ``Ref(mem)`` nodes that are a memory ``Bit`` target within
        ``top`` — these are legal element selects, not whole-array refs."""
        found: set[int] = set()
        for sub in _iter_expr(top):
            if (
                isinstance(sub, Bit)
                and isinstance(sub.target, Ref)
                and sub.target.name in memories
            ):
                found.add(id(sub.target))
        return found

    # --- gather all statement bodies from procedural items ------------------
    # Each entry pairs a Stmt with the genvar in scope (None at module level).
    all_procedural_stmts: list[Stmt] = []
    scoped_procedural_stmts: list[tuple[Stmt, str | None]] = []
    for item, gf in _effective_items():
        gv = gf.genvar if gf is not None else None
        if isinstance(item, AlwaysFF):
            for s in list(_iter_stmts(item.reset_body)) + list(_iter_stmts(item.body)):
                all_procedural_stmts.append(s)
                scoped_procedural_stmts.append((s, gv))
        elif isinstance(item, AlwaysComb):
            for s in _iter_stmts(item.body):
                all_procedural_stmts.append(s)
                scoped_procedural_stmts.append((s, gv))

    # --- Rule 2: every Ref / EnumRef resolves -------------------------------
    def check_exprs(exprs, where: str, scope_genvar: str | None = None) -> None:
        # A genvar resolves only inside its own GenFor (rule 8). Other genvars
        # never resolve; a Ref(genvar) at module level also does not resolve.
        local = resolvable | ({scope_genvar} if scope_genvar else set())
        for top in exprs:
            skip = _mem_select_ref_ids(top)
            for sub in _iter_expr(top):
                if isinstance(sub, Ref):
                    if id(sub) in skip:
                        continue  # legal memory element select (rule 9)
                    if sub.name in memories:
                        v.append(
                            f"[rule 9] whole-array reference to memory "
                            f"{sub.name!r} in {where} (element-select only)"
                        )
                    elif sub.name in genvars and sub.name != scope_genvar:
                        v.append(
                            f"[rule 8] Ref to genvar {sub.name!r} outside its "
                            f"GenFor in {where}"
                        )
                    elif sub.name not in local:
                        v.append(
                            f"[rule 2] unresolved Ref {sub.name!r} in {where}"
                        )
                elif isinstance(sub, EnumRef):
                    if sub.enum not in enums:
                        v.append(
                            f"[rule 2] EnumRef to undeclared enum "
                            f"{sub.enum!r} in {where}"
                        )
                    elif sub.value not in enum_members[sub.enum]:
                        v.append(
                            f"[rule 2] EnumRef {sub.enum!r}.{sub.value!r} is "
                            f"not a member in {where}"
                        )

    for s, gv in scoped_procedural_stmts:
        check_exprs(_stmt_exprs(s), "procedural body", gv)
    for item, gf in _effective_items():
        gv = gf.genvar if gf is not None else None
        if isinstance(item, ContAssign):
            check_exprs([item.lhs, item.rhs], "continuous assign", gv)
        elif isinstance(item, Instance):
            check_exprs(
                [e for _n, e in item.params], f"instance {item.name!r} params", gv
            )
            check_exprs(
                [e for _n, e in item.conns], f"instance {item.name!r} conns", gv
            )

    # --- Rule 4: valid lvalues; input ports never driven --------------------
    input_ports = {p.name for p in module.ports if p.dir.value == "input"}

    def check_driven(lhs: Expr, where: str) -> None:
        if not _is_valid_lvalue(lhs):
            v.append(f"[rule 4] invalid lvalue in {where}: {lhs!r}")
            return
        for name in _lvalue_names(lhs):
            if name in input_ports:
                v.append(f"[rule 4] input port {name!r} is driven in {where}")

    for s in all_procedural_stmts:
        if isinstance(s, Assign):
            check_driven(s.lhs, "procedural assign")
    for item, _gf in _effective_items():
        if isinstance(item, ContAssign):
            check_driven(item.lhs, "continuous assign")

    # --- Rule 3: single-driver rule -----------------------------------------
    # Count each distinct driver of a base name. Multiple assigns within one
    # procedural block count once for that block.
    drivers: dict[str, list[str]] = {}

    def add_driver(name: str, source: str) -> None:
        drivers.setdefault(name, []).append(source)

    def _proc_targets(item) -> set[str]:
        block_stmts = (
            list(_iter_stmts(item.reset_body)) + list(_iter_stmts(item.body))
            if isinstance(item, AlwaysFF)
            else list(_iter_stmts(item.body))
        )
        targets: set[str] = set()
        for s in block_stmts:
            if isinstance(s, Assign):
                targets.update(_lvalue_names(s.lhs))
        return targets

    for idx, item in enumerate(module.items):
        if isinstance(item, (AlwaysFF, AlwaysComb)):
            for name in _proc_targets(item):
                add_driver(name, f"procedural block #{idx}")
        elif isinstance(item, ContAssign):
            for name in _lvalue_names(item.lhs):
                add_driver(name, f"ContAssign #{idx}")
        elif isinstance(item, GenFor):
            # Conservative: a GenFor replicates its body across iterations, so a
            # net driven inside counts as exactly ONE driver for the whole loop
            # (per-iteration these are distinct bit-slices, but the IR lacks the
            # width algebra to prove disjointness). If that same net is also
            # driven outside the loop, rule 3 rightly flags a conflict.
            gf_targets: set[str] = set()
            for inner in item.items:
                if isinstance(inner, (AlwaysFF, AlwaysComb)):
                    gf_targets.update(_proc_targets(inner))
                elif isinstance(inner, ContAssign):
                    gf_targets.update(_lvalue_names(inner.lhs))
            for name in gf_targets:
                add_driver(name, f"GenFor {item.label!r} #{idx}")
        elif isinstance(item, Instance):
            # Instance output connections drive their connected nets. We cannot
            # know port directions of the instantiated module here, so any Ref
            # connected is treated as potentially driven only if it is an
            # lvalue-shaped simple net — conservatively skip (no false errors).
            pass

    for name in sorted(drivers):
        srcs = drivers[name]
        if len(srcs) > 1:
            v.append(
                f"[rule 3] signal {name!r} has multiple drivers: "
                f"{', '.join(sorted(srcs))}"
            )

    # --- Rule 5: case coverage ----------------------------------------------
    for s in all_procedural_stmts:
        if isinstance(s, Case):
            if s.default is not None:
                continue
            # No default: must be an enum case covering all members.
            labels = [
                lbl
                for item in s.items
                for lbl in item.labels
            ]
            if labels and all(isinstance(lbl, EnumRef) for lbl in labels):
                enum_name = labels[0].enum
                covered = {lbl.value for lbl in labels}
                declared = enum_members.get(enum_name, set())
                same_enum = all(lbl.enum == enum_name for lbl in labels)
                if not same_enum:
                    v.append(
                        "[rule 5] enum Case mixes members from different "
                        "enums and has no default"
                    )
                elif enum_name not in enums:
                    v.append(
                        f"[rule 5] enum Case over undeclared enum "
                        f"{enum_name!r} and has no default"
                    )
                elif covered != declared:
                    missing = sorted(declared - covered)
                    v.append(
                        f"[rule 5] enum Case over {enum_name!r} missing "
                        f"member(s) {missing} and has no default"
                    )
            else:
                v.append(
                    "[rule 5] non-enum Case (or empty) without a default"
                )

    # --- Rule 6: reset=None implies empty reset_body ------------------------
    for idx, item in enumerate(module.items):
        if isinstance(item, AlwaysFF) and item.reset is None and item.reset_body:
            v.append(
                f"[rule 6] AlwaysFF #{idx} has reset=None but a non-empty "
                f"reset_body"
            )

    # --- Rule 8: GenFor genvar shadowing + item member types ----------------
    declared_names = params | ports | signals | enums | memories
    for g in genfors:
        if g.genvar in declared_names:
            v.append(
                f"[rule 8] genvar {g.genvar!r} of GenFor {g.label!r} shadows a "
                f"declared name"
            )
        for inner in g.items:
            if not isinstance(inner, _GENFOR_ITEM_TYPES):
                v.append(
                    f"[rule 8] GenFor {g.label!r} contains a disallowed item "
                    f"type {type(inner).__name__!r} (allowed: ContAssign, "
                    f"Instance, AlwaysFF, AlwaysComb, Comment)"
                )
    # Duplicate genvars across GenFors are also a shadow-ish hazard: two loops
    # using the same genvar name are independent in SV (block-scoped), but the
    # rule-2 scoping above cannot tell them apart, so forbid it.
    seen_genvars: set[str] = set()
    for g in genfors:
        if g.genvar in seen_genvars:
            v.append(
                f"[rule 8] genvar {g.genvar!r} reused across GenFor blocks"
            )
        seen_genvars.add(g.genvar)

    # --- Rule 9: Memory access discipline -----------------------------------
    # Whole-array refs / array-dim slices are caught in the rule-2 walk (bare
    # Ref(mem)) and here (Slice on Ref(mem)). Writes: only procedural Assign
    # lhs whose base is a memory, and only inside AlwaysFF. ContAssign lhs to a
    # memory element is forbidden.
    def _mem_slice_violations(top: Expr, where: str) -> None:
        for sub in _iter_expr(top):
            if (
                isinstance(sub, Slice)
                and isinstance(sub.target, Ref)
                and sub.target.name in memories
            ):
                v.append(
                    f"[rule 9] slice on memory array dimension {sub.target.name!r} "
                    f"in {where} (element-select only)"
                )

    def _lhs_mem_base(lhs: Expr) -> str | None:
        """The memory name written by ``lhs`` via a ``Bit`` select, else None."""
        if isinstance(lhs, Bit) and isinstance(lhs.target, Ref):
            if lhs.target.name in memories:
                return lhs.target.name
        return None

    # Memory writes must occur only in AlwaysFF; not AlwaysComb, not ContAssign.
    for item, _gf in _effective_items():
        if isinstance(item, AlwaysComb):
            for s in _iter_stmts(item.body):
                if isinstance(s, Assign) and _lhs_mem_base(s.lhs) is not None:
                    v.append(
                        f"[rule 9] memory {_lhs_mem_base(s.lhs)!r} written in "
                        f"AlwaysComb (synchronous write in AlwaysFF only)"
                    )
        elif isinstance(item, ContAssign):
            base = _lhs_mem_base(item.lhs)
            if base is not None:
                v.append(
                    f"[rule 9] continuous assignment to memory element "
                    f"{base!r} (procedural AlwaysFF write only)"
                )
    # Array-dimension slices anywhere.
    for s in all_procedural_stmts:
        for e in _stmt_exprs(s):
            _mem_slice_violations(e, "procedural body")
    for item, _gf in _effective_items():
        if isinstance(item, ContAssign):
            _mem_slice_violations(item.lhs, "continuous assign")
            _mem_slice_violations(item.rhs, "continuous assign")

    # --- Rule 10: DataType.enum_type resolves; width must be None -----------
    def _check_dtype(dtype: DataType, where: str) -> None:
        if dtype.enum_type is None:
            return
        if dtype.enum_type not in enums:
            v.append(
                f"[rule 10] enum_type {dtype.enum_type!r} in {where} is not a "
                f"declared EnumDecl"
            )
        if dtype.width is not None:
            v.append(
                f"[rule 10] enum_type {dtype.enum_type!r} in {where} also sets "
                f"width (must be None — width comes from the enum layout)"
            )

    for p in module.ports:
        _check_dtype(p.dtype, f"port {p.name!r}")
    for item in module.items:
        if isinstance(item, Signal):
            _check_dtype(item.dtype, f"signal {item.name!r}")

    # --- Rule 7: reserved-word check ----------------------------------------
    reserved = SV_KEYWORDS | VERILOG_KEYWORDS | extra_reserved
    checked_names = (
        [module.name]
        + [p.name for p in module.params]
        + [p.name for p in module.ports]
        + [s.name for s in module.items if isinstance(s, Signal)]
        + [e.name for e in module.items if isinstance(e, EnumDecl)]
        + [m.name for m in module.items if isinstance(m, Memory)]
        + genfor_labels
        + list(genvars)
    )
    for edecl in (e for e in module.items if isinstance(e, EnumDecl)):
        checked_names.extend(edecl.members)
    for name in sorted(set(checked_names)):
        if name in reserved:
            v.append(f"[rule 7] name collides with a reserved word: {name!r}")

    if v:
        raise IRValidationError(v)
