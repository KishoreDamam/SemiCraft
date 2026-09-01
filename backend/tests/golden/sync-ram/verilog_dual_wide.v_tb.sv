// SemiCraft v0.4.0
// Testbench: sync_ram_tb (config hash: a20114503dbf)
// Smoke testbench (stub, compile-checked only) for sync_ram
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module sync_ram_tb;
    logic clk;
    logic [11:0] waddr;
    logic we;
    logic [31:0] din;
    logic [11:0] raddr;
    logic re;
    logic [31:0] dout;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    sync_ram dut (
        .clk   (clk),
        .waddr (waddr),
        .we    (we),
        .din   (din),
        .raddr (raddr),
        .re    (re),
        .dout  (dout)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 224; watchdog_i++) @(posedge clk);
                $fatal(1, "TIMEOUT: sync_ram_tb exceeded 224 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        waddr = 12'd0;
        we = 1'd0;
        din = 32'd0;
        raddr = 12'd0;
        re = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        din = 32'd17;
        re = 1'd0;
        waddr = 12'd0;
        we = 1'd1;
        @(negedge clk);
        din = 32'd34;
        re = 1'd0;
        waddr = 12'd1;
        we = 1'd1;
        @(negedge clk);
        din = 32'd51;
        re = 1'd0;
        waddr = 12'd4095;
        we = 1'd1;
        @(negedge clk);
        raddr = 12'd0;
        re = 1'd1;
        we = 1'd0;
        @(negedge clk);
        raddr = 12'd1;
        #1;
        if (dout !== 32'd17) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 4 expected 17, got %0d", dout);
        end
        @(negedge clk);
        raddr = 12'd4095;
        #1;
        if (dout !== 32'd34) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 5 expected 34, got %0d", dout);
        end
        @(negedge clk);
        #1;
        if (dout !== 32'd51) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 6 expected 51, got %0d", dout);
        end
        @(negedge clk);
        din = 32'd4294967278;
        raddr = 12'd0;
        re = 1'd1;
        waddr = 12'd0;
        we = 1'd1;
        @(negedge clk);
        raddr = 12'd0;
        re = 1'd1;
        we = 1'd0;
        #1;
        if (dout !== 32'd17) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 8 expected 17, got %0d", dout);
        end
        @(negedge clk);
        raddr = 12'd4095;
        re = 1'd0;
        #1;
        if (dout !== 32'd4294967278) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 9 expected 4294967278, got %0d", dout);
        end
        @(negedge clk);
        #1;
        if (dout !== 32'd4294967278) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 10 expected 4294967278, got %0d", dout);
        end
        $display("SMOKE PASS: sync_ram");
        $finish;
    end

endmodule
