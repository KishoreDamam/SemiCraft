// SemiCraft v0.4.0
// Testbench: axil_gpio_tb (config hash: 0d3b07e1a0df)
// Smoke testbench (stub, compile-checked only) for axil_gpio
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_gpio_tb;
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
    logic gpio_in;
    logic gpio_out;
    logic gpio_oe;

    // Free-running clock
    initial aclk = 1'b0;
    always #5 aclk = ~aclk;

    // Device under test
    axil_gpio dut (
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
        .gpio_in  (gpio_in),
        .gpio_out (gpio_out),
        .gpio_oe  (gpio_oe)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 304; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_gpio_tb exceeded 304 cycles");
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
        gpio_in = 1'd0;
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
        if (awready !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: awready at cycle 0 expected 1, got %0d", awready);
        end
        if (gpio_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: gpio_oe at cycle 0 expected 0, got %0d", gpio_oe);
        end
        if (gpio_out !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: gpio_out at cycle 0 expected 0, got %0d", gpio_out);
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 3 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 3 expected 0, got %0d", bresp);
        end
        if (gpio_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: gpio_oe at cycle 3 expected 1, got %0d", gpio_oe);
        end
        @(negedge aclk);
        awaddr = 4'd4;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd1;
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
        if (gpio_out !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: gpio_out at cycle 6 expected 1, got %0d", gpio_out);
        end
        @(negedge aclk);
        araddr = 4'd0;
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
        if (rdata !== 32'd1) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 8 expected 1, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 8 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        gpio_in = 1'd0;
        @(negedge aclk);
        araddr = 4'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 11 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 11 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 11 expected 0, got %0d", rresp);
        end
        repeat (3) @(negedge aclk);
        araddr = 4'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 15 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 15 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 15 expected 0, got %0d", rresp);
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 18 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 18 expected 2, got %0d", bresp);
        end
        if (gpio_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: gpio_oe at cycle 18 expected 1, got %0d", gpio_oe);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 19 expected 0, got %0d", bvalid);
        end
        $display("SMOKE PASS: axil_gpio");
        $finish;
    end

    // Concurrent assertions (SVA)
    bvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");
    rvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> rvalid == 1'd0)
        else $fatal(1, "SVA FAIL: rvalid_idle_after_reset");
    pins_not_driven_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> gpio_oe == 1'd0)
        else $fatal(1, "SVA FAIL: pins_not_driven_after_reset");

endmodule
