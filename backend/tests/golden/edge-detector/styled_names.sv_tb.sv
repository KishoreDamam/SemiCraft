// SemiCraft v0.4.0
// Testbench: edge_detector_tb (config hash: 6c652ad52515)
// Smoke testbench (stub, compile-checked only) for edge_detector
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module edge_detector_tb;
    logic p_clk;
    logic p_rst_n;
    logic p_d;
    logic p_pulse;

    // Free-running clock
    initial p_clk = 1'b0;
    always #5 p_clk = ~p_clk;

    // Device under test
    edge_detector dut (
        .p_clk   (p_clk),
        .p_rst_n (p_rst_n),
        .p_d     (p_d),
        .p_pulse (p_pulse)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 192; watchdog_i++) @(posedge p_clk);
                $fatal(1, "TIMEOUT: edge_detector_tb exceeded 192 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_d = 1'd0;
        p_rst_n = 1'd0;
        repeat (2) @(posedge p_clk);
        #1;
        p_rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_clk);
        p_d = 1'd0;
        @(negedge p_clk);
        p_d = 1'd1;
        @(negedge p_clk);
        p_d = 1'd1;
        #1;
        if (p_pulse !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_pulse at cycle 2 expected 1, got %0d", p_pulse);
        end
        @(negedge p_clk);
        p_d = 1'd0;
        #1;
        if (p_pulse !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_pulse at cycle 3 expected 0, got %0d", p_pulse);
        end
        @(negedge p_clk);
        p_d = 1'd0;
        @(negedge p_clk);
        p_d = 1'd1;
        $display("SMOKE PASS: edge_detector");
        $finish;
    end

    // Concurrent assertions (SVA)
    pulse_reset_value: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_pulse == 1'd0)
        else $fatal(1, "SVA FAIL: pulse_reset_value");

endmodule
