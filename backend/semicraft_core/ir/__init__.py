"""Intermediate representation (IR) for generated RTL (IR_SPEC.md, WP-01).

Public API: node classes and enums (:mod:`.nodes`), builder helpers
(:mod:`.build`), and validation (:mod:`.validate`).
"""

from __future__ import annotations

from .build import IN, OUT, add, bit, const, sub, vec, width
from .nodes import (
    AlwaysComb,
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    Bit,
    Case,
    CaseItem,
    ClockEdge,
    ClockSpec,
    Comment,
    CommentLevel,
    Concat,
    Const,
    ConstBase,
    ContAssign,
    DataType,
    EnumDecl,
    EnumEncoding,
    EnumRef,
    Expr,
    Header,
    If,
    Instance,
    Module,
    ModuleItem,
    Param,
    Port,
    PortDir,
    Ref,
    Repl,
    ResetKind,
    ResetSpec,
    Signal,
    Slice,
    Stmt,
    Ternary,
    UnaryOp,
    UnaryOpKind,
)
from .validate import (
    SV_KEYWORDS,
    VERILOG_KEYWORDS,
    IRValidationError,
    validate,
)

__all__ = [
    # abstract bases
    "Expr",
    "Stmt",
    "ModuleItem",
    # expressions
    "Ref",
    "Const",
    "UnaryOp",
    "BinOp",
    "Ternary",
    "Bit",
    "Slice",
    "Concat",
    "Repl",
    "EnumRef",
    # statements
    "Assign",
    "If",
    "Case",
    "CaseItem",
    "Comment",
    # supporting specs
    "ClockSpec",
    "ResetSpec",
    "DataType",
    # module items
    "Module",
    "Header",
    "Param",
    "Port",
    "Signal",
    "EnumDecl",
    "ContAssign",
    "AlwaysFF",
    "AlwaysComb",
    "Instance",
    # enums
    "UnaryOpKind",
    "BinOpKind",
    "ConstBase",
    "PortDir",
    "ClockEdge",
    "ResetKind",
    "EnumEncoding",
    "CommentLevel",
    # builder helpers
    "IN",
    "OUT",
    "bit",
    "vec",
    "width",
    "const",
    "add",
    "sub",
    # validation
    "validate",
    "IRValidationError",
    "SV_KEYWORDS",
    "VERILOG_KEYWORDS",
]
