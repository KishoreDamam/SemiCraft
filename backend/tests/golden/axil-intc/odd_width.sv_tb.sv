// SemiCraft v0.4.0
// Testbench: axil_intc_tb (config hash: f2ebca9f537b)
// Smoke testbench (stub, compile-checked only) for axil_intc
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_intc_tb;
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
    logic [12:0] irq_in;
    logic irq_out;

    // Free-running clock
    initial aclk = 1'b0;
    always #5 aclk = ~aclk;

    // Device under test
    axil_intc dut (
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
        .irq_in   (irq_in),
        .irq_out  (irq_out)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 608; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_intc_tb exceeded 608 cycles");
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
        irq_in = 13'd0;
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
        if (irq_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq_out at cycle 0 expected 0, got %0d", irq_out);
        end
        @(negedge aclk);
        irq_in = 13'd1;
        repeat (2) @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        irq_in = 13'd0;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 4 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 4 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 4 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 6 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd1) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 6 expected 1, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 6 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 4'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 8 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 8 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 8 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 4'd4;
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 11 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 11 expected 0, got %0d", bresp);
        end
        if (irq_out !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: irq_out at cycle 11 expected 1, got %0d", irq_out);
        end
        @(negedge aclk);
        araddr = 4'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 12 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 13 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd1) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 13 expected 1, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 13 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        irq_in = 13'd2;
        repeat (2) @(negedge aclk);
        irq_in = 13'd0;
        repeat (4) @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 21 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd3) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 21 expected 3, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 21 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 4'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 23 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd1) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 23 expected 1, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 23 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 4'd0;
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 26 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 26 expected 0, got %0d", bresp);
        end
        if (irq_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq_out at cycle 26 expected 0, got %0d", irq_out);
        end
        @(negedge aclk);
        araddr = 4'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 27 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 28 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 28 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 28 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 30 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd2) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 30 expected 2, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 30 expected 0, got %0d", rresp);
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 33 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 33 expected 0, got %0d", bresp);
        end
        if (irq_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq_out at cycle 33 expected 0, got %0d", irq_out);
        end
        @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 34 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 35 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 35 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 35 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 4'd4;
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 38 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 38 expected 0, got %0d", bresp);
        end
        if (irq_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq_out at cycle 38 expected 0, got %0d", irq_out);
        end
        @(negedge aclk);
        irq_in = 13'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 39 expected 0, got %0d", bvalid);
        end
        repeat (4) @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 44 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd1) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 44 expected 1, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 44 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 4'd0;
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 47 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 47 expected 0, got %0d", bresp);
        end
        if (irq_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq_out at cycle 47 expected 0, got %0d", irq_out);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 48 expected 0, got %0d", bvalid);
        end
        repeat (4) @(negedge aclk);
        araddr = 4'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 53 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 53 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 53 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 4'd4;
        awvalid = 1'd1;
        bready = 1'd1;
        irq_in = 13'd0;
        wdata = 32'd8192;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 56 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 56 expected 2, got %0d", bresp);
        end
        if (irq_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: irq_out at cycle 56 expected 0, got %0d", irq_out);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 57 expected 0, got %0d", bvalid);
        end
        $display("SMOKE PASS: axil_intc");
        $finish;
    end

    // Concurrent assertions (SVA)
    bvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");
    rvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> rvalid == 1'd0)
        else $fatal(1, "SVA FAIL: rvalid_idle_after_reset");
    irq_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> irq_out == 1'd0)
        else $fatal(1, "SVA FAIL: irq_idle_after_reset");

endmodule
