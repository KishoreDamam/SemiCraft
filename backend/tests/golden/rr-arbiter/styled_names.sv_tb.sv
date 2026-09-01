// SemiCraft v0.4.0
// Testbench: rr_arbiter_tb (config hash: b56dc4a4ccc9)
// Smoke testbench (stub, compile-checked only) for rr_arbiter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module rr_arbiter_tb;
    logic p_clk;
    logic p_rst_n;
    logic [3:0] p_req;
    logic [3:0] p_grant;
    logic p_grantValid;

    // Free-running clock
    initial p_clk = 1'b0;
    always #5 p_clk = ~p_clk;

    // Device under test
    rr_arbiter dut (
        .p_clk        (p_clk),
        .p_rst_n      (p_rst_n),
        .p_req        (p_req),
        .p_grant      (p_grant),
        .p_grantValid (p_grantValid)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 224; watchdog_i++) @(posedge p_clk);
                $fatal(1, "TIMEOUT: rr_arbiter_tb exceeded 224 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_req = 4'd0;
        p_rst_n = 1'd0;
        repeat (2) @(posedge p_clk);
        #1;
        p_rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_clk);
        p_req = 4'd0;
        @(negedge p_clk);
        p_req = 4'd1;
        @(negedge p_clk);
        p_req = 4'd1;
        #1;
        if (p_grantValid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_grantValid at cycle 2 expected 1, got %0d", p_grantValid);
        end
        if (p_grant !== 4'd1) begin
            $fatal(1, "SMOKE FAIL: p_grant at cycle 2 expected 1, got %0d", p_grant);
        end
        @(negedge p_clk);
        p_req = 4'd15;
        @(negedge p_clk);
        p_req = 4'd15;
        @(negedge p_clk);
        p_req = 4'd15;
        @(negedge p_clk);
        p_req = 4'd15;
        @(negedge p_clk);
        p_req = 4'd0;
        @(negedge p_clk);
        p_req = 4'd8;
        #1;
        if (p_grantValid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_grantValid at cycle 8 expected 0, got %0d", p_grantValid);
        end
        @(negedge p_clk);
        p_req = 4'd8;
        $display("SMOKE PASS: rr_arbiter");
        $finish;
    end

    // Concurrent assertions (SVA)
    grant_onehot0: assert property (@(posedge p_clk) disable iff (!p_rst_n) $onehot0(p_grant))
        else $fatal(1, "SVA FAIL: grant_onehot0");
    grant_reset_value: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_grant == 4'd0)
        else $fatal(1, "SVA FAIL: grant_reset_value");

endmodule
