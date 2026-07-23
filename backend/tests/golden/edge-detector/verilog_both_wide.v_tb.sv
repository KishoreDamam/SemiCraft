// SemiCraft v0.1.0
// Testbench: edge_detector_tb (config hash: 67441c12731d)
// Smoke testbench (stub, compile-checked only) for edge_detector
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module edge_detector_tb;
    logic clk;
    logic rst_n;
    logic [3:0] d;
    logic [3:0] pulse;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    edge_detector dut (
        .clk   (clk),
        .rst_n (rst_n),
        .d     (d),
        .pulse (pulse)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                repeat (192) @(posedge clk);
                $fatal(1, "TIMEOUT: edge_detector_tb exceeded 192 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        d = 4'd0;
        rst_n = 1'd0;
        repeat (2) @(posedge clk);
        rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        d = 4'd0;
        @(negedge clk);
        d = 4'd15;
        @(negedge clk);
        d = 4'd15;
        #1;
        if (pulse !== 4'd15) begin
            $fatal(1, "SMOKE FAIL: pulse at cycle 2 expected 15, got %0d", pulse);
        end
        @(negedge clk);
        d = 4'd0;
        @(negedge clk);
        d = 4'd0;
        #1;
        if (pulse !== 4'd15) begin
            $fatal(1, "SMOKE FAIL: pulse at cycle 4 expected 15, got %0d", pulse);
        end
        @(negedge clk);
        d = 4'd15;
        $display("SMOKE PASS: edge_detector");
        $finish;
    end

endmodule
