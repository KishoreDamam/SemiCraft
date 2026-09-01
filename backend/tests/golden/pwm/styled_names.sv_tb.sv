// SemiCraft v0.4.0
// Testbench: pwm_tb (config hash: 30a28f1388c6)
// Smoke testbench (stub, compile-checked only) for pwm
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module pwm_tb;
    logic p_clk;
    logic p_rst_n;
    logic [7:0] p_duty;
    logic p_pwmOut;

    // Free-running clock
    initial p_clk = 1'b0;
    always #5 p_clk = ~p_clk;

    // Device under test
    pwm dut (
        .p_clk    (p_clk),
        .p_rst_n  (p_rst_n),
        .p_duty   (p_duty),
        .p_pwmOut (p_pwmOut)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 184; watchdog_i++) @(posedge p_clk);
                $fatal(1, "TIMEOUT: pwm_tb exceeded 184 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_duty = 8'd0;
        p_rst_n = 1'd0;
        repeat (2) @(posedge p_clk);
        #1;
        p_rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_clk);
        p_duty = 8'd0;
        #1;
        if (p_pwmOut !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_pwmOut at cycle 0 expected 0, got %0d", p_pwmOut);
        end
        @(negedge p_clk);
        p_duty = 8'd128;
        #1;
        if (p_pwmOut !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_pwmOut at cycle 1 expected 1, got %0d", p_pwmOut);
        end
        @(negedge p_clk);
        p_duty = 8'd128;
        @(negedge p_clk);
        p_duty = 8'd255;
        @(negedge p_clk);
        p_duty = 8'd255;
        $display("SMOKE PASS: pwm");
        $finish;
    end

endmodule
