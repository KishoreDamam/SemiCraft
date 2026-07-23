// SemiCraft v0.1.0
// Testbench: lfsr_tb (config hash: 869cdc1e3c02)
// Smoke testbench (stub, compile-checked only) for lfsr
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module lfsr_tb;
    logic clk;
    logic rst_n;
    logic en;
    logic [7:0] q;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    lfsr dut (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (en),
        .q     (q)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 192; watchdog_i++) @(posedge clk);
                $fatal(1, "TIMEOUT: lfsr_tb exceeded 192 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        en = 1'd0;
        rst_n = 1'd0;
        repeat (2) @(posedge clk);
        rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        en = 1'd1;
        #1;
        if (q !== 8'd5) begin
            $fatal(1, "SMOKE FAIL: q at cycle 0 expected 5, got %0d", q);
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
        if (q !== 8'd0) begin
            $fatal(1, "SMOKE FAIL: q at cycle 4 expected 0, got %0d", q);
        end
        @(negedge clk);
        en = 1'd1;
        $display("SMOKE PASS: lfsr");
        $finish;
    end

endmodule
