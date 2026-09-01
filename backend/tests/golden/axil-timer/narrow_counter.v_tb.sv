// SemiCraft v0.4.0
// Testbench: axil_timer_tb (config hash: 60dfc6337525)
// Smoke testbench (stub, compile-checked only) for axil_timer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_timer_tb;
    logic aclk;
    logic areset_n;
    logic [4:0] awaddr;
    logic awvalid;
    logic awready;
    logic [31:0] wdata;
    logic [3:0] wstrb;
    logic wvalid;
    logic wready;
    logic [1:0] bresp;
    logic bvalid;
    logic bready;
    logic [4:0] araddr;
    logic arvalid;
    logic arready;
    logic [31:0] rdata;
    logic [1:0] rresp;
    logic rvalid;
    logic rready;
    logic irq;

    // Free-running clock
    initial aclk = 1'b0;
    always #5 aclk = ~aclk;

    // Device under test
    axil_timer dut (
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
        .irq      (irq)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 768; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_timer_tb exceeded 768 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        awaddr = 5'd0;
        awvalid = 1'd0;
        wdata = 32'd0;
        wstrb = 4'd0;
        wvalid = 1'd0;
        bready = 1'd0;
        araddr = 5'd0;
        arvalid = 1'd0;
        rready = 1'd0;
        areset_n = 1'd0;
        repeat (2) @(posedge aclk);
        #1;
        areset_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 0 expected 0, got %0d", bvalid);
        end
        if (rvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 0 expected 0, got %0d", rvalid);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 0 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        awaddr = 5'd12;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd1;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 3 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 3 expected 0, got %0d", bresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 3 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        awaddr = 5'd4;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd3;
        wstrb = 4'd15;
        wvalid = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 4 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 6 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 6 expected 0, got %0d", bresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 6 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        araddr = 5'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 7 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 8 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd3) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 8 expected 3, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 8 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 5'd0;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd7;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 11 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 11 expected 0, got %0d", bresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 11 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 12 expected 0, got %0d", bvalid);
        end
        repeat (7) @(negedge aclk);
        #1;
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 19 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        #1;
        if (irq !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 20 expected 1, got %0d", irq);
        end
        @(negedge aclk);
        araddr = 5'd16;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 22 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd1) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 22 expected 1, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 22 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 5'd0;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd0;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 25 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 25 expected 0, got %0d", bresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 25 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        awaddr = 5'd16;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd1;
        wstrb = 4'd15;
        wvalid = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 26 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 28 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 28 expected 0, got %0d", bresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 28 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        araddr = 5'd16;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 29 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 30 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 30 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 30 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 5'd0;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd5;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 33 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 33 expected 0, got %0d", bresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 33 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 34 expected 0, got %0d", bvalid);
        end
        repeat (7) @(negedge aclk);
        #1;
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 41 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        #1;
        if (irq !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 42 expected 1, got %0d", irq);
        end
        @(negedge aclk);
        awaddr = 5'd16;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd1;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 45 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 45 expected 0, got %0d", bresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 45 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 46 expected 0, got %0d", bvalid);
        end
        repeat (24) @(negedge aclk);
        araddr = 5'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 71 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 71 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 71 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 5'd16;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 73 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 73 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 73 expected 0, got %0d", rresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 73 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        awaddr = 5'd0;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd8;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 76 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 76 expected 2, got %0d", bresp);
        end
        if (irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq at cycle 76 expected 0, got %0d", irq);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 77 expected 0, got %0d", bvalid);
        end
        $display("SMOKE PASS: axil_timer");
        $finish;
    end

    // Concurrent assertions (SVA)
    bvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");
    rvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> rvalid == 1'd0)
        else $fatal(1, "SVA FAIL: rvalid_idle_after_reset");
    irq_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> irq == 1'd0)
        else $fatal(1, "SVA FAIL: irq_idle_after_reset");

endmodule
