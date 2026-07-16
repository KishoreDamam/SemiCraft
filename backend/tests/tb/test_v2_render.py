"""P3-02 renderer tests: every P3-01 node renders to exact SystemVerilog.

Exact-string assertions over ``render_tb`` output for the full node family:
WaitUntil, ForkJoin (all three join kinds), RepeatBlock, IfTb (with/without
else), TimeoutGuard, Dump, Task + CallTask round trip, AssertProperty
(with/without disable iff), ResetSeq, and nested containers. The P2 smoke
subset's rendering is untouched (golden byte-identity is proven separately by
backend/tests/golden/test_snapshots.py).
"""

from __future__ import annotations

import pytest
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
    WaitUntil,
)
from semicraft_core.tb.render_tb import render_tb


def _render(
    stmts,
    *,
    tasks=(),
    asserts=(),
    reset_seq=None,
) -> str:
    tb = TbModule(
        name="mini_tb",
        decls=[Decl("clk", 1), Decl("rst_n", 1), Decl("d", 8), Decl("q", 8)],
        clock=ClockGen("clk"),
        dut=DutInstance(
            "mini", "dut", (("clk", "clk"), ("d", "d"), ("q", "q"))
        ),
        initial=Initial(tuple(stmts)),
        tasks=tasks,
        asserts=asserts,
        reset_seq=reset_seq,
    )
    return render_tb(tb)


# Initial-block bodies sit two indent levels deep (module -> initial).
_I2 = "        "
_I3 = "            "
_I4 = "                "


# --------------------------------------------------------------------------- #
# simple statements
# --------------------------------------------------------------------------- #


def test_wait_until_renders_level_sensitive_wait() -> None:
    text = _render([WaitUntil("done == 1'b1"), Finish()])
    assert f"{_I2}wait (done == 1'b1);\n" in text


def test_call_task_renders_invocation() -> None:
    text = _render(
        [CallTask("drive_idle"), Finish()],
        tasks=(Task("drive_idle", [DriveSignal("d", 0, 8)]),),
    )
    assert f"{_I2}drive_idle();\n" in text


def test_dump_renders_dumpfile_and_dumpvars_with_tb_scope() -> None:
    text = _render([Dump("waves.vcd"), Finish()])
    assert f'{_I2}$dumpfile("waves.vcd");\n{_I2}$dumpvars(0, mini_tb);\n' in text


def test_dump_levels_forwarded() -> None:
    text = _render([Dump("waves.vcd", levels=2), Finish()])
    assert f"{_I2}$dumpvars(2, mini_tb);\n" in text


# --------------------------------------------------------------------------- #
# fork/join — all three join disciplines
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("join", "keyword"),
    [("all", "join"), ("any", "join_any"), ("none", "join_none")],
)
def test_fork_join_disciplines(join: str, keyword: str) -> None:
    fj = ForkJoin([[Display("a")], [Display("b")]], join)
    text = _render([fj, Finish()])
    expected = (
        f"{_I2}fork\n"
        f"{_I3}begin\n"
        f'{_I4}$display("a");\n'
        f"{_I3}end\n"
        f"{_I3}begin\n"
        f'{_I4}$display("b");\n'
        f"{_I3}end\n"
        f"{_I2}{keyword}\n"
    )
    assert expected in text


# --------------------------------------------------------------------------- #
# repeat / if
# --------------------------------------------------------------------------- #


def test_repeat_block_renders_begin_end() -> None:
    text = _render([RepeatBlock(4, [DriveSignal("d", 1, 8)]), Finish()])
    expected = (
        f"{_I2}repeat (4) begin\n"
        f"{_I3}d = 8'd1;\n"
        f"{_I2}end\n"
    )
    assert expected in text


def test_if_without_else() -> None:
    text = _render([IfTb("q == 8'd3", [Display("hit")]), Finish()])
    expected = (
        f"{_I2}if (q == 8'd3) begin\n"
        f'{_I3}$display("hit");\n'
        f"{_I2}end\n"
    )
    assert expected in text
    assert "else" not in text


def test_if_with_else() -> None:
    text = _render(
        [IfTb("q == 8'd3", [Display("hit")], [Display("miss")]), Finish()]
    )
    expected = (
        f"{_I2}if (q == 8'd3) begin\n"
        f'{_I3}$display("hit");\n'
        f"{_I2}end else begin\n"
        f'{_I3}$display("miss");\n'
        f"{_I2}end\n"
    )
    assert expected in text


# --------------------------------------------------------------------------- #
# timeout guard
# --------------------------------------------------------------------------- #


def test_timeout_guard_renders_forked_watchdog() -> None:
    text = _render([TimeoutGuard(1000, "TIMEOUT: mini hung"), Finish()])
    expected = (
        f"{_I2}fork\n"
        f"{_I3}begin\n"
        f"{_I4}repeat (1000) @(posedge clk);\n"
        f'{_I4}$fatal(1, "TIMEOUT: mini hung");\n'
        f"{_I3}end\n"
        f"{_I2}join_none\n"
    )
    assert expected in text


