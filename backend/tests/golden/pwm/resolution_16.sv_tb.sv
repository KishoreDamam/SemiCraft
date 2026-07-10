// SemiCraft v0.1.0
// Testbench: pwm_tb (config hash: 2490f028d4d5)
// Smoke testbench (stub, compile-checked only) for pwm
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module pwm_tb;
    logic clk;
    logic rst_n;
    logic [15:0] duty;
    logic pwm_out;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    pwm dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .duty    (duty),
        .pwm_out (pwm_out)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Initialise inputs and assert reset
        duty = 16'd0;
        rst_n = 1'd0;
        repeat (2) @(posedge clk);
        rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        duty = 16'd0;
        #1;
        if (pwm_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: pwm_out at cycle 0 expected 0, got %0d", pwm_out);
        end
        @(negedge clk);
        duty = 16'd32768;
        #1;
        if (pwm_out !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: pwm_out at cycle 1 expected 1, got %0d", pwm_out);
        end
        @(negedge clk);
        duty = 16'd32768;
        @(negedge clk);
        duty = 16'd65535;
        @(negedge clk);
        duty = 16'd65535;
        $display("SMOKE PASS: pwm");
        $finish;
    end

endmodule
