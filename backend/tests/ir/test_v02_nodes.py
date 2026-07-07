"""Construction and immutability of the IR v0.2 nodes (IR_SPEC §10).

Covers ``GenFor``, ``Memory``, ``DataType.enum_type`` plus the v0.2 builder
helpers (``genfor``, ``mem``, ``enum_t``). Backward compatibility of the
existing positional ``DataType(width, signed)`` call form is asserted here so a
regression fails loudly.
"""

from __future__ import annotations

import dataclasses

import pytest
from semicraft_core.ir import (
    Comment,
    Const,
    ContAssign,
    DataType,
    GenFor,
    Memory,
    Ref,
    enum_t,
    genfor,
    mem,
)

# --- GenFor -----------------------------------------------------------------


def test_genfor_construction() -> None:
    body = [ContAssign(Ref("y"), Ref("a"))]
    g = GenFor(label="lanes", genvar="i", count=Const(4), items=body)
    assert g.label == "lanes"
    assert g.genvar == "i"
    assert g.count == Const(4)
    assert g.items == tuple(body)


def test_genfor_coerces_items_to_tuple() -> None:
    body = [ContAssign(Ref("y"), Ref("a")), Comment("note")]
    g = GenFor(label="lanes", genvar="i", count=Const(4), items=body)
    assert isinstance(g.items, tuple)
    body.append(Comment("later"))  # mutating the source must not leak in
    assert len(g.items) == 2


def test_genfor_is_frozen() -> None:
    g = GenFor(label="lanes", genvar="i", count=Const(4), items=[])
    with pytest.raises(dataclasses.FrozenInstanceError):
        g.label = "other"  # type: ignore[misc]


# --- Memory -----------------------------------------------------------------


def test_memory_construction() -> None:
    m = Memory(name="ram", width=Const(8), depth=Const(256), doc="scratch")
    assert m.name == "ram"
    assert m.width == Const(8)
    assert m.depth == Const(256)
    assert m.doc == "scratch"


def test_memory_doc_defaults_empty() -> None:
    m = Memory(name="ram", width=Const(8), depth=Const(256))
    assert m.doc == ""


def test_memory_is_frozen() -> None:
    m = Memory(name="ram", width=Const(8), depth=Const(256))
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.name = "other"  # type: ignore[misc]


# --- DataType.enum_type -----------------------------------------------------


def test_datatype_enum_type_default_none() -> None:
    assert DataType().enum_type is None
    assert DataType(width=Const(8)).enum_type is None


def test_datatype_enum_type_keyword_only() -> None:
    dt = DataType(enum_type="state_t")
    assert dt.enum_type == "state_t"
    assert dt.width is None


def test_datatype_positional_backward_compat() -> None:
    # Existing positional usage DataType(width, signed) must keep working: the
    # new enum_type field is keyword-only, so it never absorbs a positional arg.
    dt = DataType(Const(8), True)
    assert dt.width == Const(8)
    assert dt.signed is True
    assert dt.enum_type is None


def test_datatype_enum_type_cannot_be_positional() -> None:
    # Three positional args would only be possible if enum_type were positional.
    with pytest.raises(TypeError):
        DataType(Const(8), False, "state_t")  # type: ignore[misc]


def test_datatype_is_frozen() -> None:
    dt = DataType(enum_type="state_t")
    with pytest.raises(dataclasses.FrozenInstanceError):
        dt.enum_type = "other_t"  # type: ignore[misc]


# --- builder helpers --------------------------------------------------------


def test_enum_t_helper() -> None:
    dt = enum_t("state_t")
    assert dt == DataType(enum_type="state_t")
    assert dt.width is None


def test_mem_helper_coerces_int_and_name() -> None:
    m = mem("ram", 8, "DEPTH", doc="d")
    assert m == Memory(name="ram", width=Const(8), depth=Ref("DEPTH"), doc="d")


def test_mem_helper_passes_expr_through() -> None:
    w = Const(16)
    m = mem("ram", w, 4)
    assert m.width is w


def test_genfor_helper_coerces_count() -> None:
    g = genfor("lanes", "i", 4, [ContAssign(Ref("y"), Ref("a"))])
    assert g == GenFor(
        label="lanes", genvar="i", count=Const(4),
        items=[ContAssign(Ref("y"), Ref("a"))],
    )


def test_genfor_helper_count_name() -> None:
    g = genfor("lanes", "i", "N", [])
    assert g.count == Ref("N")
