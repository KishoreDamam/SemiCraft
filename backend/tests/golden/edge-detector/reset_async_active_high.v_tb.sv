// SemiCraft v0.1.0
// Testbench: edge_detector_tb (config hash: 583637a620d6)
// Smoke testbench (stub, compile-checked only) for edge_detector
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module edge_detector_tb;
    logic clk;
    logic rst;
    logic d;
    logic pulse;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    edge_detector dut (
        .clk   (clk),
        .rst   (rst),
        .d     (d),
        .pulse (pulse)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Initialise inputs and assert reset
        d = 1'd0;
        rst = 1'd1;
        repeat (2) @(posedge clk);
        rst = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        d = 1'd0;
        @(negedge clk);
        d = 1'd1;
        @(negedge clk);
        d = 1'd1;
        #1;
        if (pulse !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: pulse at cycle 2 expected 1, got %0d", pulse);
        end
        @(negedge clk);
        d = 1'd0;
        #1;
        if (pulse !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: pulse at cycle 3 expected 0, got %0d", pulse);
        end
        @(negedge clk);
        d = 1'd0;
        @(negedge clk);
        d = 1'd1;
        $display("SMOKE PASS: edge_detector");
        $finish;
    end

endmodule
