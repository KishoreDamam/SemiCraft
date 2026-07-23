// SemiCraft v0.1.0
// Testbench: lfsr_tb (config hash: fabf7568e1ae)
// Smoke testbench (stub, compile-checked only) for lfsr
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module lfsr_tb;
    logic clk;
    logic rst;
    logic en;
    logic [7:0] q;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    lfsr dut (
        .clk (clk),
        .rst (rst),
        .en  (en),
        .q   (q)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                repeat (192) @(posedge clk);
                $fatal(1, "TIMEOUT: lfsr_tb exceeded 192 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        en = 1'd0;
        rst = 1'd1;
        repeat (2) @(posedge clk);
        rst = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        en = 1'd1;
        #1;
        if (q !== 8'd1) begin
            $fatal(1, "SMOKE FAIL: q at cycle 0 expected 1, got %0d", q);
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
