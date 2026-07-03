"""Validation tests: one passing valid module + one negative per §6 rule.

Each ``test_rule_N_*`` deliberately constructs a module that violates exactly
one IR_SPEC §6 rule and asserts the corresponding message appears. Because
``validate`` reports *all* violations, the negatives keep other rules satisfied
so the intent is unambiguous.
"""

from __future__ import annotations

import pytest
from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysComb,
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    Case,
    CaseItem,
    ClockSpec,
    Comment,
    Const,
    ContAssign,
    DataType,
    EnumDecl,
    EnumEncoding,
    EnumRef,
    Header,
    IRValidationError,
    Module,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
    bit,
    validate,
    vec,
)

HEADER = Header(
    license="as-is",
    config_hash="0" * 12,
    tool_version="0.1.0",
    description="test",
)


def _mod(name: str = "m", *, params=(), ports=(), items=()) -> Module:
    return Module(name=name, header=HEADER, params=params, ports=ports, items=items)


# --- a hand-built valid module passes ---------------------------------------


def test_valid_module_passes() -> None:
    m = _mod(
        ports=[
            Port("clk", IN, bit()),
            Port("a", IN, vec(8)),
            Port("y", OUT, vec(8)),
        ],
        items=[ContAssign(Ref("y"), Ref("a"))],
    )
    validate(m)  # must not raise


def _messages(exc: IRValidationError) -> str:
    return "\n".join(exc.violations)


# --- Rule 1: identifiers valid; no duplicates -------------------------------


def test_rule_1_duplicate_name() -> None:
    m = _mod(
        ports=[Port("clk", IN, bit())],
        items=[Signal("clk", bit())],  # collides with the port
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 1] duplicate declared name: 'clk'" in _messages(ei.value)


def test_rule_1_non_canonical_identifier() -> None:
    m = _mod(ports=[Port("DataIn", IN, bit())])  # not lower_snake_case
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 1]" in _messages(ei.value)
    assert "DataIn" in _messages(ei.value)


def test_rule_1_param_names_are_upper_snake() -> None:
    from semicraft_core.ir.nodes import Const, Param

    ok = _mod(params=[Param("WIDTH", Const(8))])
    validate(ok)  # UPPER_SNAKE_CASE param is canonical

    bad = _mod(params=[Param("width", Const(8))])  # lowercase param rejected
    with pytest.raises(IRValidationError) as ei:
        validate(bad)
    assert "UPPER_SNAKE_CASE parameter" in _messages(ei.value)


# --- Rule 2: every Ref / EnumRef resolves -----------------------------------


def test_rule_2_unresolved_ref() -> None:
    m = _mod(
        ports=[Port("y", OUT, bit())],
        items=[ContAssign(Ref("y"), Ref("nope"))],  # 'nope' undeclared
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 2] unresolved Ref 'nope'" in _messages(ei.value)