# --------------------------------------------------------------------------- #
# tasks (module level) + round trip with CallTask
# --------------------------------------------------------------------------- #


def test_task_renders_between_dut_and_initial() -> None:
    text = _render(
        [CallTask("pulse_d"), Finish()],
        tasks=(
            Task("pulse_d", [DriveSignal("d", 1, 8), DriveSignal("d", 0, 8)]),
        ),
    )
    expected = (
        "    task pulse_d;\n"
        f"{_I2}d = 8'd1;\n"
        f"{_I2}d = 8'd0;\n"
        "    endtask\n"
    )
    assert expected in text
    # declared before the stimulus process invokes it
    assert text.index("task pulse_d;") < text.index("pulse_d();")


def test_multiple_tasks_render_in_declaration_order() -> None:
    text = _render(
        [CallTask("t_a"), CallTask("t_b"), Finish()],
        tasks=(Task("t_a", [Display("a")]), Task("t_b", [Display("b")])),
    )
    assert text.index("task t_a;") < text.index("task t_b;")


# --------------------------------------------------------------------------- #
# assert property (SVA stub)
# --------------------------------------------------------------------------- #


def test_assert_property_with_disable_iff() -> None:
    text = _render(
        [Finish()],
        asserts=(
            AssertProperty("no_x_on_q", "!$isunknown(q)", "clk", "!rst_n"),
        ),
    )
    expected = (
        "    // Concurrent assertions (SVA)\n"
        "    no_x_on_q: assert property "
        "(@(posedge clk) disable iff (!rst_n) !$isunknown(q))\n"
        f'{_I2}else $fatal(1, "SVA FAIL: no_x_on_q");\n'
    )
    assert expected in text


def test_assert_property_without_disable_iff() -> None:
    text = _render(
        [Finish()],
        asserts=(AssertProperty("q_stable", "$stable(q)", "clk", None),),
    )
    assert (
        "    q_stable: assert property (@(posedge clk) $stable(q))\n" in text
    )
    assert "disable iff" not in text


# --------------------------------------------------------------------------- #
# reset sequence (module level)
# --------------------------------------------------------------------------- #


def test_reset_seq_active_low() -> None:
    text = _render(
        [Finish()], reset_seq=ResetSeq("rst_n", active_low=True, cycles=2)
    )
    expected = (
        "    // Reset sequence\n"
        "    initial begin\n"
        f"{_I2}rst_n = 1'd0;\n"
        f"{_I2}repeat (2) @(posedge clk);\n"
        f"{_I2}rst_n = 1'd1;\n"
        "    end\n"
    )
    assert expected in text


def test_reset_seq_active_high_single_cycle_drops_repeat() -> None:
    text = _render(
        [Finish()], reset_seq=ResetSeq("rst", active_low=False, cycles=1)
    )
    expected = (
        f"{_I2}rst = 1'd1;\n"
        f"{_I2}@(posedge clk);\n"
        f"{_I2}rst = 1'd0;\n"
    )
    assert expected in text


def test_reset_seq_absent_emits_no_reset_process() -> None:
    text = _render([Finish()])
    assert "// Reset sequence" not in text


# --------------------------------------------------------------------------- #
# nesting: RepeatBlock > IfTb > ExpectSignal
# --------------------------------------------------------------------------- #


def test_nested_containers_indent_correctly() -> None:
    inner = ExpectSignal("q", 5, 8, "cycle 7")
    text = _render(
        [RepeatBlock(3, [IfTb("d == 8'd1", [inner])]), Finish()]
    )
    expected = (
        f"{_I2}repeat (3) begin\n"
        f"{_I3}if (d == 8'd1) begin\n"
        f"{_I4}if (q !== 8'd5) begin\n"
        f"{_I4}    $fatal(1, \"SMOKE FAIL: q at cycle 7 "
        f'expected 5, got %0d", q);\n'
        f"{_I4}end\n"
        f"{_I3}end\n"
        f"{_I2}end\n"
    )
    assert expected in text


def test_fork_containing_repeat_and_wait_until() -> None:
    fj = ForkJoin(
        [[RepeatBlock(2, [Display("tick")])], [WaitUntil("q != 8'd0")]],
        "any",
    )
    text = _render([fj, Finish()])
    assert f"{_I4}repeat (2) begin\n" in text
    assert f"{_I4}wait (q != 8'd0);\n" in text


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_full_family_render_is_deterministic() -> None:
    def build() -> str:
        return _render(
            [
                Dump("waves.vcd"),
                TimeoutGuard(100, "hang"),
                CallTask("t"),
                ForkJoin([[Display("x")]], "none"),
                Finish(),
            ],
            tasks=(Task("t", [WaitUntil("done")]),),
            asserts=(AssertProperty("a", "q >= 0", "clk", "!rst_n"),),
            reset_seq=ResetSeq("rst_n", active_low=True, cycles=2),
        )

    assert build() == build()
