// SemiCraft v0.1.0
// Testbench: lfsr_tb (config hash: 18a744e704dc)
// Smoke testbench (stub, compile-checked only) for lfsr
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module lfsr_tb;
    logic clk;
    logic rst_n;
    logic en;
    logic out;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    lfsr dut (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (en),
        .out   (out)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 192; watchdog_i++) @(posedge clk);
                $fatal(1, "TIMEOUT: lfsr_tb exceeded 192 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        en = 1'd0;
        rst_n = 1'd0;
        repeat (2) @(posedge clk);
        #1;
        rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        en = 1'd1;
        #1;
        if (out !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: out at cycle 0 expected 1, got %0d", out);
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
        if (out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: out at cycle 4 expected 0, got %0d", out);
        end
        @(negedge clk);
        en = 1'd1;
        $display("SMOKE PASS: lfsr");
        $finish;
    end

    // Concurrent assertions (SVA)
    out_reset_value: assert property (@(posedge clk) $rose(rst_n) |-> out == 1'd1)
        else $fatal(1, "SVA FAIL: out_reset_value");
    out_stable_when_disabled: assert property (@(posedge clk) disable iff (!rst_n) !en |=> $stable(out))
        else $fatal(1, "SVA FAIL: out_stable_when_disabled");

endmodule
