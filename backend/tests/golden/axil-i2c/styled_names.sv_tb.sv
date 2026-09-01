// SemiCraft v0.4.0
// Testbench: axil_i2c_tb (config hash: 0023434d01dd)
// Smoke testbench (stub, compile-checked only) for axil_i2c
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_i2c_tb;
    logic p_aclk;
    logic p_areset_n;
    logic [4:0] p_awaddr;
    logic p_awvalid;
    logic p_awready;
    logic [31:0] p_wdata;
    logic [3:0] p_wstrb;
    logic p_wvalid;
    logic p_wready;
    logic [1:0] p_bresp;
    logic p_bvalid;
    logic p_bready;
    logic [4:0] p_araddr;
    logic p_arvalid;
    logic p_arready;
    logic [31:0] p_rdata;
    logic [1:0] p_rresp;
    logic p_rvalid;
    logic p_rready;
    logic p_sclIn;
    logic p_sdaIn;
    logic p_sclOe;
    logic p_sdaOe;

    // Free-running clock
    initial p_aclk = 1'b0;
    always #5 p_aclk = ~p_aclk;

    // Device under test
    axil_i2c dut (
        .p_aclk     (p_aclk),
        .p_areset_n (p_areset_n),
        .p_awaddr   (p_awaddr),
        .p_awvalid  (p_awvalid),
        .p_awready  (p_awready),
        .p_wdata    (p_wdata),
        .p_wstrb    (p_wstrb),
        .p_wvalid   (p_wvalid),
        .p_wready   (p_wready),
        .p_bresp    (p_bresp),
        .p_bvalid   (p_bvalid),
        .p_bready   (p_bready),
        .p_araddr   (p_araddr),
        .p_arvalid  (p_arvalid),
        .p_arready  (p_arready),
        .p_rdata    (p_rdata),
        .p_rresp    (p_rresp),
        .p_rvalid   (p_rvalid),
        .p_rready   (p_rready),
        .p_sclIn    (p_sclIn),
        .p_sdaIn    (p_sdaIn),
        .p_sclOe    (p_sclOe),
        .p_sdaOe    (p_sdaOe)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 1784; watchdog_i++) @(posedge p_aclk);
                $fatal(1, "TIMEOUT: axil_i2c_tb exceeded 1784 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_awaddr = 5'd0;
        p_awvalid = 1'd0;
        p_wdata = 32'd0;
        p_wstrb = 4'd0;
        p_wvalid = 1'd0;
        p_bready = 1'd0;
        p_araddr = 5'd0;
        p_arvalid = 1'd0;
        p_rready = 1'd0;
        p_sclIn = 1'd0;
        p_sdaIn = 1'd0;
        p_areset_n = 1'd0;
        repeat (2) @(posedge p_aclk);
        #1;
        p_areset_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_aclk);
        p_sclIn = 1'd1;
        p_sdaIn = 1'd1;
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 0 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 0 expected 0, got %0d", p_sdaOe);
        end
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 0 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd8;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd75;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 3 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 3 expected 0, got %0d", p_bresp);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd4;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd19;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 4 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 6 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 6 expected 0, got %0d", p_bresp);
        end
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 7 expected 0, got %0d", p_bvalid);
        end
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 7 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 7 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 9 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 9 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 11 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 11 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 13 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 13 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 15 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 15 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        p_sclIn = 1'd0;
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 17 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 17 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 19 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 19 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        p_sclIn = 1'd1;
        repeat (4) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 25 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 25 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 27 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 27 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 29 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 29 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 31 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 31 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 33 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 33 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 35 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 35 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 37 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 37 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 39 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 39 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 41 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 41 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 43 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 43 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 45 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 45 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 47 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 47 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 49 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 49 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 51 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 51 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 53 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 53 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 55 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 55 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 57 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 57 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 59 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 59 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 61 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 61 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 63 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 63 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 65 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 65 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 67 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 67 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 69 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 69 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 71 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 71 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 73 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 73 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 75 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 75 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 77 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 77 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 79 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 79 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        p_sdaIn = 1'd0;
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 81 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 81 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 83 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 83 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 85 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 85 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 87 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 87 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 89 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 89 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        p_sdaIn = 1'd1;
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 91 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 91 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 93 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 93 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 95 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 95 expected 1, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 97 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 97 expected 0, got %0d", p_sdaOe);
        end
        repeat (5) @(negedge p_aclk);
        p_araddr = 5'd0;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 103 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd2) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 103 expected 2, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 103 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd0;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd2;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 106 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 106 expected 0, got %0d", p_bresp);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd4;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd21;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 107 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 109 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 109 expected 0, got %0d", p_bresp);
        end
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 110 expected 0, got %0d", p_bvalid);
        end
        repeat (6) @(negedge p_aclk);
        p_sdaIn = 1'd0;
        repeat (8) @(negedge p_aclk);
        p_sdaIn = 1'd0;
        repeat (8) @(negedge p_aclk);
        p_sdaIn = 1'd1;
        repeat (8) @(negedge p_aclk);
        p_sdaIn = 1'd0;
        repeat (8) @(negedge p_aclk);
        p_sdaIn = 1'd1;
        repeat (8) @(negedge p_aclk);
        p_sdaIn = 1'd1;
        repeat (8) @(negedge p_aclk);
        p_sdaIn = 1'd0;
        repeat (8) @(negedge p_aclk);
        p_sdaIn = 1'd1;
        repeat (8) @(negedge p_aclk);
        p_sdaIn = 1'd1;
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 182 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 182 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 184 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 184 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 186 expected 0, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 186 expected 0, got %0d", p_sdaOe);
        end
        repeat (2) @(negedge p_aclk);
        #1;
        if (p_sclOe !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_sclOe at cycle 188 expected 1, got %0d", p_sclOe);
        end
        if (p_sdaOe !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_sdaOe at cycle 188 expected 0, got %0d", p_sdaOe);
        end
        repeat (13) @(negedge p_aclk);
        p_araddr = 5'd0;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 202 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd10) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 202 expected 10, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 202 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_araddr = 5'd12;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 204 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd45) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 204 expected 45, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 204 expected 0, got %0d", p_rresp);
        end
        $display("SMOKE PASS: axil_i2c");
        $finish;
    end

    // Concurrent assertions (SVA)
    scl_released_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_sclOe == 1'd0)
        else $fatal(1, "SVA FAIL: scl_released_after_reset");
    sda_released_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_sdaOe == 1'd0)
        else $fatal(1, "SVA FAIL: sda_released_after_reset");
    bvalid_idle_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");

endmodule
