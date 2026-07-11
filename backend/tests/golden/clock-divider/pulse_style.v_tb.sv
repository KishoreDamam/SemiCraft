// SemiCraft v0.1.0
// Testbench: clock_divider_tb (config hash: 716c16a4e6be)
// Smoke testbench (stub, compile-checked only) for clock_divider
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module clock_divider_tb;
    logic clk;
    logic rst_n;
    logic clk_out;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    clock_divider dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .clk_out (clk_out)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Initialise inputs and assert reset
        rst_n = 1'd0;
        repeat (2) @(posedge clk);
        rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        repeat (2) @(negedge clk);
        #1;
        if (clk_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: clk_out at cycle 1 expected 0, got %0d", clk_out);
        end
        @(negedge clk);
        #1;
        if (clk_out !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: clk_out at cycle 2 expected 1, got %0d", clk_out);
        end
        $display("SMOKE PASS: clock_divider");
        $finish;
    end

endmodule
