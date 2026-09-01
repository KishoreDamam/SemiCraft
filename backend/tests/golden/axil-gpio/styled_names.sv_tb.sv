// SemiCraft v0.4.0
// Testbench: axil_gpio_tb (config hash: 28458bc0a6db)
// Smoke testbench (stub, compile-checked only) for axil_gpio
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_gpio_tb;
    logic p_aclk;
    logic p_areset_n;
    logic [3:0] p_awaddr;
    logic p_awvalid;
    logic p_awready;
    logic [31:0] p_wdata;
    logic [3:0] p_wstrb;
    logic p_wvalid;
    logic p_wready;
    logic [1:0] p_bresp;
    logic p_bvalid;
    logic p_bready;
    logic [3:0] p_araddr;
    logic p_arvalid;
    logic p_arready;
    logic [31:0] p_rdata;
    logic [1:0] p_rresp;
    logic p_rvalid;
    logic p_rready;
    logic [7:0] p_gpioIn;
    logic [7:0] p_gpioOut;
    logic [7:0] p_gpioOe;

    // Free-running clock
    initial p_aclk = 1'b0;
    always #5 p_aclk = ~p_aclk;

    // Device under test
    axil_gpio dut (
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
        .p_gpioIn   (p_gpioIn),
        .p_gpioOut  (p_gpioOut),
        .p_gpioOe   (p_gpioOe)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 304; watchdog_i++) @(posedge p_aclk);
                $fatal(1, "TIMEOUT: axil_gpio_tb exceeded 304 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        p_awaddr = 4'd0;
        p_awvalid = 1'd0;
        p_wdata = 32'd0;
        p_wstrb = 4'd0;
        p_wvalid = 1'd0;
        p_bready = 1'd0;
        p_araddr = 4'd0;
        p_arvalid = 1'd0;
        p_rready = 1'd0;
        p_gpioIn = 8'd0;
        p_areset_n = 1'd0;
        repeat (2) @(posedge p_aclk);
        #1;
        p_areset_n = 1'd1;
        // Apply directed vectors; sample checks on the falling edge
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 0 expected 0, got %0d", p_bvalid);
        end
        if (p_rvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 0 expected 0, got %0d", p_rvalid);
        end
        if (p_awready !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_awready at cycle 0 expected 1, got %0d", p_awready);
        end
        if (p_gpioOe !== 8'd0) begin
            $fatal(1, "SMOKE FAIL: p_gpioOe at cycle 0 expected 0, got %0d", p_gpioOe);
        end
        if (p_gpioOut !== 8'd0) begin
            $fatal(1, "SMOKE FAIL: p_gpioOut at cycle 0 expected 0, got %0d", p_gpioOut);
        end
        @(negedge p_aclk);
        p_awaddr = 4'd0;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd255;
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
        if (p_gpioOe !== 8'd255) begin
            $fatal(1, "SMOKE FAIL: p_gpioOe at cycle 3 expected 255, got %0d", p_gpioOe);
        end
        @(negedge p_aclk);
        p_awaddr = 4'd4;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd165;
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
        if (p_gpioOut !== 8'd165) begin
            $fatal(1, "SMOKE FAIL: p_gpioOut at cycle 6 expected 165, got %0d", p_gpioOut);
        end
        @(negedge p_aclk);
        p_araddr = 4'd0;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 7 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 8 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd255) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 8 expected 255, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 8 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_gpioIn = 8'd90;
        @(negedge p_aclk);
        p_araddr = 4'd8;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 11 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 11 expected 0, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 11 expected 0, got %0d", p_rresp);
        end
        repeat (3) @(negedge p_aclk);
        p_araddr = 4'd8;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 15 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd90) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 15 expected 90, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 15 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_awaddr = 4'd0;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd256;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 18 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 18 expected 2, got %0d", p_bresp);
        end
        if (p_gpioOe !== 8'd255) begin
            $fatal(1, "SMOKE FAIL: p_gpioOe at cycle 18 expected 255, got %0d", p_gpioOe);
        end
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 19 expected 0, got %0d", p_bvalid);
        end
        $display("SMOKE PASS: axil_gpio");
        $finish;
    end

    // Concurrent assertions (SVA)
    bvalid_idle_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");
    rvalid_idle_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_rvalid == 1'd0)
        else $fatal(1, "SVA FAIL: rvalid_idle_after_reset");
    pins_not_driven_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_gpioOe == 8'd0)
        else $fatal(1, "SVA FAIL: pins_not_driven_after_reset");

endmodule
