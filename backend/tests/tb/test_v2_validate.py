"""validate_tb (TB_SPEC T1–T8) coverage.

A valid full-featured TbModule (fork/join, tasks, timeout, dump, assert) passes;
at least one negative case per rule/sub-clause fails with a matching message.
The T3 separation test smuggles a synthesizable ir.nodes.Assign into an Initial
and asserts rejection.
"""

from __future__ import annotations

import pytest
from semicraft_core.ir.nodes import Assign, Const, Ref
from semicraft_core.tb.nodes import (
    AssertProperty,
    CallTask,
    ClockGen,
    Decl,
    Display,
    DriveSignal,
    Dump,
    DutInstance,
    ExpectSignal,
    Finish,
    ForkJoin,
    IfTb,
    Initial,
    RepeatBlock,
    ResetSeq,
    Task,
    TbModule,
    TimeoutGuard,
    WaitCycles,
    WaitUntil,
)
from semicraft_core.tb.validate import TbValidationError, validate_tb

# --------------------------------------------------------------------------- #
# a valid, full-featured testbench
# --------------------------------------------------------------------------- #


def _valid_tb(**overrides) -> TbModule:
    decls = [
        Decl("clk", 1),
        Decl("rst_n", 1),
        Decl("data_in", 8),
        Decl("data_out", 8),
        Decl("done", 1),
    ]
    tasks = [
        Task(
            "apply_reset",
            [
                DriveSignal("rst_n", 0, 1),
                WaitCycles(3),
                DriveSignal("rst_n", 1, 1),
            ],
        ),
        Task("drive_one", [DriveSignal("data_in", 1, 8)]),
    ]
    asserts = [
        AssertProperty("p_done", "done |-> ##1 data_out != 0", "clk", "rst_n"),
    ]
    initial = Initial(
        (
            Dump("waves.vcd", 0),
            CallTask("apply_reset"),
            DriveSignal("data_in", 5, 8),
            WaitCycles(1, "negedge"),
            WaitUntil("done == 1'b1"),
            RepeatBlock(3, [CallTask("drive_one")]),
            IfTb(
                "data_out == 8'd5",
                [Display("ok")],
                [Display("bad")],
            ),
            ForkJoin(
                [
                    [TimeoutGuard(100, "timeout waiting for done")],
                    [WaitUntil("done == 1'b1")],
                ],
                "any",
            ),
            ExpectSignal("data_out", 5, 8, "cycle 1"),
            Display("SMOKE PASS: dut_mod"),
            Finish(),
        )
    )
    kwargs = dict(
        name="dut_mod_tb",
        decls=decls,
        clock=ClockGen("clk"),
        dut=DutInstance(
            "dut_mod",
            "dut",
            (("clk", "clk"), ("rst_n", "rst_n"), ("data_in", "data_in")),
        ),
        initial=initial,
        tasks=tasks,
        asserts=asserts,
        reset_seq=ResetSeq("rst_n", active_low=True, cycles=3),
    )
    kwargs.update(overrides)
    return TbModule(**kwargs)


def test_valid_full_featured_tb_passes() -> None:
    validate_tb(_valid_tb())  # must not raise


def _messages(tb: TbModule, **kw) -> list[str]:
    with pytest.raises(TbValidationError) as exc:
        validate_tb(tb, **kw)
    return exc.value.violations


# --------------------------------------------------------------------------- #
# T1 — identifiers, uniqueness, DUT-instance collision
# --------------------------------------------------------------------------- #


def test_t1_non_snake_case_decl() -> None:
    tb = _valid_tb(
        decls=[Decl("clk", 1), Decl("DataIn", 8), Decl("done", 1)],
        dut=DutInstance("dut_mod", "dut", (("clk", "clk"),)),
        initial=Initial((Finish(),)),
        tasks=[],
        asserts=[],
    )
    assert any("not lower_snake_case" in m and "DataIn" in m for m in _messages(tb))


def test_t1_reserved_word_decl() -> None:
    tb = _valid_tb(
        decls=[Decl("clk", 1), Decl("wire", 8), Decl("done", 1)],
        dut=DutInstance("dut_mod", "dut", (("clk", "clk"),)),
        initial=Initial((Finish(),)),
        tasks=[],
        asserts=[],
    )
    assert any("reserved word" in m and "wire" in m for m in _messages(tb))


