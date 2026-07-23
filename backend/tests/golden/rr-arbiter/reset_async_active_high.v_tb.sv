// SemiCraft v0.1.0
// Testbench: rr_arbiter_tb (config hash: 6c80fc9b86d4)
// Smoke testbench (stub, compile-checked only) for rr_arbiter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module rr_arbiter_tb;
    logic clk;
    logic rst;
    logic [3:0] req;
    logic [3:0] grant;
    logic grant_valid;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    rr_arbiter dut (
        .clk         (clk),
        .rst         (rst),
        .req         (req),
        .grant       (grant),
        .grant_valid (grant_valid)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                repeat (224) @(posedge clk);
                $fatal(1, "TIMEOUT: rr_arbiter_tb exceeded 224 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        req = 4'd0;
        rst = 1'd1;
        repeat (2) @(posedge clk);
        rst = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        req = 4'd0;
        @(negedge clk);
        req = 4'd1;
        @(negedge clk);
        req = 4'd1;
        #1;
        if (grant_valid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: grant_valid at cycle 2 expected 1, got %0d", grant_valid);
        end
        if (grant !== 4'd1) begin
            $fatal(1, "SMOKE FAIL: grant at cycle 2 expected 1, got %0d", grant);
        end
        @(negedge clk);
        req = 4'd15;
        @(negedge clk);
        req = 4'd15;
        @(negedge clk);
        req = 4'd15;
        @(negedge clk);
        req = 4'd15;
        @(negedge clk);
        req = 4'd0;
        @(negedge clk);
        req = 4'd8;
        #1;
        if (grant_valid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: grant_valid at cycle 8 expected 0, got %0d", grant_valid);
        end
        @(negedge clk);
        req = 4'd8;
        $display("SMOKE PASS: rr_arbiter");
        $finish;
    end

endmodule
