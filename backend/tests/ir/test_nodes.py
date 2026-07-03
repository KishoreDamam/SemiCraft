"""Node construction and immutability (WP-01 task 4).

These tests double as usage documentation for the IR node catalog (IR_SPEC §3).
"""

from __future__ import annotations

import dataclasses

import pytest
from semicraft_core.ir import (
    BinOp,
    BinOpKind,
    Concat,
    Const,
    ConstBase,
    If,
    Instance,
    Ref,
)


def test_ref_construction() -> None:
    r = Ref("count")
    assert r.name == "count"


def test_const_defaults() -> None:
    c = Const(0)
    assert c.value == 0
    assert c.width is None
    assert c.base is ConstBase.DEC
    assert c.signed is False


def test_sized_const_stores_width_expr() -> None:
    c = Const(0, width=Ref("WIDTH"))
    assert c.width == Ref("WIDTH")


def test_binop_construction() -> None:
    b = BinOp(BinOpKind.ADD, Ref("count"), Const(1))
    assert b.op is BinOpKind.ADD
    assert b.a == Ref("count")
    assert b.b == Const(1)


def test_sequence_fields_stored_as_tuple() -> None:
    # Concat accepts any Sequence and stores an immutable tuple.
    parts = [Ref("a"), Ref("b")]
    cat = Concat(parts)
    assert isinstance(cat.parts, tuple)
    parts.append(Ref("c"))  # mutating the input must not affect the node
    assert cat.parts == (Ref("a"), Ref("b"))


def test_if_normalizes_bodies_to_tuples() -> None:
    node = If(
        Ref("en"),
        then=[__import_assign()],
        elifs=[(Ref("clr"), [__import_assign()])],
        else_=[__import_assign()],
    )
    assert isinstance(node.then, tuple)
    assert isinstance(node.elifs, tuple)
    assert isinstance(node.elifs[0][1], tuple)
    assert isinstance(node.else_, tuple)


def test_instance_stores_hashable_pairs_and_exposes_dict() -> None:
    inst = Instance(
        "sub", "u0", params={"W": Const(8)}, conns={"a": Ref("x")}
    )
    assert isinstance(inst.params, tuple)
    assert inst.params_dict == {"W": Const(8)}
    assert inst.conns_dict == {"a": Ref("x")}
    # Hashable because everything is a tuple of frozen nodes.
    assert isinstance(hash(inst), int)


def test_nodes_are_hashable() -> None:
    assert isinstance(hash(Ref("a")), int)
    assert isinstance(hash(Const(3, width=Ref("W"))), int)
    assert isinstance(hash(BinOp(BinOpKind.ADD, Ref("a"), Const(1))), int)


def test_mutation_attempt_raises() -> None:
    r = Ref("count")
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.name = "other"  # type: ignore[misc]


def test_mutation_of_sequence_field_raises() -> None:
    cat = Concat([Ref("a")])
    with pytest.raises(dataclasses.FrozenInstanceError):
        cat.parts = ()  # type: ignore[misc]


def __import_assign():
    # Local factory to avoid a module-level import solely for one helper.
    from semicraft_core.ir import Assign

    return Assign(Ref("count"), Const(0))