def test_t1_duplicate_decl() -> None:
    tb = _valid_tb(
        decls=[Decl("clk", 1), Decl("done", 1), Decl("done", 1)],
        dut=DutInstance("dut_mod", "dut", (("clk", "clk"),)),
        initial=Initial((Finish(),)),
        tasks=[],
        asserts=[],
    )
    assert any("duplicate declaration name" in m and "done" in m for m in _messages(tb))


def test_t1_duplicate_task() -> None:
    tb = _valid_tb(
        tasks=[Task("t", [Finish()]), Task("t", [Display("x")])],
    )
    assert any("duplicate task name" in m and "'t'" in m for m in _messages(tb))


def test_t1_dut_instance_collides_with_decl() -> None:
    tb = _valid_tb(
        decls=[Decl("clk", 1), Decl("dut", 1), Decl("done", 1)],
        dut=DutInstance("dut_mod", "dut", (("clk", "clk"),)),
        initial=Initial((Finish(),)),
        tasks=[],
        asserts=[],
    )
    assert any("collides with a declared net" in m for m in _messages(tb))


# --------------------------------------------------------------------------- #
# T2 — driven / expected signals resolve
# --------------------------------------------------------------------------- #


def test_t2_drive_undeclared_signal() -> None:
    tb = _valid_tb(
        initial=Initial((DriveSignal("ghost", 1, 8), Finish())),
        tasks=[],
    )
    assert any("[T2]" in m and "ghost" in m for m in _messages(tb))


def test_t2_expect_undeclared_signal() -> None:
    tb = _valid_tb(
        initial=Initial((ExpectSignal("ghost", 1, 8, "c0"), Finish())),
        tasks=[],
    )
    assert any("[T2]" in m and "ghost" in m for m in _messages(tb))


def test_t2_drive_inside_task_body_is_checked() -> None:
    tb = _valid_tb(
        tasks=[Task("bad", [DriveSignal("ghost", 0, 8)])],
    )
    assert any("[T2]" in m and "ghost" in m for m in _messages(tb))


# --------------------------------------------------------------------------- #
# T3 — separation: no synthesizable IR node in the TB tree
# --------------------------------------------------------------------------- #


def test_t3_rejects_ir_assign_in_initial() -> None:
    tb = _valid_tb(
        initial=Initial((Assign(Ref("data_out"), Const(1)), Finish())),
        tasks=[],
    )
    msgs = _messages(tb)
    assert any("[T3]" in m and "Assign" in m for m in msgs)


def test_t3_rejects_ir_node_nested_in_fork_branch() -> None:
    tb = _valid_tb(
        initial=Initial(
            (
                ForkJoin([[Assign(Ref("data_out"), Const(0))]], "all"),
                Finish(),
            )
        ),
        tasks=[],
    )
    assert any("[T3]" in m for m in _messages(tb))


def test_t3_rejects_ir_node_inside_task() -> None:
    tb = _valid_tb(
        tasks=[Task("bad", [Assign(Ref("data_out"), Const(0))])],
    )
    assert any("[T3]" in m for m in _messages(tb))


# --------------------------------------------------------------------------- #
# T4 — fork/join shape; timeout cycles
# --------------------------------------------------------------------------- #


def test_t4_empty_fork_branches() -> None:
    tb = _valid_tb(
        initial=Initial((ForkJoin([], "all"), Finish())),
        tasks=[],
    )
    assert any("[T4]" in m and "no branches" in m for m in _messages(tb))


def test_t4_empty_single_branch() -> None:
    tb = _valid_tb(
        initial=Initial((ForkJoin([[]], "all"), Finish())),
        tasks=[],
    )
    assert any("[T4]" in m and "empty" in m for m in _messages(tb))


def test_t4_bad_join_kind() -> None:
    tb = _valid_tb(
        initial=Initial((ForkJoin([[Display("x")]], "some"), Finish())),
        tasks=[],
    )
    assert any("[T4]" in m and "'some'" in m for m in _messages(tb))


def test_t4_timeout_nonpositive_cycles() -> None:
    tb = _valid_tb(
        initial=Initial(
            (ForkJoin([[TimeoutGuard(0, "x")]], "any"), Finish())
        ),
        tasks=[],
    )
    assert any("[T4]" in m and "cycles must be > 0" in m for m in _messages(tb))


# --------------------------------------------------------------------------- #
# T5 — CallTask resolution + recursion
# --------------------------------------------------------------------------- #


def test_t5_call_undeclared_task() -> None:
    tb = _valid_tb(
        initial=Initial((CallTask("missing"), Finish())),
        tasks=[],
    )
    assert any("[T5]" in m and "missing" in m for m in _messages(tb))


