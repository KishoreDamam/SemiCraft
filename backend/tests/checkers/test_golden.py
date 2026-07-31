"""Full multi-component golden-text coverage (P3-06).

Builds one monitor, one checker (all three item families), and one
scoreboard (with wrapper) for a hypothetical req/ack module and asserts the
exact emitted SystemVerilog for all three, plus that concatenating them is
byte-identical across repeated generation (determinism end-to-end).
"""

from __future__ import annotations

from semicraft_core.checkers import (
    CheckerSpec,
    LatencyCheck,
    MonitorSpec,
    ResetPolarity,
    ResetValueCheck,
    ScoreboardSpec,
    ScoreboardWrapper,
    Signal,
    StabilityCheck,
    generate_checker,
    generate_monitor,
    generate_scoreboard,
)

RST_N = ResetPolarity(signal="rst_n", active_low=True)

_MONITOR_SPEC = MonitorSpec(
    name="req_ack_mon",
    clock="clk",
    fields=[Signal("req", 1), Signal("ack", 1), Signal("data", 8)],
    qualifier="req && ack",
)

_CHECKER_SPEC = CheckerSpec(
    name="req_ack_checker",
    clock="clk",
    reset=RST_N,
    ports=[
        Signal("busy", 1),
        Signal("data", 8),
        Signal("en", 1),
        Signal("req", 1),
        Signal("ack", 1),
    ],
    checks=[
        ResetValueCheck("busy_reset", "busy", 0, 1),
        StabilityCheck("data_hold", "data", "en", 8),
        LatencyCheck("req_ack_latency", "req", "ack", 4),
    ],
)

_SCOREBOARD_SPEC = ScoreboardSpec(
    name="req_ack_scoreboard",
    item_type="logic [7:0]",
    wrapper=ScoreboardWrapper(
        module_name="req_ack_scoreboard_wrap",
        clock="clk",
        push_signal="req",
        push_expr="data",
        compare_signal="ack",
        compare_expr="data",
        # Required: `data` is referenced by push_expr/compare_expr but is not
        # one of the three implicit ports, so without it the emitted wrapper
        # references an undeclared signal and does not compile (caught by
        # test_compile.py).
        ports=[Signal("data", 8)],
    ),
)

_EXPECTED_MONITOR = """\
module req_ack_mon (
    input logic clk,
    input logic req,
    input logic ack,
    input logic [7:0] data
);

    // Passive monitor: samples the bundle on posedge clk when req && ack
    always @(posedge clk) begin
        if (req && ack) begin
            $display("[%0t] req_ack_mon: req=%0d ack=%0d data=%0d", $time, req, ack, data);
        end
    end

endmodule
"""

_EXPECTED_CHECKER = """\
module req_ack_checker (
    input logic clk,
    input logic rst_n,
    input logic busy,
    input logic [7:0] data,
    input logic en,
    input logic req,
    input logic ack
);

    logic rst_n_prev;
    always @(posedge clk) rst_n_prev <= rst_n;

    // busy_reset: busy known value on reset deassertion
    always @(posedge clk) begin
        if (!rst_n_prev && rst_n) begin
            if (busy !== 1'd0) begin
                $error("CHECK FAIL: busy_reset: busy expected 1'd0 on reset \
deassertion, got %0d", busy);
            end
        end
    end

    // data_hold: data stable one cycle after en deasserts
    logic data_hold_enable_prev;
    logic [7:0] data_hold_signal_prev;
    always @(posedge clk) begin
        data_hold_enable_prev <= en;
        data_hold_signal_prev <= data;
    end
    always @(posedge clk) begin
        if (rst_n && !data_hold_enable_prev && (data !== data_hold_signal_prev)) begin
            $error("CHECK FAIL: data_hold: data changed while en was deasserted \
last cycle (was %0d, now %0d)", data_hold_signal_prev, data);
        end
    end

    // req_ack_latency: ack must arrive within 4 cycles of req
    logic req_ack_latency_pending;
    logic [31:0] req_ack_latency_wait;
    always @(posedge clk) begin
        if (!rst_n) begin
            req_ack_latency_pending <= 1'b0;
            req_ack_latency_wait <= 32'd0;
        end else if (req_ack_latency_pending) begin
            if (ack) begin
                req_ack_latency_pending <= 1'b0;
            end else if (req_ack_latency_wait >= 32'd4) begin
                $error("CHECK FAIL: req_ack_latency: ack did not arrive within 4 cycles of req");
                req_ack_latency_pending <= 1'b0;
            end else begin
                req_ack_latency_wait <= req_ack_latency_wait + 32'd1;
            end
        end else if (req) begin
            req_ack_latency_pending <= 1'b1;
            req_ack_latency_wait <= 32'd0;
        end
    end

endmodule
"""

_EXPECTED_SCOREBOARD = """\
class req_ack_scoreboard;

    logic [7:0] expected_q[$];
    int unsigned match_count;
    int unsigned mismatch_count;

    function new();
        match_count = 0;
        mismatch_count = 0;
    endfunction

    function void push_expected(logic [7:0] item);
        expected_q.push_back(item);
    endfunction

    function void compare(logic [7:0] actual);
        logic [7:0] expected;
        if (expected_q.size() == 0) begin
            mismatch_count++;
            $error("req_ack_scoreboard: compare() called with an empty expected queue");
            return;
        end
        expected = expected_q.pop_front();
        if (actual !== expected) begin
            mismatch_count++;
            $error("req_ack_scoreboard: mismatch: expected %0d, got %0d", expected, actual);
        end else begin
            match_count++;
        end
    endfunction

    function void report();
        $display("req_ack_scoreboard: %0d match, %0d mismatch, %0d total", \
match_count, mismatch_count, match_count + mismatch_count);
    endfunction

endclass

module req_ack_scoreboard_wrap (
    input logic clk,
    input logic req,
    input logic ack,
    input logic [7:0] data
);

    req_ack_scoreboard sb;

    initial sb = new();

    always @(posedge clk) begin
        if (req) begin
            sb.push_expected(data);
        end
        if (ack) begin
            sb.compare(data);
        end
    end

    final begin
        sb.report();
    end

endmodule
"""


def test_monitor_golden_text() -> None:
    assert generate_monitor(_MONITOR_SPEC) == _EXPECTED_MONITOR


def test_checker_golden_text() -> None:
    assert generate_checker(_CHECKER_SPEC) == _EXPECTED_CHECKER


def test_scoreboard_golden_text() -> None:
    assert generate_scoreboard(_SCOREBOARD_SPEC) == _EXPECTED_SCOREBOARD


def test_full_bundle_determinism() -> None:
    """Same three specs in -> byte-identical concatenated text out, twice."""

    def render_all() -> str:
        return (
            generate_monitor(_MONITOR_SPEC)
            + generate_checker(_CHECKER_SPEC)
            + generate_scoreboard(_SCOREBOARD_SPEC)
        )

    assert render_all() == render_all()
    assert render_all() == _EXPECTED_MONITOR + _EXPECTED_CHECKER + _EXPECTED_SCOREBOARD