def test_rule_2_unresolved_enum_member() -> None:
    m = _mod(
        ports=[Port("clk", IN, bit()), Port("y", OUT, bit())],
        items=[
            EnumDecl("state_t", ["s_idle", "s_run"], EnumEncoding.BINARY),
            Signal("state", DataType(width=Const(1))),
            AlwaysComb(
                body=[
                    Case(
                        Ref("state"),
                        items=[
                            CaseItem(
                                [EnumRef("state_t", "s_bogus")],  # not a member
                                [Assign(Ref("y"), Const(0))],
                            )
                        ],
                        default=[Assign(Ref("y"), Const(0))],
                    )
                ]
            ),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "not a member" in _messages(ei.value)


# --- Rule 3: single-driver rule ---------------------------------------------


def test_rule_3_multiple_drivers() -> None:
    m = _mod(
        ports=[Port("a", IN, bit()), Port("y", OUT, bit())],
        items=[
            ContAssign(Ref("y"), Ref("a")),
            ContAssign(Ref("y"), Const(0)),  # second driver of 'y'
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 3] signal 'y' has multiple drivers" in _messages(ei.value)


# --- Rule 4: valid lvalue; input ports never driven -------------------------


def test_rule_4_input_port_driven() -> None:
    m = _mod(
        ports=[Port("a", IN, bit())],
        items=[ContAssign(Ref("a"), Const(0))],  # driving an input
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 4] input port 'a' is driven" in _messages(ei.value)


def test_rule_4_invalid_lvalue() -> None:
    m = _mod(
        ports=[Port("a", IN, bit()), Port("y", OUT, bit())],
        # lhs is a BinOp, not a Ref/Bit/Slice/Concat -> invalid lvalue
        items=[ContAssign(BinOp(BinOpKind.ADD, Ref("y"), Ref("a")), Const(0))],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 4] invalid lvalue" in _messages(ei.value)


# --- Rule 5: case coverage --------------------------------------------------


def test_rule_5_non_enum_case_without_default() -> None:
    m = _mod(
        ports=[Port("sel", IN, vec(2)), Port("y", OUT, bit())],
        items=[
            AlwaysComb(
                body=[
                    Case(
                        Ref("sel"),
                        items=[CaseItem([Const(0)], [Assign(Ref("y"), Const(1))])],
                        default=None,  # non-enum labels + no default
                    )
                ]
            )
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 5] non-enum Case" in _messages(ei.value)


def test_rule_5_enum_case_missing_member() -> None:
    m = _mod(
        ports=[Port("y", OUT, bit())],
        items=[
            EnumDecl("state_t", ["s_idle", "s_run"], EnumEncoding.BINARY),
            Signal("state", DataType(width=Const(1))),
            AlwaysComb(
                body=[
                    Case(
                        Ref("state"),
                        items=[
                            CaseItem(
                                [EnumRef("state_t", "s_idle")],  # s_run missing
                                [Assign(Ref("y"), Const(0))],
                            )
                        ],
                        default=None,
                    )
                ]
            ),
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "missing member(s)" in _messages(ei.value)


# --- Rule 6: reset=None implies empty reset_body ----------------------------


def test_rule_6_reset_none_with_reset_body() -> None:
    m = _mod(
        ports=[Port("clk", IN, bit()), Port("y", OUT, bit())],
        items=[
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=None,
                reset_body=[Assign(Ref("y"), Const(0))],  # must be empty
                body=[Assign(Ref("y"), Const(1))],
            )
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    assert "[rule 6]" in _messages(ei.value)


# --- Rule 7: reserved-word check --------------------------------------------


def test_rule_7_reserved_word_name() -> None:
    # 'wire' is a Verilog keyword; 'logic' is an SV keyword. Use both.
    m = _mod(
        ports=[Port("clk", IN, bit())],
        items=[Signal("wire", bit()), Signal("logic", bit())],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    msg = _messages(ei.value)
    assert "[rule 7]" in msg
    assert "'wire'" in msg
    assert "'logic'" in msg


def test_rule_7_extra_reserved_parameter() -> None:
    # The style engine passes post-transform keyword collisions here.
    m = _mod(ports=[Port("clk", IN, bit()), Port("myname", OUT, bit())])
    with pytest.raises(IRValidationError) as ei:
        validate(m, extra_reserved=frozenset({"myname"}))
    assert "[rule 7] name collides with a reserved word: 'myname'" in _messages(ei.value)


# --- error reports ALL violations, not just the first -----------------------


def test_error_lists_all_violations_sorted() -> None:
    m = _mod(
        ports=[Port("a", IN, bit())],
        items=[
            ContAssign(Ref("a"), Ref("undeclared")),  # rule 2 + rule 4
        ],
    )
    with pytest.raises(IRValidationError) as ei:
        validate(m)
    v = ei.value.violations
    assert v == sorted(v)  # deterministic ordering
    assert any("[rule 2]" in x for x in v)
    assert any("[rule 4]" in x for x in v)


def test_comment_stmt_ignored_by_validation() -> None:
    # Comments carry no expressions; they must not trip Ref resolution.
    m = _mod(
        ports=[Port("clk", IN, bit()), Port("y", OUT, bit())],
        items=[
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=ResetSpec("rst", ResetKind.SYNC, active_low=True),
                reset_body=[Assign(Ref("y"), Const(0))],
                body=[Comment("just a note"), Assign(Ref("y"), Const(1))],
            )
        ],
    )
    validate(m)  # must not raise
