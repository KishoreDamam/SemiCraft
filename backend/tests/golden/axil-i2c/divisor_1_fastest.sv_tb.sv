// SemiCraft v0.3.0
// Testbench: axil_i2c_tb (config hash: 8fe3b2c829db)
// Smoke testbench (stub, compile-checked only) for axil_i2c
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_i2c_tb;
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
    logic scl_in;
    logic sda_in;
    logic scl_oe;
    logic sda_oe;

    // Free-running clock
    initial aclk = 1'b0;
    always #5 aclk = ~aclk;

    // Device under test
    axil_i2c dut (
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
        .scl_in   (scl_in),
        .sda_in   (sda_in),
        .scl_oe   (scl_oe),
        .sda_oe   (sda_oe)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 1080; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_i2c_tb exceeded 1080 cycles");
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
        scl_in = 1'd0;
        sda_in = 1'd0;
        areset_n = 1'd0;
        repeat (2) @(posedge aclk);
        #1;
        areset_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge aclk);
        scl_in = 1'd1;
        sda_in = 1'd1;
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 0 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 0 expected 0, got %0d", sda_oe);
        end
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 0 expected 0, got %0d", bvalid);
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 3 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 3 expected 0, got %0d", bresp);
        end
        @(negedge aclk);
        awaddr = 5'd4;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd19;
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
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 7 expected 0, got %0d", bvalid);
        end
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 7 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 7 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 8 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 8 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 9 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 9 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 10 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 10 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        scl_in = 1'd0;
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 11 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 11 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 12 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 12 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 13 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 13 expected 1, got %0d", sda_oe);
        end
        repeat (2) @(negedge aclk);
        scl_in = 1'd1;
        repeat (3) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 18 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 18 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 19 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 19 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 20 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 20 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 21 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 21 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 22 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 22 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 23 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 23 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 24 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 24 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 25 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 25 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 26 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 26 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 27 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 27 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 28 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 28 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 29 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 29 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 30 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 30 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 31 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 31 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 32 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 32 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 33 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 33 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 34 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 34 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 35 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 35 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 36 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 36 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 37 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 37 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 38 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 38 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 39 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 39 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 40 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 40 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 41 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 41 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 42 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 42 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 43 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 43 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 44 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 44 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        sda_in = 1'd0;
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 45 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 45 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 46 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 46 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 47 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 47 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 48 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 48 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 49 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 49 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 50 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 50 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        sda_in = 1'd1;
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 51 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 51 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 52 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 52 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 53 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 53 expected 1, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 54 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 54 expected 0, got %0d", sda_oe);
        end
        repeat (4) @(negedge aclk);
        araddr = 5'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 59 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd2) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 59 expected 2, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 59 expected 0, got %0d", rresp);
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 62 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 62 expected 0, got %0d", bresp);
        end
        @(negedge aclk);
        awaddr = 5'd4;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd21;
        wstrb = 4'd15;
        wvalid = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 63 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 65 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 65 expected 0, got %0d", bresp);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 66 expected 0, got %0d", bvalid);
        end
        repeat (2) @(negedge aclk);
        sda_in = 1'd0;
        repeat (4) @(negedge aclk);
        sda_in = 1'd0;
        repeat (4) @(negedge aclk);
        sda_in = 1'd1;
        repeat (4) @(negedge aclk);
        sda_in = 1'd0;
        repeat (4) @(negedge aclk);
        sda_in = 1'd1;
        repeat (4) @(negedge aclk);
        sda_in = 1'd1;
        repeat (4) @(negedge aclk);
        sda_in = 1'd0;
        repeat (4) @(negedge aclk);
        sda_in = 1'd1;
        repeat (4) @(negedge aclk);
        sda_in = 1'd1;
        repeat (2) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 102 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 102 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 103 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 103 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 104 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 104 expected 0, got %0d", sda_oe);
        end
        @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 105 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 105 expected 0, got %0d", sda_oe);
        end
        repeat (8) @(negedge aclk);
        araddr = 5'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 114 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd10) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 114 expected 10, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 114 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 5'd12;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 116 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd45) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 116 expected 45, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 116 expected 0, got %0d", rresp);
        end
        $display("SMOKE PASS: axil_i2c");
        $finish;
    end

    // Concurrent assertions (SVA)
    scl_released_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> scl_oe == 1'd0)
        else $fatal(1, "SVA FAIL: scl_released_after_reset");
    sda_released_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> sda_oe == 1'd0)
        else $fatal(1, "SVA FAIL: sda_released_after_reset");
    bvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");

endmodule
