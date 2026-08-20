// SemiCraft v0.3.0
// Testbench: gray_counter_tb (config hash: a2abbef65194)
// Smoke testbench (stub, compile-checked only) for gray_counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module gray_counter_tb;
    logic clk;
    logic rst;
    logic en;
    logic [2:0] gray;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    gray_counter dut (
        .clk  (clk),
        .rst  (rst),
        .en   (en),
        .gray (gray)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 192; watchdog_i++) @(posedge clk);
                $fatal(1, "TIMEOUT: gray_counter_tb exceeded 192 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        en = 1'd0;
        rst = 1'd1;
        repeat (2) @(posedge clk);
        #1;
        rst = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        en = 1'd1;
        #1;
        if (gray !== 3'd0) begin
            $fatal(1, "SMOKE FAIL: gray at cycle 0 expected 0, got %0d", gray);
        end
        @(negedge clk);
        en = 1'd1;
        @(negedge clk);
        en = 1'd1;
        @(negedge clk);
        en = 1'd0;
        @(negedge clk);
        en = 1'd1;
        #1;
        if (gray !== 3'd2) begin
            $fatal(1, "SMOKE FAIL: gray at cycle 4 expected 2, got %0d", gray);
        end
        @(negedge clk);
        en = 1'd1;
        $display("SMOKE PASS: gray_counter");
        $finish;
    end

    // Concurrent assertions (SVA)
    gray_reset_value: assert property (@(posedge clk) $fell(rst) |-> gray == 3'd0)
        else $fatal(1, "SVA FAIL: gray_reset_value");
    gray_stable_when_disabled: assert property (@(posedge clk) disable iff (rst) !en |=> $stable(gray))
        else $fatal(1, "SVA FAIL: gray_stable_when_disabled");

endmodule
