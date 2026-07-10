// SemiCraft v0.1.0
// Testbench: debouncer_tb (config hash: afd0954e174b)
// Smoke testbench (stub, compile-checked only) for debouncer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module debouncer_tb;
    logic clk;
    logic rst;
    logic d_in;
    logic q;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    debouncer dut (
        .clk  (clk),
        .rst  (rst),
        .d_in (d_in),
        .q    (q)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Initialise inputs and assert reset
        d_in = 1'd0;
        rst = 1'd1;
        repeat (2) @(posedge clk);
        rst = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        d_in = 1'd1;
        @(negedge clk);
        d_in = 1'd0;
        @(negedge clk);
        d_in = 1'd1;
        @(negedge clk);
        d_in = 1'd0;
        @(negedge clk);
        d_in = 1'd1;
        #1;
        if (q !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: q at cycle 4 expected 1, got %0d", q);
        end
        @(negedge clk);
        d_in = 1'd0;
        @(negedge clk);
        d_in = 1'd0;
        @(negedge clk);
        d_in = 1'd0;
        #1;
        if (q !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: q at cycle 7 expected 1, got %0d", q);
        end
        $display("SMOKE PASS: debouncer");
        $finish;
    end

endmodule
