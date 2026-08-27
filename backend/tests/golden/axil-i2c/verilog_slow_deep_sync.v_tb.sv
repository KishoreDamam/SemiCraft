// SemiCraft v0.3.0
// Testbench: axil_i2c_tb (config hash: 26587d292b6d)
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
                for (watchdog_i = 0; watchdog_i < 8984; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_i2c_tb exceeded 8984 cycles");
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
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 19 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 19 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 31 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 31 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 43 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 43 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 55 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 55 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 67 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 67 expected 1, got %0d", sda_oe);
        end
        repeat (9) @(negedge aclk);
        scl_in = 1'd0;
        repeat (3) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 79 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 79 expected 1, got %0d", sda_oe);
        end
        repeat (21) @(negedge aclk);
        scl_in = 1'd1;
        repeat (15) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 115 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 115 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 127 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 127 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 139 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 139 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 151 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 151 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 163 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 163 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 175 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 175 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 187 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 187 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 199 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 199 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 211 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 211 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 223 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 223 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 235 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 235 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 247 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 247 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 259 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 259 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 271 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 271 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 283 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 283 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 295 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 295 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 307 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 307 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 319 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 319 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 331 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 331 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 343 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 343 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 355 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 355 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 367 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 367 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 379 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 379 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 391 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 391 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 403 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 403 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 415 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 415 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 427 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 427 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 439 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 439 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 451 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 451 expected 0, got %0d", sda_oe);
        end
        repeat (9) @(negedge aclk);
        sda_in = 1'd0;
        repeat (3) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 463 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 463 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 475 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 475 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 487 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 487 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 499 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 499 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        sda_in = 1'd1;
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 511 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 511 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 523 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 523 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 535 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 535 expected 1, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 547 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 547 expected 0, got %0d", sda_oe);
        end
        repeat (15) @(negedge aclk);
        araddr = 5'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 563 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd2) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 563 expected 2, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 563 expected 0, got %0d", rresp);
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 566 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 566 expected 0, got %0d", bresp);
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
            $fatal(1, "SMOKE FAIL: bvalid at cycle 567 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 569 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 569 expected 0, got %0d", bresp);
        end
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 570 expected 0, got %0d", bvalid);
        end
        repeat (45) @(negedge aclk);
        sda_in = 1'd0;
        repeat (48) @(negedge aclk);
        sda_in = 1'd0;
        repeat (48) @(negedge aclk);
        sda_in = 1'd1;
        repeat (48) @(negedge aclk);
        sda_in = 1'd0;
        repeat (48) @(negedge aclk);
        sda_in = 1'd1;
        repeat (48) @(negedge aclk);
        sda_in = 1'd1;
        repeat (48) @(negedge aclk);
        sda_in = 1'd0;
        repeat (48) @(negedge aclk);
        sda_in = 1'd1;
        repeat (48) @(negedge aclk);
        sda_in = 1'd1;
        repeat (3) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 1002 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 1002 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 1014 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 1014 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 1026 expected 0, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 1026 expected 0, got %0d", sda_oe);
        end
        repeat (12) @(negedge aclk);
        #1;
        if (scl_oe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: scl_oe at cycle 1038 expected 1, got %0d", scl_oe);
        end
        if (sda_oe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: sda_oe at cycle 1038 expected 0, got %0d", sda_oe);
        end
        repeat (63) @(negedge aclk);
        araddr = 5'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 1102 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd10) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 1102 expected 10, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 1102 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 5'd12;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 1104 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd45) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 1104 expected 45, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 1104 expected 0, got %0d", rresp);
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
