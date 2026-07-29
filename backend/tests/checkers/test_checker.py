"""Checker family (P3-06) coverage: exact emission per item, determinism,
guard composition, and validation error paths.

These are the *procedural* (``always``-block) checks, distinct from the
P3-05 concurrent-SVA generator (``semicraft_core.assertions``) -- assertions
here are only about this module's own emitted text/behaviour, not SVA.
"""

from __future__ import annotations

import pytest
from semicraft_core.checkers import (
    CheckerSpec,
    LatencyCheck,
    ResetPolarity,
    ResetValueCheck,
    Signal,
    StabilityCheck,
    generate_checker,
)

RST_N = ResetPolarity(signal="rst_n", active_low=True)
RST = ResetPolarity(signal="rst", active_low=False)


def _ports_and_body(text: str) -> tuple[str, str]:
    head, _, tail = text.partition(");\n")
    return head, tail


# --------------------------------------------------------------------------- #
# ResetValueCheck
# --------------------------------------------------------------------------- #


def test_reset_value_check_active_low_edge() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("done", 1)],
        checks=[ResetValueCheck("done_reset", "done", 0, 1)],
    )
    text = generate_checker(spec)
    assert "logic rst_n_prev;" in text
    assert "always @(posedge clk) rst_n_prev <= rst_n;" in text
    assert "if (!rst_n_prev && rst_n) begin" in text
    assert "if (done !== 1'd0) begin" in text
    assert (
        '$error("CHECK FAIL: done_reset: done expected 1\'d0 on reset '
        'deassertion, got %0d", done);' in text
    )


def test_reset_value_check_active_high_edge() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST,
        ports=[Signal("count", 8)],
        checks=[ResetValueCheck("count_reset", "count", 0, 8)],
    )
    text = generate_checker(spec)
    assert "logic rst_prev;" in text
    assert "always @(posedge clk) rst_prev <= rst;" in text
    assert "if (rst_prev && !rst) begin" in text
    assert "if (count !== 8'd0) begin" in text


def test_reset_value_check_without_reset_raises() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=None,
        ports=[Signal("done", 1)],
        checks=[ResetValueCheck("done_reset", "done", 0, 1)],
    )
    with pytest.raises(ValueError, match="requires CheckerSpec.reset"):
        generate_checker(spec)


def test_reset_prev_register_emitted_once_for_multiple_reset_checks() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("done", 1), Signal("busy", 1)],
        checks=[
            ResetValueCheck("done_reset", "done", 0, 1),
            ResetValueCheck("busy_reset", "busy", 0, 1),
        ],
    )
    text = generate_checker(spec)
    assert text.count("logic rst_n_prev;") == 1


def test_reset_prev_register_omitted_without_reset_value_check() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("count", 8), Signal("en", 1)],
        checks=[StabilityCheck("count_hold", "count", "en", 8)],
    )
    text = generate_checker(spec)
    assert "rst_n_prev" not in text


# --------------------------------------------------------------------------- #
# StabilityCheck
# --------------------------------------------------------------------------- #


def test_stability_check_guarded_with_reset() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("count", 8), Signal("en", 1)],
        checks=[StabilityCheck("count_hold", "count", "en", 8)],
    )
    text = generate_checker(spec)
    assert "logic count_hold_enable_prev;" in text
    assert "logic [7:0] count_hold_signal_prev;" in text
    assert "count_hold_enable_prev <= en;" in text
    assert "count_hold_signal_prev <= count;" in text
    assert (
        "if (rst_n && !count_hold_enable_prev && "
        "(count !== count_hold_signal_prev)) begin" in text
    )


def test_stability_check_active_high_guard() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST,
        ports=[Signal("count", 8), Signal("en", 1)],
        checks=[StabilityCheck("count_hold", "count", "en", 8)],
    )
    text = generate_checker(spec)
    assert "if (!rst && !count_hold_enable_prev && " in text


def test_stability_check_unguarded_omits_prefix() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("count", 8), Signal("en", 1)],
        checks=[StabilityCheck("count_hold", "count", "en", 8, guarded=False)],
    )
    text = generate_checker(spec)
    assert "if (!count_hold_enable_prev && (count !== count_hold_signal_prev)) begin" in text


def test_stability_check_without_spec_reset_has_no_guard() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=None,
        ports=[Signal("count", 8), Signal("en", 1)],
        checks=[StabilityCheck("count_hold", "count", "en", 8)],
    )
    text = generate_checker(spec)
    assert "if (!count_hold_enable_prev && (count !== count_hold_signal_prev)) begin" in text


def test_stability_check_single_bit_shadow_register_is_bare() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=None,
        ports=[Signal("flag", 1), Signal("en", 1)],
        checks=[StabilityCheck("flag_hold", "flag", "en", 1)],
    )
    text = generate_checker(spec)
    assert "logic flag_hold_signal_prev;" in text
    assert "[0:0]" not in text


# --------------------------------------------------------------------------- #
# LatencyCheck
# --------------------------------------------------------------------------- #


