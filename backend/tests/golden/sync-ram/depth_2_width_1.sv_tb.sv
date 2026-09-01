// SemiCraft v0.4.0
// Testbench: sync_ram_tb (config hash: cba02084b546)
// Smoke testbench (stub, compile-checked only) for sync_ram
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module sync_ram_tb;
    logic clk;
    logic addr;
    logic we;
    logic din;
    logic re;
    logic dout;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    sync_ram dut (
        .clk  (clk),
        .addr (addr),
        .we   (we),
        .din  (din),
        .re   (re),
        .dout (dout)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 208; watchdog_i++) @(posedge clk);
                $fatal(1, "TIMEOUT: sync_ram_tb exceeded 208 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        addr = 1'd0;
        we = 1'd0;
        din = 1'd0;
        re = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        addr = 1'd0;
        din = 1'd1;
        re = 1'd0;
        we = 1'd1;
        @(negedge clk);
        addr = 1'd1;
        din = 1'd0;
        re = 1'd0;
        we = 1'd1;
        @(negedge clk);
        addr = 1'd0;
        re = 1'd1;
        we = 1'd0;
        @(negedge clk);
        addr = 1'd1;
        #1;
        if (dout !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 3 expected 1, got %0d", dout);
        end
        @(negedge clk);
        #1;
        if (dout !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 4 expected 0, got %0d", dout);
        end
        @(negedge clk);
        addr = 1'd0;
        din = 1'd0;
        re = 1'd1;
        we = 1'd1;
        @(negedge clk);
        addr = 1'd0;
        re = 1'd1;
        we = 1'd0;
        #1;
        if (dout !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 6 expected 1, got %0d", dout);
        end
        @(negedge clk);
        addr = 1'd1;
        re = 1'd0;
        #1;
        if (dout !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 7 expected 0, got %0d", dout);
        end
        @(negedge clk);
        #1;
        if (dout !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 8 expected 0, got %0d", dout);
        end
        $display("SMOKE PASS: sync_ram");
        $finish;
    end

endmodule
