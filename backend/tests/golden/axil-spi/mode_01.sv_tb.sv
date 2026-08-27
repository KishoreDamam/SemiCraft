// SemiCraft v0.3.0
// Testbench: axil_spi_tb (config hash: ec21710137da)
// Smoke testbench (stub, compile-checked only) for axil_spi
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_spi_tb;
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
    logic miso;
    logic sclk;
    logic mosi;
    logic cs_n;

    // Free-running clock
    initial aclk = 1'b0;
    always #5 aclk = ~aclk;

    // Device under test
    axil_spi dut (
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
        .miso     (miso),
        .sclk     (sclk),
        .mosi     (mosi),
        .cs_n     (cs_n)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 568; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_spi_tb exceeded 568 cycles");
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
        miso = 1'd0;
        areset_n = 1'd0;
        repeat (2) @(posedge aclk);
        #1;
        areset_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge aclk);
        awaddr = 5'd4;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd1;
        wstrb = 4'd15;
        wvalid = 1'd1;
        #1;
        if (sclk !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sclk at cycle 0 expected 0, got %0d", sclk);
        end
        if (cs_n !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: cs_n at cycle 0 expected 1, got %0d", cs_n);
        end
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 0 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 2 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 2 expected 0, got %0d", bresp);
        end
        if (cs_n !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: cs_n at cycle 2 expected 0, got %0d", cs_n);
        end
        @(negedge aclk);
        miso = 1'd0;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 3 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        awaddr = 5'd8;
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 6 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 6 expected 0, got %0d", bresp);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 7 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        miso = 1'd0;
        @(negedge aclk);
        #1;
        if (sclk !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sclk at cycle 9 expected 1, got %0d", sclk);
        end
        @(negedge aclk);
        #1;
        if (mosi !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: mosi at cycle 10 expected 0, got %0d", mosi);
        end
        @(negedge aclk);
        #1;
        if (sclk !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sclk at cycle 11 expected 0, got %0d", sclk);
        end
        @(negedge aclk);
        miso = 1'd0;
        repeat (2) @(negedge aclk);
        #1;
        if (mosi !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: mosi at cycle 14 expected 1, got %0d", mosi);
        end
        repeat (2) @(negedge aclk);
        miso = 1'd1;
        repeat (2) @(negedge aclk);
        #1;
        if (mosi !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: mosi at cycle 18 expected 0, got %0d", mosi);
        end
        repeat (2) @(negedge aclk);
        miso = 1'd0;
        repeat (2) @(negedge aclk);
        #1;
        if (mosi !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: mosi at cycle 22 expected 0, got %0d", mosi);
        end
        repeat (2) @(negedge aclk);
        miso = 1'd1;
        repeat (2) @(negedge aclk);
        #1;
        if (mosi !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: mosi at cycle 26 expected 1, got %0d", mosi);
        end
        repeat (2) @(negedge aclk);
        miso = 1'd1;
        repeat (2) @(negedge aclk);
        #1;
        if (mosi !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: mosi at cycle 30 expected 0, got %0d", mosi);
        end
        repeat (2) @(negedge aclk);
        miso = 1'd0;
        repeat (2) @(negedge aclk);
        #1;
        if (mosi !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: mosi at cycle 34 expected 1, got %0d", mosi);
        end
        repeat (2) @(negedge aclk);
        miso = 1'd1;
        repeat (2) @(negedge aclk);
        #1;
        if (mosi !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: mosi at cycle 38 expected 1, got %0d", mosi);
        end
        @(negedge aclk);
        #1;
        if (sclk !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sclk at cycle 39 expected 0, got %0d", sclk);
        end
        @(negedge aclk);
        araddr = 5'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 41 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd2) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 41 expected 2, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 41 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 5'd12;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 43 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd45) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 43 expected 45, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 43 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 5'd0;
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 46 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 46 expected 0, got %0d", bresp);
        end
        @(negedge aclk);
        araddr = 5'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 47 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 48 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 48 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 48 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 5'd4;
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 51 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 51 expected 0, got %0d", bresp);
        end
        if (cs_n !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: cs_n at cycle 51 expected 1, got %0d", cs_n);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 52 expected 0, got %0d", bvalid);
        end
        $display("SMOKE PASS: axil_spi");
        $finish;
    end

    // Concurrent assertions (SVA)
    cs_released_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> cs_n == 1'd1)
        else $fatal(1, "SVA FAIL: cs_released_after_reset");
    sclk_idles_at_cpol_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> sclk == 1'd0)
        else $fatal(1, "SVA FAIL: sclk_idles_at_cpol_after_reset");
    bvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");

endmodule
