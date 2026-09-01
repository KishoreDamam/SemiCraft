// SemiCraft v0.4.0
// Testbench: debouncer_tb (config hash: 25b930679f39)
// Smoke testbench (stub, compile-checked only) for debouncer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module debouncer_tb;
    logic p_clk;
    logic p_rst_n;
    logic p_dIn;
    logic p_q;

    // Free-running clock
    initial p_clk = 1'b0;
    always #5 p_clk = ~p_clk;

    // Device under test
    debouncer dut (
        .p_clk   (p_clk),
        .p_rst_n (p_rst_n),
        .p_dIn   (p_dIn),
        .p_q     (p_q)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 208; watchdog_i++) @(posedge p_clk);
                $fatal(1, "TIMEOUT: debouncer_tb exceeded 208 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_dIn = 1'd0;
        p_rst_n = 1'd0;
        repeat (2) @(posedge p_clk);
        #1;
        p_rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_clk);
        p_dIn = 1'd1;
        @(negedge p_clk);
        p_dIn = 1'd0;
        @(negedge p_clk);
        p_dIn = 1'd1;
        @(negedge p_clk);
        p_dIn = 1'd0;
        @(negedge p_clk);
        p_dIn = 1'd1;
        #1;
        if (p_q !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_q at cycle 4 expected 1, got %0d", p_q);
        end
        @(negedge p_clk);
        p_dIn = 1'd0;
        @(negedge p_clk);
        p_dIn = 1'd0;
        @(negedge p_clk);
        p_dIn = 1'd0;
        #1;
        if (p_q !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_q at cycle 7 expected 1, got %0d", p_q);
        end
        $display("SMOKE PASS: debouncer");
        $finish;
    end

    // Concurrent assertions (SVA)
    q_reset_value: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_q == 1'd1)
        else $fatal(1, "SVA FAIL: q_reset_value");

endmodule
