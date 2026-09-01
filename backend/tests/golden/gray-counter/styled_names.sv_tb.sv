// SemiCraft v0.4.0
// Testbench: gray_counter_tb (config hash: 0b6953eb14f8)
// Smoke testbench (stub, compile-checked only) for gray_counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module gray_counter_tb;
    logic p_clk;
    logic p_rst_n;
    logic p_en;
    logic [7:0] p_gray;

    // Free-running clock
    initial p_clk = 1'b0;
    always #5 p_clk = ~p_clk;

    // Device under test
    gray_counter dut (
        .p_clk   (p_clk),
        .p_rst_n (p_rst_n),
        .p_en    (p_en),
        .p_gray  (p_gray)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 192; watchdog_i++) @(posedge p_clk);
                $fatal(1, "TIMEOUT: gray_counter_tb exceeded 192 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_en = 1'd0;
        p_rst_n = 1'd0;
        repeat (2) @(posedge p_clk);
        #1;
        p_rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_clk);
        p_en = 1'd1;
        #1;
        if (p_gray !== 8'd0) begin
            $fatal(1, "SMOKE FAIL: p_gray at cycle 0 expected 0, got %0d", p_gray);
        end
        @(negedge p_clk);
        p_en = 1'd1;
        @(negedge p_clk);
        p_en = 1'd1;
        @(negedge p_clk);
        p_en = 1'd0;
        @(negedge p_clk);
        p_en = 1'd1;
        #1;
        if (p_gray !== 8'd2) begin
            $fatal(1, "SMOKE FAIL: p_gray at cycle 4 expected 2, got %0d", p_gray);
        end
        @(negedge p_clk);
        p_en = 1'd1;
        $display("SMOKE PASS: gray_counter");
        $finish;
    end

    // Concurrent assertions (SVA)
    gray_reset_value: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_gray == 8'd0)
        else $fatal(1, "SVA FAIL: gray_reset_value");
    gray_stable_when_disabled: assert property (@(posedge p_clk) disable iff (!p_rst_n) !p_en |=> $stable(p_gray))
        else $fatal(1, "SVA FAIL: gray_stable_when_disabled");

endmodule
