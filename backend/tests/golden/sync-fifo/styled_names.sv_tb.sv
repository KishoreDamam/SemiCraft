// SemiCraft v0.4.0
// Testbench: sync_fifo_tb (config hash: aa4576c29109)
// Smoke testbench (stub, compile-checked only) for sync_fifo
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module sync_fifo_tb;
    logic p_clk;
    logic p_rst_n;
    logic p_wrEn;
    logic [7:0] p_wrData;
    logic p_full;
    logic p_rdEn;
    logic [7:0] p_rdData;
    logic p_empty;
    logic [3:0] p_count;

    // Free-running clock
    initial p_clk = 1'b0;
    always #5 p_clk = ~p_clk;

    // Device under test
    sync_fifo dut (
        .p_clk    (p_clk),
        .p_rst_n  (p_rst_n),
        .p_wrEn   (p_wrEn),
        .p_wrData (p_wrData),
        .p_full   (p_full),
        .p_rdEn   (p_rdEn),
        .p_rdData (p_rdData),
        .p_empty  (p_empty),
        .p_count  (p_count)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 408; watchdog_i++) @(posedge p_clk);
                $fatal(1, "TIMEOUT: sync_fifo_tb exceeded 408 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_wrEn = 1'd0;
        p_wrData = 8'd0;
        p_rdEn = 1'd0;
        p_rst_n = 1'd0;
        repeat (2) @(posedge p_clk);
        #1;
        p_rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_clk);
        #1;
        if (p_empty !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 0 expected 1, got %0d", p_empty);
        end
        if (p_full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 0 expected 0, got %0d", p_full);
        end
        if (p_count !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 0 expected 0, got %0d", p_count);
        end
        if (p_rdData !== 8'd0) begin
            $fatal(1, "SMOKE FAIL: p_rdData at cycle 0 expected 0, got %0d", p_rdData);
        end
        @(negedge p_clk);
        p_wrData = 8'd1;
        p_wrEn = 1'd1;
        @(negedge p_clk);
        p_wrData = 8'd2;
        p_wrEn = 1'd1;
        @(negedge p_clk);
        p_wrData = 8'd3;
        p_wrEn = 1'd1;
        @(negedge p_clk);
        p_wrData = 8'd4;
        p_wrEn = 1'd1;
        @(negedge p_clk);
        p_rdEn = 1'd1;
        p_wrEn = 1'd0;
        #1;
        if (p_empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 5 expected 0, got %0d", p_empty);
        end
        if (p_full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 5 expected 0, got %0d", p_full);
        end
        if (p_count !== 4'd4) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 5 expected 4, got %0d", p_count);
        end
        @(negedge p_clk);
        #1;
        if (p_rdData !== 8'd1) begin
            $fatal(1, "SMOKE FAIL: p_rdData at cycle 6 expected 1, got %0d", p_rdData);
        end
        if (p_empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 6 expected 0, got %0d", p_empty);
        end
        if (p_full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 6 expected 0, got %0d", p_full);
        end
        if (p_count !== 4'd3) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 6 expected 3, got %0d", p_count);
        end
        @(negedge p_clk);
        #1;
        if (p_rdData !== 8'd2) begin
            $fatal(1, "SMOKE FAIL: p_rdData at cycle 7 expected 2, got %0d", p_rdData);
        end
        if (p_empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 7 expected 0, got %0d", p_empty);
        end
        if (p_full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 7 expected 0, got %0d", p_full);
        end
        if (p_count !== 4'd2) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 7 expected 2, got %0d", p_count);
        end
        @(negedge p_clk);
        #1;
        if (p_rdData !== 8'd3) begin
            $fatal(1, "SMOKE FAIL: p_rdData at cycle 8 expected 3, got %0d", p_rdData);
        end
        if (p_empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 8 expected 0, got %0d", p_empty);
        end
        if (p_full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 8 expected 0, got %0d", p_full);
        end
        if (p_count !== 4'd1) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 8 expected 1, got %0d", p_count);
        end
        @(negedge p_clk);
        #1;
        if (p_rdData !== 8'd4) begin
            $fatal(1, "SMOKE FAIL: p_rdData at cycle 9 expected 4, got %0d", p_rdData);
        end
        if (p_empty !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 9 expected 1, got %0d", p_empty);
        end
        if (p_full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 9 expected 0, got %0d", p_full);
        end
        if (p_count !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 9 expected 0, got %0d", p_count);
        end
        @(negedge p_clk);
        p_rdEn = 1'd0;
        p_wrData = 8'd255;
        p_wrEn = 1'd1;
        repeat (8) @(negedge p_clk);
        #1;
        if (p_empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 18 expected 0, got %0d", p_empty);
        end
        if (p_full !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 18 expected 1, got %0d", p_full);
        end
        if (p_count !== 4'd8) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 18 expected 8, got %0d", p_count);
        end
        repeat (2) @(negedge p_clk);
        p_wrEn = 1'd0;
        #1;
        if (p_empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 20 expected 0, got %0d", p_empty);
        end
        if (p_full !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 20 expected 1, got %0d", p_full);
        end
        if (p_count !== 4'd8) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 20 expected 8, got %0d", p_count);
        end
        @(negedge p_clk);
        p_rdEn = 1'd1;
        repeat (8) @(negedge p_clk);
        #1;
        if (p_empty !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 29 expected 1, got %0d", p_empty);
        end
        if (p_full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 29 expected 0, got %0d", p_full);
        end
        if (p_count !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 29 expected 0, got %0d", p_count);
        end
        if (p_rdData !== 8'd255) begin
            $fatal(1, "SMOKE FAIL: p_rdData at cycle 29 expected 255, got %0d", p_rdData);
        end
        repeat (2) @(negedge p_clk);
        p_rdEn = 1'd0;
        #1;
        if (p_empty !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_empty at cycle 31 expected 1, got %0d", p_empty);
        end
        if (p_full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_full at cycle 31 expected 0, got %0d", p_full);
        end
        if (p_count !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: p_count at cycle 31 expected 0, got %0d", p_count);
        end
        if (p_rdData !== 8'd255) begin
            $fatal(1, "SMOKE FAIL: p_rdData at cycle 31 expected 255, got %0d", p_rdData);
        end
        $display("SMOKE PASS: sync_fifo");
        $finish;
    end

    // Concurrent assertions (SVA)
    rd_data_reset_value: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_rdData == 8'd0)
        else $fatal(1, "SVA FAIL: rd_data_reset_value");
    empty_after_reset: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_empty == 1'd1)
        else $fatal(1, "SVA FAIL: empty_after_reset");
    not_full_after_reset: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_full == 1'd0)
        else $fatal(1, "SVA FAIL: not_full_after_reset");
    count_zero_after_reset: assert property (@(posedge p_clk) $rose(p_rst_n) |-> p_count == 4'd0)
        else $fatal(1, "SVA FAIL: count_zero_after_reset");

endmodule
