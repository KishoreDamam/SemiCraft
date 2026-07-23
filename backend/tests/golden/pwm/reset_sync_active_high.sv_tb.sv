// SemiCraft v0.1.0
// Testbench: pwm_tb (config hash: 574cb551084d)
// Smoke testbench (stub, compile-checked only) for pwm
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module pwm_tb;
    logic clk;
    logic rst;
    logic [7:0] duty;
    logic pwm_out;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    pwm dut (
        .clk     (clk),
        .rst     (rst),
        .duty    (duty),
        .pwm_out (pwm_out)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                repeat (184) @(posedge clk);
                $fatal(1, "TIMEOUT: pwm_tb exceeded 184 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        duty = 8'd0;
        rst = 1'd1;
        repeat (2) @(posedge clk);
        rst = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        duty = 8'd0;
        #1;
        if (pwm_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: pwm_out at cycle 0 expected 0, got %0d", pwm_out);
        end
        @(negedge clk);
        duty = 8'd128;
        #1;
        if (pwm_out !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: pwm_out at cycle 1 expected 1, got %0d", pwm_out);
        end
        @(negedge clk);
        duty = 8'd128;
        @(negedge clk);
        duty = 8'd255;
        @(negedge clk);
        duty = 8'd255;
        $display("SMOKE PASS: pwm");
        $finish;
    end

endmodule
