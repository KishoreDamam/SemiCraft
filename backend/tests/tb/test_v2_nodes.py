"""Construction and immutability of the P3-01 testbench node family.

Covers every new node (WaitUntil, ForkJoin, RepeatBlock, IfTb, TimeoutGuard,
Dump, CallTask, ResetSeq, Task, AssertProperty) plus the additive TbModule
fields — construction, Sequence->tuple coercion, immutability, hashability — and
confirms the P2 smoke set stays source-compatible.
"""

from __future__ import annotations

import dataclasses

import pytest
from semicraft_core.tb.nodes import (
    JOIN_KINDS,
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

# --------------------------------------------------------------------------- #
# construction
# --------------------------------------------------------------------------- #


def test_wait_until_construction() -> None:
    w = WaitUntil("done == 1'b1")
    assert w.condition_text == "done == 1'b1"


def test_fork_join_coerces_nested_sequences_to_tuples() -> None:
    branch_a = [Display("a"), Finish()]
    branch_b = [WaitUntil("done")]
    fj = ForkJoin([branch_a, branch_b], "any")
    assert isinstance(fj.branches, tuple)
    assert isinstance(fj.branches[0], tuple)
    assert fj.branches[0] == (Display("a"), Finish())
    assert fj.join == "any"
    # mutating the inputs must not affect the node
    branch_a.append(Display("z"))
    assert fj.branches[0] == (Display("a"), Finish())


def test_repeat_block_coerces_stmts() -> None:
    stmts = [DriveSignal("d", 1, 8)]
    rb = RepeatBlock(4, stmts)
    assert rb.count == 4
    assert isinstance(rb.stmts, tuple)
    stmts.append(DriveSignal("d", 2, 8))
    assert rb.stmts == (DriveSignal("d", 1, 8),)


def test_if_tb_construction_with_and_without_else() -> None:
    then = [Display("t")]
    node = IfTb("x == 1", then, [Display("e")])
    assert node.condition_text == "x == 1"
    assert isinstance(node.then, tuple)
    assert isinstance(node.else_, tuple)
    no_else = IfTb("x == 1", then)
    assert no_else.else_ is None


def test_timeout_guard_construction() -> None:
    g = TimeoutGuard(1000, "watchdog fired")
    assert g.cycles == 1000
    assert g.message == "watchdog fired"


def test_dump_defaults_levels_to_zero() -> None:
    d = Dump("waves.vcd")
    assert d.file == "waves.vcd"
    assert d.levels == 0
    assert Dump("waves.vcd", 3).levels == 3


def test_call_task_construction() -> None:
    assert CallTask("apply_reset").name == "apply_reset"


def test_reset_seq_construction() -> None:
    r = ResetSeq("rst_n", active_low=True, cycles=5)
    assert r.signal == "rst_n"
    assert r.active_low is True
    assert r.cycles == 5


def test_task_coerces_stmts() -> None:
    stmts = [DriveSignal("d", 0, 8)]
    t = Task("drive_zero", stmts)
    assert t.name == "drive_zero"
    assert isinstance(t.stmts, tuple)
    stmts.append(Finish())
    assert t.stmts == (DriveSignal("d", 0, 8),)


def test_assert_property_construction() -> None:
    a = AssertProperty("p_ack", "req |-> ##1 ack", "clk", "rst_n")
    assert a.name == "p_ack"
    assert a.property_text == "req |-> ##1 ack"
    assert a.clock == "clk"
    assert a.disable_iff == "rst_n"
    assert AssertProperty("p", "x", "clk", None).disable_iff is None


def test_join_kinds_constant() -> None:
    assert JOIN_KINDS == frozenset({"all", "any", "none"})


# --------------------------------------------------------------------------- #
# TbModule additive fields are source-compatible with the P2 smoke set
# --------------------------------------------------------------------------- #


def _minimal_module(**extra) -> TbModule:
    return TbModule(
        name="dut_tb",
        decls=[Decl("clk", 1)],
        clock=ClockGen("clk"),
        dut=DutInstance("dut_mod", "dut", (("clk", "clk"),)),
        initial=Initial((Finish(),)),
        **extra,
    )


def test_tbmodule_p2_shape_still_builds_with_defaults() -> None:
    tb = _minimal_module()
    assert tb.tasks == ()
    assert tb.asserts == ()
    assert tb.reset_seq is None
    assert isinstance(tb.decls, tuple)


def test_tbmodule_coerces_new_sequence_fields() -> None:
    tasks = [Task("t", [Finish()])]
    asserts = [AssertProperty("p", "x", "clk", None)]
    tb = _minimal_module(
        tasks=tasks, asserts=asserts, reset_seq=ResetSeq("clk", False, 2)
    )
    assert isinstance(tb.tasks, tuple)
    assert isinstance(tb.asserts, tuple)
    assert tb.reset_seq == ResetSeq("clk", False, 2)
    tasks.append(Task("u", [Finish()]))
    assert len(tb.tasks) == 1


# --------------------------------------------------------------------------- #
# immutability + hashability
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "node",
    [
        WaitUntil("c"),
        ForkJoin([[Finish()]], "all"),
        RepeatBlock(2, [Finish()]),
        IfTb("c", [Finish()]),
        TimeoutGuard(3, "m"),
        Dump("w.vcd"),
        CallTask("t"),
        ResetSeq("rst", True, 1),
        Task("t", [Finish()]),
        AssertProperty("p", "x", "clk", None),
    ],
)
def test_new_nodes_are_frozen(node: object) -> None:
    field0 = dataclasses.fields(node)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(node, field0, "mutated")


def test_new_nodes_are_hashable() -> None:
    for node in (
        WaitUntil("c"),
        ForkJoin([[Finish()]], "all"),
        RepeatBlock(2, [Finish()]),
        IfTb("c", [Finish()], [Display("e")]),
        TimeoutGuard(3, "m"),
        Dump("w.vcd", 1),
        CallTask("t"),
        ResetSeq("rst", True, 1),
        Task("t", [Finish()]),
        AssertProperty("p", "x", "clk", None),
    ):
        assert isinstance(hash(node), int)


def test_waitcycles_still_defaults_edge() -> None:
    # P2 smoke-set node unchanged: edge defaults to posedge.
    assert WaitCycles(1).edge == "posedge"


def test_expect_signal_shape_unchanged() -> None:
    e = ExpectSignal("data_out", 5, 8, "cycle 1")
    assert (e.signal, e.expected, e.width, e.cycle_label) == (
        "data_out",
        5,
        8,
        "cycle 1",
    )
