"""Shared rendering walker for both output languages (WP-02, render/base.py).

One tree walker owns everything language-neutral (IR_SPEC §7: "Both renderers
share one tree walker"):

- indentation and statement blocks (``begin``/``end`` on every block);
- expression rendering with full parenthesization of nested operator
  expressions; statement top level stays unparenthesized (IR_SPEC §3.1);
- comment filtering by the ``comment_verbosity`` style option (design rule 7);
- reset composition per IR_SPEC §4 — sensitivity list and the
  ``if (<rst-active>) RB else B`` skeleton are synthesized here, generators
  never hand-write them (design rule 4);
- assignment operator selection by context (design rule 3): ``<=`` inside
  ``AlwaysFF``, ``=`` inside ``AlwaysComb``, ``assign`` for ``ContAssign``;
- fragment mode (``include_wrapper=False``): declarations-as-comment block +
  processes + continuous assigns, no ``module``/``endmodule``;
- header banner rendering from the ``Header`` node (no timestamps).

Language subclasses (:mod:`.sv`, :mod:`.verilog`) override only the small
hook set at the bottom of :class:`BaseRenderer` — keywords, declaration
type keywords (``logic`` vs inferred ``reg``/``wire``), parameter keywords,
and enum declaration syntax (IR_SPEC §7 table).

Two expression contexts exist:

- *data context* (default): spaces around binary operators, unsized constants
  render as minimal-width binary literals (``Const(1)`` -> ``1'b1``, matching
  IR_SPEC §9), constants with a non-literal width expression compose a
  replication (``Const(0, width=Ref("WIDTH"))`` -> ``{WIDTH{1'b0}}``);
- *size context* (declaration ranges, indexes, slice bounds, replication
  counts, parameter values): compact spacing (``WIDTH-1``), unsized constants
  render as plain numbers (``parameter WIDTH = 8``).
"""

from __future__ import annotations

import textwrap
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager

from ..ir.nodes import (
    AlwaysComb,
    AlwaysFF,
    Assign,
    BinOp,
    Bit,
    Case,
    ClockEdge,
    Comment,
    CommentLevel,
    Concat,
    Const,
    ConstBase,
    ContAssign,
    EnumDecl,
    EnumEncoding,
    EnumRef,
    Expr,
    If,
    Instance,
    Module,
    Param,
    Port,
    Ref,
    Repl,
    ResetKind,
    ResetSpec,
    Signal,
    Slice,
    Stmt,
    Ternary,
    UnaryOp,
)
from ..license import DISCLAIMER
from .style import StyleOptions, build_name_map

# Wrap width for the header disclaimer text ("// " prefix keeps lines < 80).
_WRAP_WIDTH = 74

# Operator expressions get parenthesized when nested as operands; everything
# else is self-delimiting.
_OPERATOR_EXPRS = (BinOp, UnaryOp, Ternary)


def _iter_stmts(stmts: Iterable[Stmt]) -> Iterator[Stmt]:
    """Yield every statement in ``stmts``, descending into ``If``/``Case``."""
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


def _lvalue_names(lhs: Expr) -> Iterator[str]:
    """Yield the base names targeted by a (valid) lvalue expression."""
    if isinstance(lhs, Ref):
        yield lhs.name
    elif isinstance(lhs, (Bit, Slice)):
        yield from _lvalue_names(lhs.target)
    elif isinstance(lhs, Concat):
        for p in lhs.parts:
            yield from _lvalue_names(p)


def procedural_targets(module: Module) -> frozenset[str]:
    """Names assigned inside any procedural block (reg/wire inference, rule 6)."""
    driven: set[str] = set()
    for item in module.items:
        if isinstance(item, AlwaysFF):
            stmts: list[Stmt] = list(_iter_stmts(item.reset_body))
            stmts += list(_iter_stmts(item.body))
        elif isinstance(item, AlwaysComb):
            stmts = list(_iter_stmts(item.body))
        else:
            continue
        for s in stmts:
            if isinstance(s, Assign):
                driven.update(_lvalue_names(s.lhs))
    return frozenset(driven)


