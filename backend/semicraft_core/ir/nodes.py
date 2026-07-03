"""IR node definitions for SemiCraft generated RTL.

All nodes are frozen, slotted dataclasses per IR_SPEC.md design rule 1
(immutable nodes) and §3 (node catalog). Field names and lists exactly
match IR_SPEC §3.1-§3.3; do not add or rename fields.

List-valued fields accept any ``Sequence`` at construction and are stored as
``tuple`` (via ``__post_init__`` + ``object.__setattr__``) so that nodes stay
hashable and immutable. Language decisions (reg/wire, blocking/non-blocking,
always_ff vs always) never appear here; they live in renderers (design rule 2).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class UnaryOpKind(StrEnum):
    """Unary operators (IR_SPEC §3.1). Last six are reductions."""

    NOT_BITWISE = "~"
    NEG = "-"
    NOT_LOGICAL = "!"
    RED_AND = "&"
    RED_OR = "|"
    RED_XOR = "^"
    RED_NAND = "~&"
    RED_NOR = "~|"
    RED_XNOR = "~^"


class BinOpKind(StrEnum):
    """Binary operators (IR_SPEC §3.1). No ``/`` or ``%`` in v0.1 (§8)."""

    ADD = "+"
    SUB = "-"
    MUL = "*"
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    SHL = "<<"
    SHR = ">>"
    ASHR = ">>>"
    AND = "&"
    OR = "|"
    XOR = "^"
    LAND = "&&"
    LOR = "||"


class ConstBase(StrEnum):
    """Literal radix for ``Const`` (IR_SPEC §3.1)."""

    DEC = "dec"
    HEX = "hex"
    BIN = "bin"


class PortDir(StrEnum):
    """Port direction (IR_SPEC §3.3). No ``inout`` in v0.1."""

    INPUT = "input"
    OUTPUT = "output"


class ClockEdge(StrEnum):
    """Clock edge for ``ClockSpec`` (IR_SPEC §3.3)."""

    POS = "pos"
    NEG = "neg"


class ResetKind(StrEnum):
    """Reset kind for ``ResetSpec`` (IR_SPEC §3.3 / §4)."""

    SYNC = "sync"
    ASYNC = "async"


class EnumEncoding(StrEnum):
    """FSM state encoding for ``EnumDecl`` (IR_SPEC §3.3 / §5)."""

    BINARY = "binary"
    ONEHOT = "onehot"
    GRAY = "gray"


class CommentLevel(StrEnum):
    """Verbosity level carried by a ``Comment`` node (IR_SPEC §3.2)."""

    NORMAL = "normal"
    VERBOSE = "verbose"


# ---------------------------------------------------------------------------
# Abstract bases
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Expr:
    """Abstract base for expression nodes (IR_SPEC §3.1)."""


@dataclass(frozen=True, slots=True)
class Stmt:
    """Abstract base for statement nodes (IR_SPEC §3.2)."""


@dataclass(frozen=True, slots=True)
class ModuleItem:
    """Marker base for module-level items (IR_SPEC §3.3)."""


# ---------------------------------------------------------------------------
# Expressions (IR_SPEC §3.1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Ref(Expr):
    """Reference to a signal, port, or param. Must resolve within the module."""

    name: str


@dataclass(frozen=True, slots=True)
class Const(Expr):
    """Integer literal. ``width=None`` -> unsized; sized renders as ``8'hFF``."""

    value: int
    width: Expr | None = None
    base: ConstBase = ConstBase.DEC
    signed: bool = False


@dataclass(frozen=True, slots=True)
class UnaryOp(Expr):
    """Unary operation ``op a`` (IR_SPEC §3.1)."""

    op: UnaryOpKind
    a: Expr


@dataclass(frozen=True, slots=True)
class BinOp(Expr):
    """Binary operation ``a op b`` (IR_SPEC §3.1)."""

    op: BinOpKind
    a: Expr
    b: Expr


@dataclass(frozen=True, slots=True)
class Ternary(Expr):
    """Conditional expression ``cond ? then : else_`` (IR_SPEC §3.1)."""

    cond: Expr
    then: Expr
    else_: Expr


@dataclass(frozen=True, slots=True)
class Bit(Expr):
    """Single-bit select ``target[index]`` (IR_SPEC §3.1)."""

    target: Expr
    index: Expr


@dataclass(frozen=True, slots=True)
class Slice(Expr):
    """Part-select ``target[msb:lsb]``; constant/param-derived bounds only."""

    target: Expr
    msb: Expr
    lsb: Expr


