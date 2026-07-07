"""Ergonomic builder helpers for constructing IR trees (WP-01 task 2).

These make generator code read like the IR_SPEC §9 counter example. They are
thin wrappers over :mod:`semicraft_core.ir.nodes`; no semantics live here that
are not in the node catalog.
"""

from __future__ import annotations

from collections.abc import Sequence

from .nodes import (
    BinOp,
    BinOpKind,
    Const,
    ConstBase,
    DataType,
    Expr,
    GenFor,
    Memory,
    ModuleItem,
    PortDir,
    Ref,
)

# Port-direction constants, so ports read ``Port("clk", IN, bit())``.
IN = PortDir.INPUT
OUT = PortDir.OUTPUT


def width(n_or_name: int | str | Expr) -> Expr:
    """Build a width expression.

    - ``int`` -> ``Const(n)`` (an unsized decimal literal).
    - ``str`` -> ``Ref(name)`` (a parameter reference, e.g. ``"WIDTH"``).
    - ``Expr`` -> returned unchanged (e.g. ``BinOp("-", Ref("WIDTH"), Const(1))``).
    """
    if isinstance(n_or_name, Expr):
        return n_or_name
    if isinstance(n_or_name, bool):  # bool is an int subclass; reject explicitly
        raise TypeError("width() expects int, str, or Expr, not bool")
    if isinstance(n_or_name, int):
        return Const(n_or_name)
    if isinstance(n_or_name, str):
        return Ref(n_or_name)
    raise TypeError(f"width() expects int, str, or Expr, got {type(n_or_name)!r}")


def bit() -> DataType:
    """A 1-bit scalar data type (``width=None``)."""
    return DataType(width=None)


def vec(width_expr_or_name_or_int: int | str | Expr) -> DataType:
    """A packed 1-D vector data type of the given width.

    Accepts an int literal, a param name (``"WIDTH"``), or a width ``Expr``.
    """
    return DataType(width=width(width_expr_or_name_or_int))


# --- small expression factories -------------------------------------------


def const(value: int, *, w: int | str | Expr | None = None, base: ConstBase = ConstBase.DEC,
          signed: bool = False) -> Const:
    """Build a ``Const``; ``w`` sizes the literal (int/name/Expr) or ``None``."""
    return Const(value, width=None if w is None else width(w), base=base, signed=signed)


def add(a: Expr, b: Expr) -> BinOp:
    """``a + b``."""
    return BinOp(BinOpKind.ADD, a, b)


def sub(a: Expr, b: Expr) -> BinOp:
    """``a - b``."""
    return BinOp(BinOpKind.SUB, a, b)


# --- v0.2 module-item helpers (IR_SPEC §10) --------------------------------


def enum_t(name: str) -> DataType:
    """An enum-typed ``DataType`` (IR_SPEC §10.3); ``width`` stays ``None``."""
    return DataType(enum_type=name)


def mem(
    name: str,
    width: int | str | Expr,
    depth: int | str | Expr,
    *,
    doc: str = "",
) -> Memory:
    """Build a ``Memory`` (IR_SPEC §10.2). ``width``/``depth`` accept int, name,
    or ``Expr`` (coerced via :func:`width`)."""
    return Memory(name=name, width=_expr(width), depth=_expr(depth), doc=doc)


def genfor(
    label: str,
    genvar: str,
    count: int | str | Expr,
    items: Sequence[ModuleItem],
) -> GenFor:
    """Build a ``GenFor`` (IR_SPEC §10.1). ``count`` accepts int, name, or
    ``Expr``."""
    return GenFor(label=label, genvar=genvar, count=_expr(count), items=items)


def _expr(n_or_name: int | str | Expr) -> Expr:
    """Coerce int -> ``Const``, str -> ``Ref``, ``Expr`` -> unchanged."""
    return width(n_or_name)
