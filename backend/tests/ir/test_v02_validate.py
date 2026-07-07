"""Validation tests for IR v0.2 rules 8-11 (IR_SPEC §10).

One passing module each for GenFor replication and Memory (sync write + async
read), plus at least one negative per sub-clause of rules 8-11.

``validate`` reports *all* violations, so each negative keeps every other rule
satisfied and asserts the specific expected message tag.
"""

from __future__ import annotations

import pytest
from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysComb,
    AlwaysFF,
    Assign,
    Bit,
    ClockSpec,
    Comment,
    Const,
    ContAssign,
    DataType,
    EnumDecl,
    EnumEncoding,
    GenFor,
    Header,
    Instance,
    IRValidationError,
    Memory,
    Module,
    Port,
    Ref,
    Signal,
    Slice,
    bit,
    validate,
    vec,
)

HEADER = Header(
    license="as-is",
    config_hash="0" * 12,
    tool_version="0.2.0",
    description="test",
)


def _mod(name: str = "m", *, params=(), ports=(), items=()) -> Module:
    return Module(name=name, header=HEADER, params=params, ports=ports, items=items)


def _messages(exc: IRValidationError) -> str:
    return "\n".join(exc.violations)


# ---------------------------------------------------------------------------
# Valid modules
# ---------------------------------------------------------------------------


def test_valid_genfor_contassign_replication() -> None:
    # Replicate a bit-slice continuous assign across lanes with the genvar.
    m = _mod(
        ports=[Port("a", IN, vec(4)), Port("y", OUT, vec(4))],
        items=[
            GenFor(
                label="lanes",
                genvar="i",
                count=Const(4),
                items=[
                    Comment("one lane"),
                    ContAssign(Bit(Ref("y"), Ref("i")), Bit(Ref("a"), Ref("i"))),
                ],
            )
        ],
    )
    validate(m)


def test_valid_genfor_instance_replication() -> None:
    m = _mod(
        ports=[Port("a", IN, vec(4)), Port("y", OUT, vec(4))],
        items=[
            GenFor(
                label="cells",
                genvar="g",
                count=Const(4),
                items=[
                    Instance(
                        module="buf_cell",
                        name="u_buf",
                        params={},
                        conns={"i": Bit(Ref("a"), Ref("g")),
                               "o": Bit(Ref("y"), Ref("g"))},
                    )
                ],
            )
        ],
    )
    validate(m)


def test_valid_memory_sync_write_async_read() -> None:
    # Synchronous write in AlwaysFF, asynchronous read via ContAssign rhs.
    m = _mod(
        ports=[
            Port("clk", IN, bit()),
            Port("we", IN, bit()),
            Port("waddr", IN, vec(8)),
            Port("raddr", IN, vec(8)),
            Port("wdata", IN, vec(8)),
            Port("rdata", OUT, vec(8)),
        ],
        items=[
            Memory(name="ram", width=Const(8), depth=Const(256)),
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=None,
                reset_body=[],
                body=[
                    Assign(Bit(Ref("ram"), Ref("waddr")), Ref("wdata")),
                ],
            ),
            ContAssign(Ref("rdata"), Bit(Ref("ram"), Ref("raddr"))),
        ],
    )
    validate(m)


def test_valid_enum_type_signal() -> None:
    m = _mod(
        ports=[Port("clk", IN, bit())],
        items=[
            EnumDecl("state_t", ["s_idle", "s_run"], EnumEncoding.BINARY),
            Signal("state", DataType(enum_type="state_t")),
        ],
    )
    validate(m)


# ---------------------------------------------------------------------------
# Rule 8: GenFor
# ---------------------------------------------------------------------------