@dataclass(frozen=True, slots=True)
class Concat(Expr):
    """Concatenation ``{parts...}`` (IR_SPEC §3.1)."""

    parts: tuple[Expr, ...]

    def __init__(self, parts: Sequence[Expr]) -> None:
        object.__setattr__(self, "parts", tuple(parts))


@dataclass(frozen=True, slots=True)
class Repl(Expr):
    """Replication ``{count{value}}`` (IR_SPEC §3.1)."""

    count: Expr
    value: Expr


@dataclass(frozen=True, slots=True)
class EnumRef(Expr):
    """Reference to a declared enum member (FSM states) (IR_SPEC §3.1)."""

    enum: str
    value: str


# ---------------------------------------------------------------------------
# Statements (IR_SPEC §3.2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Assign(Stmt):
    """Assignment; operator inferred by context (design rule 3).

    ``lhs`` restricted to ``Ref``, ``Bit``, ``Slice``, or ``Concat`` of those.
    """

    lhs: Expr
    rhs: Expr


@dataclass(frozen=True, slots=True)
class If(Stmt):
    """Conditional statement with optional elif chain and else (IR_SPEC §3.2)."""

    cond: Expr
    then: tuple[Stmt, ...]
    elifs: tuple[tuple[Expr, tuple[Stmt, ...]], ...] = ()
    else_: tuple[Stmt, ...] | None = None

    def __init__(
        self,
        cond: Expr,
        then: Sequence[Stmt],
        elifs: Sequence[tuple[Expr, Sequence[Stmt]]] = (),
        else_: Sequence[Stmt] | None = None,
    ) -> None:
        object.__setattr__(self, "cond", cond)
        object.__setattr__(self, "then", tuple(then))
        object.__setattr__(
            self, "elifs", tuple((c, tuple(body)) for c, body in elifs)
        )
        object.__setattr__(
            self, "else_", None if else_ is None else tuple(else_)
        )


@dataclass(frozen=True, slots=True)
class CaseItem:
    """One arm of a ``Case``: ``labels`` matched to ``body`` (IR_SPEC §3.2)."""

    labels: tuple[Expr, ...]
    body: tuple[Stmt, ...]

    def __init__(self, labels: Sequence[Expr], body: Sequence[Stmt]) -> None:
        object.__setattr__(self, "labels", tuple(labels))
        object.__setattr__(self, "body", tuple(body))


@dataclass(frozen=True, slots=True)
class Case(Stmt):
    """Case statement over ``sel`` (IR_SPEC §3.2).

    ``default`` required unless the case is an enum case covering all members
    (validated, §6 rule 5). ``unique=True`` -> SV ``unique case``.
    """

    sel: Expr
    items: tuple[CaseItem, ...]
    default: tuple[Stmt, ...] | None = None
    unique: bool = False

    def __init__(
        self,
        sel: Expr,
        items: Sequence[CaseItem],
        default: Sequence[Stmt] | None = None,
        unique: bool = False,
    ) -> None:
        object.__setattr__(self, "sel", sel)
        object.__setattr__(self, "items", tuple(items))
        object.__setattr__(
            self, "default", None if default is None else tuple(default)
        )
        object.__setattr__(self, "unique", unique)


@dataclass(frozen=True, slots=True)
class Comment(Stmt):
    """Explanatory comment as data (design rule 7); filtered by style option."""

    text: str
    level: CommentLevel = CommentLevel.NORMAL


# ---------------------------------------------------------------------------
# Supporting specs (IR_SPEC §3.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ClockSpec:
    """Clock for an ``AlwaysFF`` (IR_SPEC §3.3)."""

    name: str = "clk"
    edge: ClockEdge = ClockEdge.POS


@dataclass(frozen=True, slots=True)
class ResetSpec:
    """Reset for an ``AlwaysFF`` (IR_SPEC §3.3 / §4).

    Canonical IR name is ``rst``; the style engine appends ``_n`` when
    ``active_low=True``.
    """

    name: str
    kind: ResetKind
    active_low: bool


@dataclass(frozen=True, slots=True)
class DataType:
    """Packed 1-D vector type. ``width=None`` -> 1-bit scalar (IR_SPEC §3.3)."""

    width: Expr | None = None
    signed: bool = False