def test_t5_direct_recursion() -> None:
    tb = _valid_tb(
        tasks=[Task("loop", [CallTask("loop")])],
        initial=Initial((CallTask("loop"), Finish())),
    )
    assert any("[T5]" in m and "recursive task cycle" in m for m in _messages(tb))


def test_t5_mutual_recursion() -> None:
    tb = _valid_tb(
        tasks=[
            Task("a", [CallTask("b")]),
            Task("b", [CallTask("a")]),
        ],
        initial=Initial((CallTask("a"), Finish())),
    )
    msgs = _messages(tb)
    assert any("recursive task cycle" in m for m in msgs)


# --------------------------------------------------------------------------- #
# T6 — exactly one $finish at the top of the main Initial
# --------------------------------------------------------------------------- #


def test_t6_no_finish() -> None:
    tb = _valid_tb(
        initial=Initial((Display("done"),)),
        tasks=[],
    )
    assert any("[T6]" in m and "no $finish" in m for m in _messages(tb))


def test_t6_finish_not_last() -> None:
    tb = _valid_tb(
        initial=Initial((Finish(), Display("after finish"))),
        tasks=[],
    )
    assert any("[T6]" in m and "last statement" in m for m in _messages(tb))


def test_t6_multiple_top_level_finish() -> None:
    tb = _valid_tb(
        initial=Initial((Finish(), Finish())),
        tasks=[],
    )
    assert any("[T6]" in m and "multiple top-level" in m for m in _messages(tb))


def test_t6_finish_inside_trailing_construct_is_accepted() -> None:
    tb = _valid_tb(
        initial=Initial(
            (
                Display("x"),
                IfTb("cond", [Finish()], [Finish()]),
            )
        ),
        tasks=[],
        asserts=[],
    )
    validate_tb(tb)  # trailing IfTb contains a Finish -> OK


# --------------------------------------------------------------------------- #
# T7 — Dump file safety
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("bad", ["../waves.vcd", "sub/waves.vcd", "a\\b.vcd", "C:x.vcd", ""])
def test_t7_unsafe_dump_names(bad: str) -> None:
    tb = _valid_tb(
        initial=Initial((Dump(bad), Finish())),
        tasks=[],
    )
    assert any("[T7]" in m for m in _messages(tb))


# --------------------------------------------------------------------------- #
# T8 — AssertProperty
# --------------------------------------------------------------------------- #


def test_t8_duplicate_assert_names() -> None:
    tb = _valid_tb(
        asserts=[
            AssertProperty("p", "a |-> b", "clk", None),
            AssertProperty("p", "c |-> d", "clk", None),
        ],
    )
    assert any("[T8]" in m and "duplicate" in m for m in _messages(tb))


def test_t8_empty_property_text() -> None:
    tb = _valid_tb(
        asserts=[AssertProperty("p", "   ", "clk", None)],
    )
    assert any("[T8]" in m and "empty property_text" in m for m in _messages(tb))


def test_t8_clock_does_not_resolve() -> None:
    tb = _valid_tb(
        asserts=[AssertProperty("p", "a |-> b", "not_a_net", None)],
    )
    assert any("[T8]" in m and "not_a_net" in m for m in _messages(tb))


def test_t8_clock_may_be_the_clockgen_signal() -> None:
    # 'clk' is the ClockGen signal and also a Decl here; resolving to it is fine.
    validate_tb(_valid_tb())


# --------------------------------------------------------------------------- #
# extra_reserved + all-violations behaviour
# --------------------------------------------------------------------------- #


def test_extra_reserved_flags_decl() -> None:
    tb = _valid_tb(
        decls=[Decl("clk", 1), Decl("foo", 8), Decl("done", 1)],
        dut=DutInstance("dut_mod", "dut", (("clk", "clk"),)),
        initial=Initial((Finish(),)),
        tasks=[],
        asserts=[],
    )
    msgs = _messages(tb, extra_reserved=frozenset({"foo"}))
    assert any("reserved word" in m and "foo" in m for m in msgs)


def test_all_violations_collected_and_sorted() -> None:
    tb = _valid_tb(
        decls=[Decl("clk", 1), Decl("Bad", 1)],
        dut=DutInstance("dut_mod", "dut", (("clk", "clk"),)),
        initial=Initial((DriveSignal("ghost", 1, 8),)),  # T2 + T6
        tasks=[],
        asserts=[],
    )
    msgs = _messages(tb)
    assert len(msgs) >= 3  # T1 style + T2 ghost + T6 no finish
    assert msgs == sorted(msgs)