def enum_layout(decl: EnumDecl) -> tuple[int, tuple[int, ...]]:
    """Compute (vector width, per-member values) for the declared encoding."""
    n = len(decl.members)
    if decl.encoding is EnumEncoding.ONEHOT:
        return n, tuple(1 << i for i in range(n))
    w = max(1, (n - 1).bit_length())
    if decl.encoding is EnumEncoding.GRAY:
        return w, tuple(i ^ (i >> 1) for i in range(n))
    return w, tuple(range(n))


class BaseRenderer:
    """Language-neutral IR-to-text walker; see module docstring."""

    language: str = ""
    #: ``True`` -> ``Case.unique`` renders a ``unique case`` keyword; ``False``
    #: -> plain ``case`` plus a verbose-level intent comment (IR_SPEC §3.2).
    supports_unique_case: bool = False
    #: Assignment operators by context (design rule 3). Same in both languages.
    FF_ASSIGN_OP = "<="
    COMB_ASSIGN_OP = "="

    def __init__(self, module: Module, style: StyleOptions) -> None:
        self.module = module
        self.style = style
        self.names = build_name_map(module, style)
        self.procedural = procedural_targets(module)
        self._lines: list[str] = []
        self._level = 0

    # ------------------------------------------------------------------ #
    # public entry point
    # ------------------------------------------------------------------ #

    def render(self, include_wrapper: bool = True) -> str:
        self._lines = []
        self._level = 0
        self._emit_banner()
        self._blank()
        if include_wrapper:
            self._emit_module_open()
            self._blank()
            with self._indented():
                self._emit_items(self._body_items())
            self._blank()
            self._emit("endmodule")
        else:
            self._emit_fragment_decls()
            self._blank()
            self._emit_items(self._fragment_items())
        return "\n".join(self._lines) + "\n"

    # ------------------------------------------------------------------ #
    # low-level emission
    # ------------------------------------------------------------------ #

    def _emit(self, text: str = "") -> None:
        if text:
            self._lines.append(" " * (self.style.indent * self._level) + text)
        else:
            self._lines.append("")

    def _blank(self) -> None:
        if self._lines and self._lines[-1] != "":
            self._lines.append("")

    @contextmanager
    def _indented(self) -> Iterator[None]:
        self._level += 1
        try:
            yield
        finally:
            self._level -= 1

    def name(self, canonical: str) -> str:
        """Resolve a canonical IR name through the style name map."""
        return self.names.get(canonical, canonical)

    # ------------------------------------------------------------------ #
    # comment filtering (design rule 7)
    # ------------------------------------------------------------------ #

    def _comment_visible(self, level: CommentLevel) -> bool:
        v = self.style.comment_verbosity
        if v == "none":
            return False
        if v == "verbose":
            return True
        return level is CommentLevel.NORMAL

    def _docs_visible(self) -> bool:
        """Port/signal ``doc`` inline comments are suppressed only at ``none``."""
        return self.style.comment_verbosity != "none"

    # ------------------------------------------------------------------ #
    # expressions
    # ------------------------------------------------------------------ #

    def _expr(self, e: Expr) -> str:
        """Data-context rendering. Nested operator operands are parenthesized;
        the returned string itself carries no outer parentheses (statement top
        level stays unparenthesized, IR_SPEC §3.1)."""
        if isinstance(e, Ref):
            return self.name(e.name)
        if isinstance(e, EnumRef):
            return self.name(e.value)
        if isinstance(e, Const):
            return self._const_data(e)
        if isinstance(e, UnaryOp):
            return f"{e.op}{self._operand(e.a)}"
        if isinstance(e, BinOp):
            return f"{self._operand(e.a)} {e.op} {self._operand(e.b)}"
        if isinstance(e, Ternary):
            return (
                f"{self._operand(e.cond)} ? {self._operand(e.then)}"
                f" : {self._operand(e.else_)}"
            )
        if isinstance(e, Bit):
            return f"{self._operand(e.target)}[{self._cexpr(e.index)}]"
        if isinstance(e, Slice):
            return (
                f"{self._operand(e.target)}"
                f"[{self._cexpr(e.msb)}:{self._cexpr(e.lsb)}]"
            )
        if isinstance(e, Concat):
            return "{" + ", ".join(self._operand(p) for p in e.parts) + "}"
        if isinstance(e, Repl):
            return "{" + self._coperand(e.count) + "{" + self._operand(e.value) + "}}"
        raise TypeError(f"unrenderable expression node: {e!r}")

    def _operand(self, e: Expr) -> str:
        s = self._expr(e)
        return f"({s})" if isinstance(e, _OPERATOR_EXPRS) else s

    def _cexpr(self, e: Expr) -> str:
        """Size-context rendering: compact operators, plain unsized numbers."""
        if isinstance(e, Const):
            if e.width is not None:
                return self._const_data(e)
            if e.base is ConstBase.HEX:
                return f"'h{e.value:X}"
            if e.base is ConstBase.BIN:
                return f"'b{e.value:b}"
            return str(e.value)
        if isinstance(e, Ref):
            return self.name(e.name)
        if isinstance(e, EnumRef):
            return self.name(e.value)
        if isinstance(e, BinOp):
            return f"{self._coperand(e.a)}{e.op}{self._coperand(e.b)}"
        if isinstance(e, UnaryOp):
            return f"{e.op}{self._coperand(e.a)}"
        return self._expr(e)

    def _coperand(self, e: Expr) -> str:
        s = self._cexpr(e)
        return f"({s})" if isinstance(e, _OPERATOR_EXPRS) else s

    def _const_data(self, c: Const) -> str:
        if c.width is None:
            if c.value < 0:
                return str(c.value)
            w = max(1, c.value.bit_length())
            return f"{w}'b{c.value:b}"
        if isinstance(c.width, Const) and c.width.width is None:
            w = c.width.value
            sign = "s" if c.signed else ""
            if c.base is ConstBase.HEX:
                return f"{w}'{sign}h{c.value:X}"
            if c.base is ConstBase.BIN:
                return f"{w}'{sign}b{c.value:b}"
            return f"{w}'{sign}d{c.value}"
        # Parameterized width: Verilog-2001 has no sized-literal syntax for a
        # non-literal width, so compose from replication (IR_SPEC §9 renders
        # Const(0, width=Ref("WIDTH")) as {WIDTH{1'b0}}).
        wexpr = self._coperand(c.width)
        if c.value == 0:
            return "{" + wexpr + "{1'b0}}"
        k = max(1, c.value.bit_length())
        pad = "{(" + wexpr + f"-{k})" + "{1'b0}}"
        return "{" + pad + f", {k}'b{c.value:b}" + "}"

    def _range(self, width: Expr | None) -> str:
        """``[MSB:0]`` packed range for a ``DataType``/declaration width."""
        if width is None:
            return ""
        if isinstance(width, Const) and width.width is None and width.base is ConstBase.DEC:
            return f"[{width.value - 1}:0]"
        return f"[{self._coperand(width)}-1:0]"

    # ------------------------------------------------------------------ #
    # statements
    # ------------------------------------------------------------------ #

    def _stmts(self, stmts: Sequence[Stmt], op: str) -> None:
        for s in stmts:
            self._stmt(s, op)

    def _stmt(self, s: Stmt, op: str) -> None:
        if isinstance(s, Comment):
            if self._comment_visible(s.level):
                self._emit(f"// {s.text}")
        elif isinstance(s, Assign):
            self._emit(f"{self._expr(s.lhs)} {op} {self._expr(s.rhs)};")
        elif isinstance(s, If):
            self._if(s, op)
        elif isinstance(s, Case):
            self._case(s, op)
        else:
            raise TypeError(f"unrenderable statement node: {s!r}")

    def _if(self, s: If, op: str) -> None:
        self._emit(f"if ({self._expr(s.cond)}) begin")
        with self._indented():
            self._stmts(s.then, op)
        for cond, body in s.elifs:
            self._emit(f"end else if ({self._expr(cond)}) begin")
            with self._indented():
                self._stmts(body, op)
        if s.else_ is not None:
            self._emit("end else begin")
            with self._indented():
                self._stmts(s.else_, op)
        self._emit("end")

    def _case(self, s: Case, op: str) -> None:
        if (
            s.unique
            and not self.supports_unique_case
            and self._comment_visible(CommentLevel.VERBOSE)
        ):
            # Verilog has no `unique case`; note the intent (IR_SPEC §3.2).
            self._emit("// unique case intent: labels are mutually exclusive")
        self._emit(f"{self.case_keyword(s.unique)} ({self._expr(s.sel)})")
        with self._indented():
            for item in s.items:
                label = ", ".join(self._expr(lbl) for lbl in item.labels)
                self._case_arm(label, item.body, op)
            if s.default is not None:
                self._case_arm("default", s.default, op)
        self._emit("endcase")

    def _case_arm(self, label: str, body: Sequence[Stmt], op: str) -> None:
        visible = [
            st
            for st in body
            if not (isinstance(st, Comment) and not self._comment_visible(st.level))
        ]
        if not visible:
            self._emit(f"{label}: ;")
        elif len(visible) == 1 and isinstance(visible[0], Assign):
            a = visible[0]
            self._emit(f"{label}: {self._expr(a.lhs)} {op} {self._expr(a.rhs)};")
        else:
            self._emit(f"{label}: begin")
            with self._indented():
                self._stmts(body, op)
            self._emit("end")

    # ------------------------------------------------------------------ #
    # processes: reset composition lives here (IR_SPEC §4)
    # ------------------------------------------------------------------ #

    def _sensitivity(self, ff: AlwaysFF) -> str:
        edge = "posedge" if ff.clock.edge is ClockEdge.POS else "negedge"
        sens = f"{edge} {self.name(ff.clock.name)}"
        r = ff.reset
        if r is not None and r.kind is ResetKind.ASYNC:
            reset_edge = "negedge" if r.active_low else "posedge"
            sens += f" or {reset_edge} {self.name(r.name)}"
        return sens

    def _reset_condition(self, r: ResetSpec) -> str:
        rendered = self.name(r.name)
        return f"!{rendered}" if r.active_low else rendered

    def _emit_always_ff(self, ff: AlwaysFF) -> None:
        self._emit(self.always_ff_open(self._sensitivity(ff)))
        with self._indented():
            if ff.reset is None:
                self._stmts(ff.body, self.FF_ASSIGN_OP)
            else:
                self._emit(f"if ({self._reset_condition(ff.reset)}) begin")
                with self._indented():
                    self._stmts(ff.reset_body, self.FF_ASSIGN_OP)
                self._emit("end else begin")
                with self._indented():
                    self._stmts(ff.body, self.FF_ASSIGN_OP)
                self._emit("end")
        self._emit("end")

    def _emit_always_comb(self, blk: AlwaysComb) -> None:
        self._emit(self.always_comb_open())
        with self._indented():
            self._stmts(blk.body, self.COMB_ASSIGN_OP)
        self._emit("end")

    def _emit_cont_assign(self, ca: ContAssign) -> None:
        self._emit(f"assign {self._expr(ca.lhs)} = {self._expr(ca.rhs)};")

    def _emit_instance(self, inst: Instance) -> None:
        params = inst.params_dict
        conns = inst.conns_dict
        if params:
            self._emit(f"{inst.module} #(")
            with self._indented():
                keys = sorted(params)
                for i, k in enumerate(keys):
                    comma = "," if i < len(keys) - 1 else ""
                    self._emit(f".{k}({self._cexpr(params[k])}){comma}")
            self._emit(f") {self.name(inst.name)} (")
        else:
            self._emit(f"{inst.module} {self.name(inst.name)} (")
        with self._indented():
            keys = sorted(conns)
            for i, k in enumerate(keys):
                comma = "," if i < len(keys) - 1 else ""
                self._emit(f".{k}({self._expr(conns[k])}){comma}")
        self._emit(");")

    # ------------------------------------------------------------------ #
    # declarations
    # ------------------------------------------------------------------ #

    def _signal_decl(self, sig: Signal) -> str:
        kind = self.signal_kind(sig)
        signed = " signed" if sig.dtype.signed else ""
        rng = self._range(sig.dtype.width)
        decl = kind + signed + (f" {rng}" if rng else "") + f" {self.name(sig.name)};"
        if sig.doc and self._docs_visible():
            decl += f"  // {sig.doc}"
        return decl

    def _param_decl(self, p: Param, *, trailing: str = ";") -> str:
        return f"{self.param_keyword(local=p.local)} {p.name} = {self._cexpr(p.default)}{trailing}"

    # ------------------------------------------------------------------ #
    # module wrapper
    # ------------------------------------------------------------------ #

    def _emit_banner(self) -> None:
        h = self.module.header
        self._emit(f"// SemiCraft v{h.tool_version}")
        self._emit(f"// Snippet: {self.module.name} (config hash: {h.config_hash})")
        if h.description:
            self._emit(f"// {h.description}")
        self._emit("//")
        for line in textwrap.wrap(h.license or DISCLAIMER, width=_WRAP_WIDTH):
            self._emit(f"// {line}")

    def _emit_module_open(self) -> None:
        public_params = [p for p in self.module.params if not p.local]
        has_ports = bool(self.module.ports)
        if public_params:
            self._emit(f"module {self.module.name} #(")
            with self._indented():
                for i, p in enumerate(public_params):
                    comma = "," if i < len(public_params) - 1 else ""
                    self._emit(self._param_decl(p, trailing=comma))
            self._emit(") (" if has_ports else ");")
        else:
            tail = " (" if has_ports else ";"
            self._emit(f"module {self.module.name}{tail}")
        if has_ports:
            self._emit_ports()
            self._emit(");")

    def _port_rows(self) -> list[tuple[str, str, str, str, str]]:
        """(direction, kind, range, rendered name, doc) per port."""
        rows: list[tuple[str, str, str, str, str]] = []
        for p in self.module.ports:
            kind = self.port_kind(p) + (" signed" if p.dtype.signed else "")
            rows.append(
                (p.dir.value, kind, self._range(p.dtype.width), self.name(p.name), p.doc)
            )
        return rows

    def _emit_ports(self) -> None:
        """ANSI ports, column-aligned as in IR_SPEC §9 / STYLE_GUIDE §4."""
        rows = self._port_rows()
        dir_w = max(len(r[0]) for r in rows)
        kind_w = max(len(r[1]) for r in rows)
        types = [r[1].ljust(kind_w) + (f" {r[2]}" if r[2] else "") for r in rows]
        type_w = max(len(t) for t in types)
        names = [r[3] + ("," if i < len(rows) - 1 else "") for i, r in enumerate(rows)]
        name_w = max(len(n) for n in names)
        with self._indented():
            for (d, _kind, _rng, _name, doc), typ, nm in zip(rows, types, names, strict=True):
                if doc and self._docs_visible():
                    line = f"{d.ljust(dir_w)} {typ.ljust(type_w)} {nm.ljust(name_w)}   // {doc}"
                else:
                    line = f"{d.ljust(dir_w)} {typ.ljust(type_w)} {nm}"
                self._emit(line)

    # ------------------------------------------------------------------ #
    # body layout
    # ------------------------------------------------------------------ #

    #: Single-line declaration-ish items; consecutive ones stay contiguous,
    #: everything else is separated by a blank line (STYLE_GUIDE §6).
    _INLINE_ITEMS = (Signal, Param, Comment)

    def _body_items(self) -> list[object]:
        # local params render inside the body, before the remaining items.
        items: list[object] = [p for p in self.module.params if p.local]
        items += list(self.module.items)
        return [
            it
            for it in items
            if not (isinstance(it, Comment) and not self._comment_visible(it.level))
        ]

    def _fragment_items(self) -> list[object]:
        return [
            it
            for it in self._body_items()
            if isinstance(it, (ContAssign, AlwaysFF, AlwaysComb, Instance, Comment))
        ]

    def _emit_items(self, items: list[object]) -> None:
        prev: object | None = None
        for it in items:
            if prev is not None:
                prev_inline = isinstance(prev, self._INLINE_ITEMS)
                cur_inline = isinstance(it, self._INLINE_ITEMS)
                # Comments attach to the following item; declaration lines
                # group together; blocks get blank-line separation.
                if not (prev_inline and cur_inline) and not isinstance(prev, Comment):
                    self._blank()
            self._emit_item(it)
            prev = it

    def _emit_item(self, it: object) -> None:
        if isinstance(it, Param):
            self._emit(self._param_decl(it))
        elif isinstance(it, Signal):
            self._emit(self._signal_decl(it))
        elif isinstance(it, Comment):
            self._emit(f"// {it.text}")
        elif isinstance(it, EnumDecl):
            self._emit_enum_decl(it)
        elif isinstance(it, ContAssign):
            self._emit_cont_assign(it)
        elif isinstance(it, AlwaysFF):
            self._emit_always_ff(it)
        elif isinstance(it, AlwaysComb):
            self._emit_always_comb(it)
        elif isinstance(it, Instance):
            self._emit_instance(it)
        else:
            raise TypeError(f"unrenderable module item: {it!r}")

    # ------------------------------------------------------------------ #
    # fragment mode
    # ------------------------------------------------------------------ #

    def _emit_fragment_decls(self) -> None:
        self._emit("// Fragment mode: no module wrapper is emitted. The enclosing")
        self._emit("// module must provide the following declarations:")
        for p in self.module.params:
            self._emit(f"//     {self._param_decl(p)}")
        rows = self._port_rows()
        if rows:
            dir_w = max(len(r[0]) for r in rows)
            for d, kind, rng, nm, _doc in rows:
                typ = kind + (f" {rng}" if rng else "")
                self._emit(f"//     {d.ljust(dir_w)} {typ} {nm};")
        for it in self.module.items:
            if isinstance(it, Signal):
                self._emit(f"//     {self._signal_decl(it)}")
            elif isinstance(it, EnumDecl):
                start = len(self._lines)
                self._emit_enum_decl(it)
                self._lines[start:] = [f"//     {ln}" for ln in self._lines[start:]]

    # ------------------------------------------------------------------ #
    # language hooks (IR_SPEC §7 table) — subclasses must override
    # ------------------------------------------------------------------ #

    def always_ff_open(self, sensitivity: str) -> str:
        raise NotImplementedError

    def always_comb_open(self) -> str:
        raise NotImplementedError

    def case_keyword(self, unique: bool) -> str:
        raise NotImplementedError

    def param_keyword(self, *, local: bool) -> str:
        raise NotImplementedError

    def port_kind(self, port: Port) -> str:
        raise NotImplementedError

    def signal_kind(self, sig: Signal) -> str:
        raise NotImplementedError

    def _emit_enum_decl(self, decl: EnumDecl) -> None:
        raise NotImplementedError


__all__ = [
    "BaseRenderer",
    "enum_layout",
    "procedural_targets",
]
