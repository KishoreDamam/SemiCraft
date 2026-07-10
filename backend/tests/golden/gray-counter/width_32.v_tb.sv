// SemiCraft v0.1.0
// Testbench: gray_counter_tb (config hash: 725624df68ef)
// Smoke testbench (stub, compile-checked only) for gray_counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module gray_counter_tb;
    logic clk;
    logic rst_n;
    logic en;
    logic [31:0] gray;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    gray_counter dut (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (en),
        .gray  (gray)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Initialise inputs and assert reset
        en = 1'd0;
        rst_n = 1'd0;
        repeat (2) @(posedge clk);
        rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        en = 1'd1;
        #1;
        if (gray !== 32'd0) begin
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
        if (gray !== 32'd2) begin
            $fatal(1, "SMOKE FAIL: gray at cycle 4 expected 2, got %0d", gray);
        end
        @(negedge clk);
        en = 1'd1;
        $display("SMOKE PASS: gray_counter");
        $finish;
    end

endmodule
