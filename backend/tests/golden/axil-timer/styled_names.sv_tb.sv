// SemiCraft v0.4.0
// Testbench: axil_timer_tb (config hash: 0cd916fa1b61)
// Smoke testbench (stub, compile-checked only) for axil_timer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_timer_tb;
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
    logic p_irq;

    // Free-running clock
    initial p_aclk = 1'b0;
    always #5 p_aclk = ~p_aclk;

    // Device under test
    axil_timer dut (
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
        .p_irq      (p_irq)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 768; watchdog_i++) @(posedge p_aclk);
                $fatal(1, "TIMEOUT: axil_timer_tb exceeded 768 cycles");
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
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 0 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd12;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd1;
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
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 3 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd4;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd3;
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
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 6 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        p_araddr = 5'd8;
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
        if (p_rdata !== 32'd3) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 8 expected 3, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 8 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd0;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd7;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 11 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 11 expected 0, got %0d", p_bresp);
        end
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 11 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 12 expected 0, got %0d", p_bvalid);
        end
        repeat (7) @(negedge p_aclk);
        #1;
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 19 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        #1;
        if (p_irq !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 20 expected 1, got %0d", p_irq);
        end
        @(negedge p_aclk);
        p_araddr = 5'd16;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 22 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd1) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 22 expected 1, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 22 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd0;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd0;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 25 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 25 expected 0, got %0d", p_bresp);
        end
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 25 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd16;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd1;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 26 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 28 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 28 expected 0, got %0d", p_bresp);
        end
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 28 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        p_araddr = 5'd16;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 29 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 30 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 30 expected 0, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 30 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd0;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd5;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 33 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 33 expected 0, got %0d", p_bresp);
        end
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 33 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 34 expected 0, got %0d", p_bvalid);
        end
        repeat (7) @(negedge p_aclk);
        #1;
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 41 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        #1;
        if (p_irq !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 42 expected 1, got %0d", p_irq);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd16;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd1;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 45 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 45 expected 0, got %0d", p_bresp);
        end
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 45 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 46 expected 0, got %0d", p_bvalid);
        end
        repeat (24) @(negedge p_aclk);
        p_araddr = 5'd8;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 71 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 71 expected 0, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 71 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_araddr = 5'd16;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 73 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 73 expected 0, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 73 expected 0, got %0d", p_rresp);
        end
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 73 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd0;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd8;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 76 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 76 expected 2, got %0d", p_bresp);
        end
        if (p_irq !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq at cycle 76 expected 0, got %0d", p_irq);
        end
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 77 expected 0, got %0d", p_bvalid);
        end
        $display("SMOKE PASS: axil_timer");
        $finish;
    end

    // Concurrent assertions (SVA)
    bvalid_idle_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");
    rvalid_idle_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_rvalid == 1'd0)
        else $fatal(1, "SVA FAIL: rvalid_idle_after_reset");
    irq_idle_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_irq == 1'd0)
        else $fatal(1, "SVA FAIL: irq_idle_after_reset");

endmodule
