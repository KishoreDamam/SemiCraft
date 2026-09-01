// SemiCraft v0.4.0
// Testbench: sync_fifo_tb (config hash: 0bb6f2d964fc)
// Smoke testbench (stub, compile-checked only) for sync_fifo
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module sync_fifo_tb;
    logic clk;
    logic rst_n;
    logic wr_en;
    logic [7:0] wr_data;
    logic full;
    logic rd_en;
    logic [7:0] rd_data;
    logic empty;
    logic [3:0] count;

    // Free-running clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Device under test
    sync_fifo dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .wr_en   (wr_en),
        .wr_data (wr_data),
        .full    (full),
        .rd_en   (rd_en),
        .rd_data (rd_data),
        .empty   (empty),
        .count   (count)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 408; watchdog_i++) @(posedge clk);
                $fatal(1, "TIMEOUT: sync_fifo_tb exceeded 408 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        wr_en = 1'd0;
        wr_data = 8'd0;
        rd_en = 1'd0;
        rst_n = 1'd0;
        repeat (2) @(posedge clk);
        #1;
        rst_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge clk);
        #1;
        if (empty !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 0 expected 1, got %0d", empty);
        end
        if (full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: full at cycle 0 expected 0, got %0d", full);
        end
        if (count !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: count at cycle 0 expected 0, got %0d", count);
        end
        if (rd_data !== 8'd0) begin
            $fatal(1, "SMOKE FAIL: rd_data at cycle 0 expected 0, got %0d", rd_data);
        end
        @(negedge clk);
        wr_data = 8'd1;
        wr_en = 1'd1;
        @(negedge clk);
        wr_data = 8'd2;
        wr_en = 1'd1;
        @(negedge clk);
        wr_data = 8'd3;
        wr_en = 1'd1;
        @(negedge clk);
        wr_data = 8'd4;
        wr_en = 1'd1;
        @(negedge clk);
        rd_en = 1'd1;
        wr_en = 1'd0;
        #1;
        if (empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 5 expected 0, got %0d", empty);
        end
        if (full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: full at cycle 5 expected 0, got %0d", full);
        end
        if (count !== 4'd4) begin
            $fatal(1, "SMOKE FAIL: count at cycle 5 expected 4, got %0d", count);
        end
        @(negedge clk);
        #1;
        if (rd_data !== 8'd1) begin
            $fatal(1, "SMOKE FAIL: rd_data at cycle 6 expected 1, got %0d", rd_data);
        end
        if (empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 6 expected 0, got %0d", empty);
        end
        if (full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: full at cycle 6 expected 0, got %0d", full);
        end
        if (count !== 4'd3) begin
            $fatal(1, "SMOKE FAIL: count at cycle 6 expected 3, got %0d", count);
        end
        @(negedge clk);
        #1;
        if (rd_data !== 8'd2) begin
            $fatal(1, "SMOKE FAIL: rd_data at cycle 7 expected 2, got %0d", rd_data);
        end
        if (empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 7 expected 0, got %0d", empty);
        end
        if (full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: full at cycle 7 expected 0, got %0d", full);
        end
        if (count !== 4'd2) begin
            $fatal(1, "SMOKE FAIL: count at cycle 7 expected 2, got %0d", count);
        end
        @(negedge clk);
        #1;
        if (rd_data !== 8'd3) begin
            $fatal(1, "SMOKE FAIL: rd_data at cycle 8 expected 3, got %0d", rd_data);
        end
        if (empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 8 expected 0, got %0d", empty);
        end
        if (full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: full at cycle 8 expected 0, got %0d", full);
        end
        if (count !== 4'd1) begin
            $fatal(1, "SMOKE FAIL: count at cycle 8 expected 1, got %0d", count);
        end
        @(negedge clk);
        #1;
        if (rd_data !== 8'd4) begin
            $fatal(1, "SMOKE FAIL: rd_data at cycle 9 expected 4, got %0d", rd_data);
        end
        if (empty !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 9 expected 1, got %0d", empty);
        end
        if (full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: full at cycle 9 expected 0, got %0d", full);
        end
        if (count !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: count at cycle 9 expected 0, got %0d", count);
        end
        @(negedge clk);
        rd_en = 1'd0;
        wr_data = 8'd255;
        wr_en = 1'd1;
        repeat (8) @(negedge clk);
        #1;
        if (empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 18 expected 0, got %0d", empty);
        end
        if (full !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: full at cycle 18 expected 1, got %0d", full);
        end
        if (count !== 4'd8) begin
            $fatal(1, "SMOKE FAIL: count at cycle 18 expected 8, got %0d", count);
        end
        repeat (2) @(negedge clk);
        wr_en = 1'd0;
        #1;
        if (empty !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 20 expected 0, got %0d", empty);
        end
        if (full !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: full at cycle 20 expected 1, got %0d", full);
        end
        if (count !== 4'd8) begin
            $fatal(1, "SMOKE FAIL: count at cycle 20 expected 8, got %0d", count);
        end
        @(negedge clk);
        rd_en = 1'd1;
        repeat (8) @(negedge clk);
        #1;
        if (empty !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 29 expected 1, got %0d", empty);
        end
        if (full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: full at cycle 29 expected 0, got %0d", full);
        end
        if (count !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: count at cycle 29 expected 0, got %0d", count);
        end
        if (rd_data !== 8'd255) begin
            $fatal(1, "SMOKE FAIL: rd_data at cycle 29 expected 255, got %0d", rd_data);
        end
        repeat (2) @(negedge clk);
        rd_en = 1'd0;
        #1;
        if (empty !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: empty at cycle 31 expected 1, got %0d", empty);
        end
        if (full !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: full at cycle 31 expected 0, got %0d", full);
        end
        if (count !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: count at cycle 31 expected 0, got %0d", count);
        end
        if (rd_data !== 8'd255) begin
            $fatal(1, "SMOKE FAIL: rd_data at cycle 31 expected 255, got %0d", rd_data);
        end
        $display("SMOKE PASS: sync_fifo");
        $finish;
    end

    // Concurrent assertions (SVA)
    rd_data_reset_value: assert property (@(posedge clk) $rose(rst_n) |-> rd_data == 8'd0)
        else $fatal(1, "SVA FAIL: rd_data_reset_value");
    empty_after_reset: assert property (@(posedge clk) $rose(rst_n) |-> empty == 1'd1)
        else $fatal(1, "SVA FAIL: empty_after_reset");
    not_full_after_reset: assert property (@(posedge clk) $rose(rst_n) |-> full == 1'd0)
        else $fatal(1, "SVA FAIL: not_full_after_reset");
    count_zero_after_reset: assert property (@(posedge clk) $rose(rst_n) |-> count == 4'd0)
        else $fatal(1, "SVA FAIL: count_zero_after_reset");

endmodule
