"""Scoreboard family (P3-06) coverage: class-only emission, wrapper emission,
determinism, and validation error paths."""

from __future__ import annotations

import pytest
from semicraft_core.checkers import (
    ScoreboardSpec,
    ScoreboardWrapper,
    Signal,
    generate_scoreboard,
)


def test_class_only_exact_text() -> None:
    spec = ScoreboardSpec(name="pkt_scoreboard", item_type="logic [7:0]")
    assert generate_scoreboard(spec) == (
        "class pkt_scoreboard;\n"
        "\n"
        "    logic [7:0] expected_q[$];\n"
        "    int unsigned match_count;\n"
        "    int unsigned mismatch_count;\n"
        "\n"
        "    function new();\n"
        "        match_count = 0;\n"
        "        mismatch_count = 0;\n"
        "    endfunction\n"
        "\n"
        "    function void push_expected(logic [7:0] item);\n"
        "        expected_q.push_back(item);\n"
        "    endfunction\n"
        "\n"
        "    function void compare(logic [7:0] actual);\n"
        "        logic [7:0] expected;\n"
        "        if (expected_q.size() == 0) begin\n"
        "            mismatch_count++;\n"
        '            $error("pkt_scoreboard: compare() called with an empty '
        'expected queue");\n'
        "            return;\n"
        "        end\n"
        "        expected = expected_q.pop_front();\n"
        "        if (actual !== expected) begin\n"
        "            mismatch_count++;\n"
        '            $error("pkt_scoreboard: mismatch: expected %0d, got %0d", '
        "expected, actual);\n"
        "        end else begin\n"
        "            match_count++;\n"
        "        end\n"
        "    endfunction\n"
        "\n"
        "    function void report();\n"
        '        $display("pkt_scoreboard: %0d match, %0d mismatch, %0d total", '
        "match_count, mismatch_count, match_count + mismatch_count);\n"
        "    endfunction\n"
        "\n"
        "endclass\n"
    )


def test_no_wrapper_emits_no_module() -> None:
    spec = ScoreboardSpec(name="sb", item_type="int")
    text = generate_scoreboard(spec)
    assert "module" not in text
    assert text.strip().endswith("endclass")


def test_wrapper_exact_text() -> None:
    spec = ScoreboardSpec(
        name="pkt_scoreboard",
        item_type="logic [7:0]",
        wrapper=ScoreboardWrapper(
            module_name="pkt_scoreboard_wrap",
            clock="clk",
            push_signal="req_valid",
            push_expr="req_data",
            compare_signal="resp_valid",
            compare_expr="resp_data",
        ),
    )
    text = generate_scoreboard(spec)
    _, _, wrapper_text = text.partition("endclass\n\n")
    assert wrapper_text == (
        "module pkt_scoreboard_wrap (\n"
        "    input logic clk,\n"
        "    input logic req_valid,\n"
        "    input logic resp_valid\n"
        ");\n"
        "\n"
        "    pkt_scoreboard sb;\n"
        "\n"
        "    initial sb = new();\n"
        "\n"
        "    always @(posedge clk) begin\n"
        "        if (req_valid) begin\n"
        "            sb.push_expected(req_data);\n"
        "        end\n"
        "        if (resp_valid) begin\n"
        "            sb.compare(resp_data);\n"
        "        end\n"
        "    end\n"
        "\n"
        "    final begin\n"
        "        sb.report();\n"
        "    end\n"
        "\n"
        "endmodule\n"
    )


def test_wrapper_extra_ports_appended_after_implicit_ports() -> None:
    spec = ScoreboardSpec(
        name="sb",
        item_type="logic [7:0]",
        wrapper=ScoreboardWrapper(
            module_name="sb_wrap",
            clock="clk",
            push_signal="push",
            push_expr="{tag, payload}",
            compare_signal="cmp",
            compare_expr="actual_data",
            ports=[Signal("tag", 2), Signal("payload", 8), Signal("actual_data", 10)],
        ),
    )
    text = generate_scoreboard(spec)
    assert "input logic [1:0] tag,\n" in text
    assert "input logic [7:0] payload,\n" in text
    assert "input logic [9:0] actual_data\n" in text


def test_wrapper_class_type_matches_scoreboard_name() -> None:
    spec = ScoreboardSpec(
        name="my_sb",
        item_type="int",
        wrapper=ScoreboardWrapper(
            module_name="my_sb_wrap",
            clock="clk",
            push_signal="p",
            push_expr="p_val",
            compare_signal="c",
            compare_expr="c_val",
        ),
    )
    text = generate_scoreboard(spec)
    assert "my_sb sb;" in text


def test_wrapper_duplicate_port_name_rejected() -> None:
    spec = ScoreboardSpec(
        name="sb",
        item_type="int",
        wrapper=ScoreboardWrapper(
            module_name="sb_wrap",
            clock="clk",
            push_signal="push",
            push_expr="v",
            compare_signal="cmp",
            compare_expr="v",
            ports=[Signal("push", 1)],
        ),
    )
    with pytest.raises(ValueError, match="duplicate scoreboard wrapper port name: 'push'"):
        generate_scoreboard(spec)


def test_wrapper_push_and_compare_signal_collision_rejected() -> None:
    spec = ScoreboardSpec(
        name="sb",
        item_type="int",
        wrapper=ScoreboardWrapper(
            module_name="sb_wrap",
            clock="clk",
            push_signal="qual",
            push_expr="v",
            compare_signal="qual",
            compare_expr="v",
        ),
    )
    with pytest.raises(ValueError, match="duplicate scoreboard wrapper port name: 'qual'"):
        generate_scoreboard(spec)


def test_determinism_same_spec_same_output() -> None:
    def make() -> ScoreboardSpec:
        return ScoreboardSpec(
            name="pkt_scoreboard",
            item_type="logic [7:0]",
            wrapper=ScoreboardWrapper(
                module_name="pkt_scoreboard_wrap",
                clock="clk",
                push_signal="req_valid",
                push_expr="req_data",
                compare_signal="resp_valid",
                compare_expr="resp_data",
            ),
        )

    assert generate_scoreboard(make()) == generate_scoreboard(make())
