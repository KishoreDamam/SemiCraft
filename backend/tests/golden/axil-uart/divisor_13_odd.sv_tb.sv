// SemiCraft v0.4.0
// Testbench: axil_uart_tb (config hash: 28a987250c5b)
// Smoke testbench (stub, compile-checked only) for axil_uart
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_uart_tb;
    logic aclk;
    logic areset_n;
    logic [3:0] awaddr;
    logic awvalid;
    logic awready;
    logic [31:0] wdata;
    logic [3:0] wstrb;
    logic wvalid;
    logic wready;
    logic [1:0] bresp;
    logic bvalid;
    logic bready;
    logic [3:0] araddr;
    logic arvalid;
    logic arready;
    logic [31:0] rdata;
    logic [1:0] rresp;
    logic rvalid;
    logic rready;
    logic uart_rx;
    logic uart_tx;

    // Free-running clock
    initial aclk = 1'b0;
    always #5 aclk = ~aclk;

    // Device under test
    axil_uart dut (
        .aclk     (aclk),
        .areset_n (areset_n),
        .awaddr   (awaddr),
        .awvalid  (awvalid),
        .awready  (awready),
        .wdata    (wdata),
        .wstrb    (wstrb),
        .wvalid   (wvalid),
        .wready   (wready),
        .bresp    (bresp),
        .bvalid   (bvalid),
        .bready   (bready),
        .araddr   (araddr),
        .arvalid  (arvalid),
        .arready  (arready),
        .rdata    (rdata),
        .rresp    (rresp),
        .rvalid   (rvalid),
        .rready   (rready),
        .uart_rx  (uart_rx),
        .uart_tx  (uart_tx)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 2408; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_uart_tb exceeded 2408 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        awaddr = 4'd0;
        awvalid = 1'd0;
        wdata = 32'd0;
        wstrb = 4'd0;
        wvalid = 1'd0;
        bready = 1'd0;
        araddr = 4'd0;
        arvalid = 1'd0;
        rready = 1'd0;
        uart_rx = 1'd0;
        areset_n = 1'd0;
        repeat (2) @(posedge aclk);
        #1;
        areset_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge aclk);
        uart_rx = 1'd1;
        #1;
        if (uart_tx !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 0 expected 1, got %0d", uart_tx);
        end
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 0 expected 0, got %0d", bvalid);
        end
        if (rvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 0 expected 0, got %0d", rvalid);
        end
        @(negedge aclk);
        araddr = 4'd12;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 2 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd13) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 2 expected 13, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 2 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 4'd4;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd75;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 5 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 5 expected 0, got %0d", bresp);
        end
        @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 6 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (uart_tx !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 7 expected 0, got %0d", uart_tx);
        end
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 7 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd1) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 7 expected 1, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 7 expected 0, got %0d", rresp);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 20 expected 1, got %0d", uart_tx);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 33 expected 1, got %0d", uart_tx);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 46 expected 0, got %0d", uart_tx);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 59 expected 1, got %0d", uart_tx);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 72 expected 0, got %0d", uart_tx);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 85 expected 0, got %0d", uart_tx);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 98 expected 1, got %0d", uart_tx);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 111 expected 0, got %0d", uart_tx);
        end
        repeat (13) @(negedge aclk);
        #1;
        if (uart_tx !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 124 expected 1, got %0d", uart_tx);
        end
        repeat (12) @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (uart_tx !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: uart_tx at cycle 136 expected 1, got %0d", uart_tx);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 137 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 137 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 137 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        uart_rx = 1'd0;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd1;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd0;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd1;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd1;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd0;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd1;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd0;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd0;
        repeat (13) @(negedge aclk);
        uart_rx = 1'd1;
        repeat (19) @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 275 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd2) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 275 expected 2, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 275 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 4'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 277 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd45) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 277 expected 45, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 277 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 4'd0;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd2;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 280 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 280 expected 0, got %0d", bresp);
        end
        @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 281 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 282 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 282 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 282 expected 0, got %0d", rresp);
        end
        $display("SMOKE PASS: axil_uart");
        $finish;
    end

    // Concurrent assertions (SVA)
    tx_idles_high_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> uart_tx == 1'd1)
        else $fatal(1, "SVA FAIL: tx_idles_high_after_reset");
    bvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");
    rvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> rvalid == 1'd0)
        else $fatal(1, "SVA FAIL: rvalid_idle_after_reset");

endmodule
