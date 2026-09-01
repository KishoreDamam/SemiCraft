// SemiCraft v0.4.0
// Testbench: clock_divider_tb (config hash: f93ac723f3c3)
// Smoke testbench (stub, compile-checked only) for clock_divider
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module clock_divider_tb;
    logic p_clk;
    logic p_rst_n;
    logic p_clkOut;

    // Free-running clock
    initial p_clk = 1'b0;
    always #5 p_clk = ~p_clk;

    // Device under test
    clock_divider dut (
        .p_clk    (p_clk),
        .p_rst_n  (p_rst_n),
        .p_clkOut (p_clkOut)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 176; watchdog_i++) @(posedge p_clk);
                $fatal(1, "TIMEOUT: clock_divider_tb exceeded 176 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_rst_n = 1'd0;
        repeat (2) @(posedge p_clk);
        #1;
        p_rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_clk);
        #1;
        if (p_clkOut !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_clkOut at cycle 0 expected 0, got %0d", p_clkOut);
        end
        @(negedge p_clk);
        #1;
        if (p_clkOut !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_clkOut at cycle 1 expected 1, got %0d", p_clkOut);
        end
        $display("SMOKE PASS: clock_divider");
        $finish;
    end

    // Concurrent assertions (SVA)
    clk_out_reset_value: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_clkOut == 1'd0)
        else $fatal(1, "SVA FAIL: clk_out_reset_value");

endmodule