# ---------------------------------------------------------------------------
# Module items (IR_SPEC §3.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Param(ModuleItem):
    """Module parameter. ``local=True`` -> ``localparam`` (IR_SPEC §3.3)."""

    name: str
    default: Expr
    local: bool = False
    doc: str = ""


@dataclass(frozen=True, slots=True)
class Port(ModuleItem):
    """Module port. No ``inout`` in v0.1 (IR_SPEC §3.3)."""

    name: str
    dir: PortDir
    dtype: DataType
    doc: str = ""


@dataclass(frozen=True, slots=True)
class Signal(ModuleItem):
    """Internal signal declaration; net/variable kind inferred (design rule 6)."""

    name: str
    dtype: DataType
    doc: str = ""


@dataclass(frozen=True, slots=True)
class EnumDecl(ModuleItem):
    """FSM state type declaration (IR_SPEC §3.3 / §5)."""

    name: str
    members: tuple[str, ...]
    encoding: EnumEncoding

    def __init__(
        self, name: str, members: Sequence[str], encoding: EnumEncoding
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "members", tuple(members))
        object.__setattr__(self, "encoding", encoding)


@dataclass(frozen=True, slots=True)
class ContAssign(ModuleItem):
    """Continuous assignment ``assign lhs = rhs;`` (IR_SPEC §3.3)."""

    lhs: Expr
    rhs: Expr


@dataclass(frozen=True, slots=True)
class AlwaysFF(ModuleItem):
    """Clocked process (IR_SPEC §3.3 / §4).

    ``reset=None`` -> no-reset register (then ``reset_body`` must be empty,
    §6 rule 6).
    """

    clock: ClockSpec
    reset: ResetSpec | None
    reset_body: tuple[Stmt, ...]
    body: tuple[Stmt, ...]

    def __init__(
        self,
        clock: ClockSpec,
        reset: ResetSpec | None,
        reset_body: Sequence[Stmt],
        body: Sequence[Stmt],
    ) -> None:
        object.__setattr__(self, "clock", clock)
        object.__setattr__(self, "reset", reset)
        object.__setattr__(self, "reset_body", tuple(reset_body))
        object.__setattr__(self, "body", tuple(body))


@dataclass(frozen=True, slots=True)
class AlwaysComb(ModuleItem):
    """Combinational process (IR_SPEC §3.3). SV ``always_comb`` / ``always @(*)``."""

    body: tuple[Stmt, ...]

    def __init__(self, body: Sequence[Stmt]) -> None:
        object.__setattr__(self, "body", tuple(body))


@dataclass(frozen=True, slots=True)
class Instance(ModuleItem):
    """Module instantiation with named connections (IR_SPEC §3.3).

    Spec §3.3 types ``params``/``conns`` as ``dict``; to keep the node frozen
    and hashable (design rule 1) they are stored as an immutable tuple of
    ``(name, expr)`` pairs. The constructor accepts any ``Mapping``; use
    ``.params_dict`` / ``.conns_dict`` to recover a plain dict for rendering.
    """

    module: str
    name: str
    params: tuple[tuple[str, Expr], ...]
    conns: tuple[tuple[str, Expr], ...]

    def __init__(
        self,
        module: str,
        name: str,
        params: Mapping[str, Expr],
        conns: Mapping[str, Expr],
    ) -> None:
        object.__setattr__(self, "module", module)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "params", tuple(dict(params).items()))
        object.__setattr__(self, "conns", tuple(dict(conns).items()))

    @property
    def params_dict(self) -> dict[str, Expr]:
        return dict(self.params)

    @property
    def conns_dict(self) -> dict[str, Expr]:
        return dict(self.conns)


@dataclass(frozen=True, slots=True)
class Header:
    """File banner comment source (IR_SPEC §3.3). No timestamps (determinism)."""

    license: str
    config_hash: str
    tool_version: str
    description: str


@dataclass(frozen=True, slots=True)
class Module:
    """Root node (IR_SPEC §3.3)."""

    name: str
    header: Header
    params: tuple[Param, ...] = ()
    ports: tuple[Port, ...] = ()
    items: tuple[ModuleItem, ...] = ()

    def __init__(
        self,
        name: str,
        header: Header,
        params: Sequence[Param] = (),
        ports: Sequence[Port] = (),
        items: Sequence[ModuleItem] = (),
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "header", header)
        object.__setattr__(self, "params", tuple(params))
        object.__setattr__(self, "ports", tuple(ports))
        object.__setattr__(self, "items", tuple(items))
