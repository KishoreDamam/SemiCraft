// SemiCraft v0.4.0
// Testbench: sync_ram_tb (config hash: 8d9d7571c91c)
// Smoke testbench (stub, compile-checked only) for sync_ram
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module sync_ram_tb;
    logic clk;
    logic [9:0] addr;
    logic we;
    logic [63:0] din;
    logic re;
    logic [63:0] dout;

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
                for (watchdog_i = 0; watchdog_i < 224; watchdog_i++) @(posedge clk);
                $fatal(1, "TIMEOUT: sync_ram_tb exceeded 224 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        addr = 10'd0;
        we = 1'd0;
        din = 64'd0;
        re = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        addr = 10'd0;
        din = 64'd17;
        re = 1'd0;
        we = 1'd1;
        @(negedge clk);
        addr = 10'd1;
        din = 64'd34;
        re = 1'd0;
        we = 1'd1;
        @(negedge clk);
        addr = 10'd1023;
        din = 64'd51;
        re = 1'd0;
        we = 1'd1;
        @(negedge clk);
        addr = 10'd0;
        re = 1'd1;
        we = 1'd0;
        @(negedge clk);
        addr = 10'd1;
        #1;
        if (dout !== 64'd17) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 4 expected 17, got %0d", dout);
        end
        @(negedge clk);
        addr = 10'd1023;
        #1;
        if (dout !== 64'd34) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 5 expected 34, got %0d", dout);
        end
        @(negedge clk);
        #1;
        if (dout !== 64'd51) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 6 expected 51, got %0d", dout);
        end
        @(negedge clk);
        addr = 10'd0;
        din = 64'd18446744073709551598;
        re = 1'd1;
        we = 1'd1;
        @(negedge clk);
        addr = 10'd0;
        re = 1'd1;
        we = 1'd0;
        #1;
        if (dout !== 64'd17) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 8 expected 17, got %0d", dout);
        end
        @(negedge clk);
        addr = 10'd1023;
        re = 1'd0;
        #1;
        if (dout !== 64'd18446744073709551598) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 9 expected 18446744073709551598, got %0d", dout);
        end
        @(negedge clk);
        #1;
        if (dout !== 64'd18446744073709551598) begin
            $fatal(1, "SMOKE FAIL: dout at cycle 10 expected 18446744073709551598, got %0d", dout);
        end
        $display("SMOKE PASS: sync_ram");
        $finish;
    end

endmodule