def test_latency_check_guarded_with_reset() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("req", 1), Signal("ack", 1)],
        checks=[LatencyCheck("req_ack", "req", "ack", 4)],
    )
    text = generate_checker(spec)
    assert "logic req_ack_pending;" in text
    assert "logic [31:0] req_ack_wait;" in text
    assert "if (!rst_n) begin" in text
    assert "req_ack_pending <= 1'b0;" in text
    assert "req_ack_wait <= 32'd0;" in text
    assert "end else if (req_ack_pending) begin" in text
    assert "if (ack) begin" in text
    assert "end else if (req_ack_wait >= 32'd4) begin" in text
    assert (
        '$error("CHECK FAIL: req_ack: ack did not arrive within 4 cycles of req");'
        in text
    )
    assert "req_ack_wait <= req_ack_wait + 32'd1;" in text
    assert "end else if (req) begin" in text
    assert "req_ack_pending <= 1'b1;" in text


def test_latency_check_without_reset_has_no_reset_branch() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=None,
        ports=[Signal("req", 1), Signal("ack", 1)],
        checks=[LatencyCheck("req_ack", "req", "ack", 3)],
    )
    text = generate_checker(spec)
    assert "if (req_ack_pending) begin" in text
    assert "rst" not in text


def test_latency_check_unguarded_omits_reset_branch_even_with_reset() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("req", 1), Signal("ack", 1)],
        checks=[LatencyCheck("req_ack", "req", "ack", 3, guarded=False)],
    )
    text = generate_checker(spec)
    assert "if (req_ack_pending) begin" in text
    assert "if (!rst_n) begin" not in text


def test_latency_check_zero_max_cycles_rejected() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=None,
        ports=[Signal("req", 1), Signal("ack", 1)],
        checks=[LatencyCheck("l", "req", "ack", 0)],
    )
    with pytest.raises(ValueError, match="requires max_cycles > 0"):
        generate_checker(spec)


def test_latency_check_negative_max_cycles_rejected() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=None,
        ports=[Signal("req", 1), Signal("ack", 1)],
        checks=[LatencyCheck("l", "req", "ack", -1)],
    )
    with pytest.raises(ValueError, match="requires max_cycles > 0"):
        generate_checker(spec)


# --------------------------------------------------------------------------- #
# Ports / module shell
# --------------------------------------------------------------------------- #


def test_ports_order_clock_reset_then_extras() -> None:
    spec = CheckerSpec(
        name="proto_checker",
        clock="clk",
        reset=RST_N,
        ports=[Signal("done", 1), Signal("count", 8)],
        checks=[],
    )
    text = generate_checker(spec)
    head, _ = _ports_and_body(text)
    port_names = [
        ln.strip().rstrip(",").split()[-1]
        for ln in head.splitlines()
        if ln.strip().startswith("input logic")
    ]
    assert port_names == ["clk", "rst_n", "done", "count"]


def test_no_checks_yields_bare_module() -> None:
    spec = CheckerSpec(name="empty_checker", clock="clk", reset=None, ports=[], checks=[])
    assert generate_checker(spec) == (
        "module empty_checker (\n"
        "    input logic clk\n"
        ");\n"
        "\n"
        "endmodule\n"
    )


def test_duplicate_port_name_rejected() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=None,
        ports=[Signal("a", 1), Signal("a", 2)],
        checks=[],
    )
    with pytest.raises(ValueError, match="duplicate checker port name: 'a'"):
        generate_checker(spec)


def test_port_colliding_with_reset_signal_rejected() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("rst_n", 1)],
        checks=[],
    )
    with pytest.raises(ValueError, match="duplicate checker port name: 'rst_n'"):
        generate_checker(spec)


def test_duplicate_check_name_rejected() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=None,
        ports=[Signal("a", 1), Signal("b", 1)],
        checks=[
            StabilityCheck("dup", "a", "b", 1),
            StabilityCheck("dup", "b", "a", 1),
        ],
    )
    with pytest.raises(ValueError, match="duplicate checker name: 'dup'"):
        generate_checker(spec)


def test_multiple_checks_render_in_order_and_are_blank_separated() -> None:
    spec = CheckerSpec(
        name="c",
        clock="clk",
        reset=RST_N,
        ports=[Signal("done", 1), Signal("count", 8), Signal("en", 1)],
        checks=[
            ResetValueCheck("done_reset", "done", 0, 1),
            StabilityCheck("count_hold", "count", "en", 8),
        ],
    )
    text = generate_checker(spec)
    assert text.index("done_reset") < text.index("count_hold")
    assert "\n\n    // count_hold:" in text


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def _full_spec() -> CheckerSpec:
    return CheckerSpec(
        name="proto_checker",
        clock="clk",
        reset=RST_N,
        ports=[
            Signal("done", 1),
            Signal("count", 8),
            Signal("en", 1),
            Signal("req", 1),
            Signal("ack", 1),
        ],
        checks=[
            ResetValueCheck("done_reset", "done", 0, 1),
            StabilityCheck("count_hold", "count", "en", 8),
            LatencyCheck("req_ack_latency", "req", "ack", 4),
        ],
    )


def test_determinism_same_spec_same_output() -> None:
    assert generate_checker(_full_spec()) == generate_checker(_full_spec())
