"""Pre-render IR validation (IR_SPEC §6).

``validate(module)`` runs before any rendering. Errors here are *generator*
bugs, not user errors: they fail loudly (raise :class:`IRValidationError`) and,
per the API contract, map to HTTP 500 rather than silently degrading.

The raised error lists **all** violations found, not just the first, so a
generator author sees the full picture in one run. Violation messages are
sorted before joining so the message is deterministic regardless of dict or
set iteration order (ground rule: determinism).

Implements all seven §6 rules:

1. Valid canonical identifiers; no duplicates among params/ports/signals/enums.
2. Every ``Ref``/``EnumRef`` resolves to a declared name.
3. Single-driver rule for each driven signal.
4. ``Assign.lhs`` is a valid lvalue; ``input`` ports are never driven.
5. ``Case`` covers all enum members or has a ``default``; non-enum needs default.
6. ``AlwaysFF`` with ``reset=None`` has empty ``reset_body``.
7. Post-style reserved-word check (SV and Verilog keyword sets).
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
    Concat,
    Const,
    ContAssign,
    EnumDecl,
    EnumRef,
    Expr,
    If,
    Instance,
    Module,
    Ref,
    Repl,
    Signal,
    Slice,
    Stmt,
    Ternary,
    UnaryOp,
)

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

    # --- Rule 1: identifiers valid + unique across the four namespaces -------
    seen: dict[str, int] = {}
    for name in (
        [p.name for p in module.params]
        + [p.name for p in module.ports]
        + [s.name for s in module.items if isinstance(s, Signal)]
        + [e.name for e in module.items if isinstance(e, EnumDecl)]
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

    # Names a Ref may resolve to (rule 2).
    resolvable = params | ports | signals

    # --- gather all statement bodies from procedural items ------------------
    all_procedural_stmts: list[Stmt] = []
    for item in module.items:
        if isinstance(item, AlwaysFF):
            all_procedural_stmts.extend(_iter_stmts(item.reset_body))
            all_procedural_stmts.extend(_iter_stmts(item.body))
        elif isinstance(item, AlwaysComb):
            all_procedural_stmts.extend(_iter_stmts(item.body))

    # --- Rule 2: every Ref / EnumRef resolves -------------------------------
    def check_exprs(exprs, where: str) -> None:
        for top in exprs:
            for sub in _iter_expr(top):
                if isinstance(sub, Ref) and sub.name not in resolvable:
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

    for s in all_procedural_stmts:
        check_exprs(_stmt_exprs(s), "procedural body")
    for item in module.items:
        if isinstance(item, ContAssign):
            check_exprs([item.lhs, item.rhs], "continuous assign")
        elif isinstance(item, Instance):
            check_exprs([e for _n, e in item.params], f"instance {item.name!r} params")
            check_exprs([e for _n, e in item.conns], f"instance {item.name!r} conns")

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
    for item in module.items:
        if isinstance(item, ContAssign):
            check_driven(item.lhs, "continuous assign")

    # --- Rule 3: single-driver rule -----------------------------------------
    # Count each distinct driver of a base name. Multiple assigns within one
    # procedural block count once for that block.
    drivers: dict[str, list[str]] = {}

    def add_driver(name: str, source: str) -> None:
        drivers.setdefault(name, []).append(source)

    for idx, item in enumerate(module.items):
        if isinstance(item, (AlwaysFF, AlwaysComb)):
            block_stmts = (
                list(_iter_stmts(item.reset_body)) + list(_iter_stmts(item.body))
                if isinstance(item, AlwaysFF)
                else list(_iter_stmts(item.body))
            )
            block_targets: set[str] = set()
            for s in block_stmts:
                if isinstance(s, Assign):
                    block_targets.update(_lvalue_names(s.lhs))
            for name in block_targets:
                add_driver(name, f"procedural block #{idx}")
        elif isinstance(item, ContAssign):
            for name in _lvalue_names(item.lhs):
                add_driver(name, f"ContAssign #{idx}")
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

    # --- Rule 7: reserved-word check ----------------------------------------
    reserved = SV_KEYWORDS | VERILOG_KEYWORDS | extra_reserved
    checked_names = (
        [module.name]
        + [p.name for p in module.params]
        + [p.name for p in module.ports]
        + [s.name for s in module.items if isinstance(s, Signal)]
        + [e.name for e in module.items if isinstance(e, EnumDecl)]
    )
    for edecl in (e for e in module.items if isinstance(e, EnumDecl)):
        checked_names.extend(edecl.members)
    for name in sorted(set(checked_names)):
        if name in reserved:
            v.append(f"[rule 7] name collides with a reserved word: {name!r}")

    if v:
        raise IRValidationError(v)