def test_rule_8_genvar_shadows_declared_name() -> None:
    m = _mod(
        ports=[Port("a", IN, vec(4)), Port("y", OUT, vec(4))],
        items=[
            Signal("i", bit()),  # genvar 'i' shadows this signal
            GenFor(
                label="lanes",
                genvar="i",
                count=Const(4),
                items=[ContAssign(Bit(Ref("y"), Ref("i")), Bit(Ref("a"), Ref("i")))],
            ),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 8] genvar 'i'" in _messages(ei.value)
    assert "shadows" in _messages(ei.value)


def test_rule_8_ref_genvar_outside_genfor() -> None:
    m = _mod(
        ports=[Port("a", IN, vec(4)), Port("y", OUT, vec(4))],
        items=[
            GenFor(
                label="lanes",
                genvar="i",
                count=Const(4),
                items=[ContAssign(Bit(Ref("y"), Ref("i")), Bit(Ref("a"), Ref("i")))],
            ),
            # 'i' is referenced at module scope — must not resolve.
            ContAssign(Bit(Ref("y"), Const(0)), Ref("i")),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 8] Ref to genvar 'i' outside its GenFor" in _messages(ei.value)


def test_rule_8_duplicate_genfor_label() -> None:
    def loop(genvar: str) -> GenFor:
        return GenFor(
            label="lanes",  # same label both times
            genvar=genvar,
            count=Const(4),
            items=[ContAssign(Bit(Ref("y"), Ref(genvar)), Bit(Ref("a"), Ref(genvar)))],
        )

    m = _mod(
        ports=[Port("a", IN, vec(4)), Port("y", OUT, vec(4))],
        items=[loop("i"), loop("j")],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 1] duplicate declared name: 'lanes'" in _messages(ei.value)


def test_rule_8_disallowed_item_type_in_genfor() -> None:
    m = _mod(
        ports=[Port("a", IN, vec(4)), Port("y", OUT, vec(4))],
        items=[
            GenFor(
                label="lanes",
                genvar="i",
                count=Const(4),
                items=[Signal("tmp", bit())],  # Signal not allowed inside GenFor
            )
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 8]" in _messages(ei.value)
    assert "disallowed item type 'Signal'" in _messages(ei.value)


# ---------------------------------------------------------------------------
# Rule 9: Memory
# ---------------------------------------------------------------------------


def test_rule_9_whole_array_reference() -> None:
    m = _mod(
        ports=[Port("y", OUT, vec(8))],
        items=[
            Memory(name="ram", width=Const(8), depth=Const(256)),
            ContAssign(Ref("y"), Ref("ram")),  # whole-array ref, not element
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 9] whole-array reference to memory 'ram'" in _messages(ei.value)


def test_rule_9_write_in_alwayscomb() -> None:
    m = _mod(
        ports=[Port("addr", IN, vec(8)), Port("wdata", IN, vec(8))],
        items=[
            Memory(name="ram", width=Const(8), depth=Const(256)),
            AlwaysComb(body=[Assign(Bit(Ref("ram"), Ref("addr")), Ref("wdata"))]),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 9] memory 'ram' written in AlwaysComb" in _messages(ei.value)


def test_rule_9_contassign_lhs_to_memory_element() -> None:
    m = _mod(
        ports=[Port("addr", IN, vec(8)), Port("wdata", IN, vec(8))],
        items=[
            Memory(name="ram", width=Const(8), depth=Const(256)),
            ContAssign(Bit(Ref("ram"), Ref("addr")), Ref("wdata")),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 9] continuous assignment to memory element 'ram'" in _messages(
        ei.value
    )


def test_rule_9_slice_on_array_dimension() -> None:
    m = _mod(
        ports=[Port("y", OUT, vec(8))],
        items=[
            Memory(name="ram", width=Const(8), depth=Const(256)),
            # Slice(target=Ref(mem), ...) targets the array dimension.
            ContAssign(Ref("y"), Slice(Ref("ram"), Const(1), Const(0))),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 9] slice on memory array dimension 'ram'" in _messages(ei.value)


# ---------------------------------------------------------------------------
# Rule 10: DataType.enum_type
# ---------------------------------------------------------------------------


def test_rule_10_unresolved_enum_type() -> None:
    m = _mod(
        items=[Signal("state", DataType(enum_type="nope_t"))],  # no such enum
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 10] enum_type 'nope_t'" in _messages(ei.value)
    assert "not a declared EnumDecl" in _messages(ei.value)


def test_rule_10_enum_type_with_width_set() -> None:
    m = _mod(
        items=[
            EnumDecl("state_t", ["s_idle", "s_run"], EnumEncoding.BINARY),
            # enum_type set AND width set — width must be None.
            Signal("state", DataType(width=Const(2), enum_type="state_t")),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 10]" in _messages(ei.value)
    assert "also sets width" in _messages(ei.value)


# ---------------------------------------------------------------------------
# Rule 11: Memory names join the duplicate check
# ---------------------------------------------------------------------------


def test_rule_11_duplicate_memory_name() -> None:
    m = _mod(
        ports=[Port("clk", IN, bit())],
        items=[
            Signal("ram", bit()),  # collides with the memory name
            Memory(name="ram", width=Const(8), depth=Const(256)),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 1] duplicate declared name: 'ram'" in _messages(ei.value)


def test_rule_11_memory_name_duplicate_of_port() -> None:
    m = _mod(
        ports=[Port("ram", IN, vec(8))],
        items=[Memory(name="ram", width=Const(8), depth=Const(256))],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 1] duplicate declared name: 'ram'" in _messages(ei.value)


# ---------------------------------------------------------------------------
# Interaction: existing rules see inside GenFor.items
# ---------------------------------------------------------------------------


def test_genfor_body_ref_still_resolved() -> None:
    # An undeclared Ref inside a GenFor body is caught by rule 2.
    m = _mod(
        ports=[Port("y", OUT, vec(4))],
        items=[
            GenFor(
                label="lanes",
                genvar="i",
                count=Const(4),
                items=[ContAssign(Bit(Ref("y"), Ref("i")), Bit(Ref("nope"), Ref("i")))],
            )
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 2] unresolved Ref 'nope'" in _messages(ei.value)


def test_genfor_and_outside_driver_conflict() -> None:
    # A net driven both inside a GenFor and outside violates rule 3.
    m = _mod(
        ports=[Port("a", IN, vec(4)), Port("y", OUT, vec(4))],
        items=[
            GenFor(
                label="lanes",
                genvar="i",
                count=Const(4),
                items=[ContAssign(Ref("y"), Bit(Ref("a"), Ref("i")))],
            ),
            ContAssign(Ref("y"), Ref("a")),  # second driver, outside the loop
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 3] signal 'y' has multiple drivers" in _messages(ei.value)
