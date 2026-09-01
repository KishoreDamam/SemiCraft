// SemiCraft v0.4.0
// Testbench: sync_ram_tb (config hash: 9e0ede76a0d6)
// Smoke testbench (stub, compile-checked only) for sync_ram
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module sync_ram_tb;
    logic p_clk;
    logic [7:0] p_addr;
    logic p_we;
    logic [7:0] p_din;
    logic p_re;
    logic [7:0] p_dout;

    // Free-running clock
    initial p_clk = 1'b0;
    always #5 p_clk = ~p_clk;

    // Device under test
    sync_ram dut (
        .p_clk  (p_clk),
        .p_addr (p_addr),
        .p_we   (p_we),
        .p_din  (p_din),
        .p_re   (p_re),
        .p_dout (p_dout)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 224; watchdog_i++) @(posedge p_clk);
                $fatal(1, "TIMEOUT: sync_ram_tb exceeded 224 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_addr = 8'd0;
        p_we = 1'd0;
        p_din = 8'd0;
        p_re = 1'd0;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_clk);
        p_addr = 8'd0;
        p_din = 8'd17;
        p_re = 1'd0;
        p_we = 1'd1;
        @(negedge p_clk);
        p_addr = 8'd1;
        p_din = 8'd34;
        p_re = 1'd0;
        p_we = 1'd1;
        @(negedge p_clk);
        p_addr = 8'd255;
        p_din = 8'd51;
        p_re = 1'd0;
        p_we = 1'd1;
        @(negedge p_clk);
        p_addr = 8'd0;
        p_re = 1'd1;
        p_we = 1'd0;
        @(negedge p_clk);
        p_addr = 8'd1;
        #1;
        if (p_dout !== 8'd17) begin
            $fatal(1, "SMOKE FAIL: p_dout at cycle 4 expected 17, got %0d", p_dout);
        end
        @(negedge p_clk);
        p_addr = 8'd255;
        #1;
        if (p_dout !== 8'd34) begin
            $fatal(1, "SMOKE FAIL: p_dout at cycle 5 expected 34, got %0d", p_dout);
        end
        @(negedge p_clk);
        #1;
        if (p_dout !== 8'd51) begin
            $fatal(1, "SMOKE FAIL: p_dout at cycle 6 expected 51, got %0d", p_dout);
        end
        @(negedge p_clk);
        p_addr = 8'd0;
        p_din = 8'd238;
        p_re = 1'd1;
        p_we = 1'd1;
        @(negedge p_clk);
        p_addr = 8'd0;
        p_re = 1'd1;
        p_we = 1'd0;
        #1;
        if (p_dout !== 8'd17) begin
            $fatal(1, "SMOKE FAIL: p_dout at cycle 8 expected 17, got %0d", p_dout);
        end
        @(negedge p_clk);
        p_addr = 8'd255;
        p_re = 1'd0;
        #1;
        if (p_dout !== 8'd238) begin
            $fatal(1, "SMOKE FAIL: p_dout at cycle 9 expected 238, got %0d", p_dout);
        end
        @(negedge p_clk);
        #1;
        if (p_dout !== 8'd238) begin
            $fatal(1, "SMOKE FAIL: p_dout at cycle 10 expected 238, got %0d", p_dout);
        end
        $display("SMOKE PASS: sync_ram");
        $finish;
    end

endmodule
