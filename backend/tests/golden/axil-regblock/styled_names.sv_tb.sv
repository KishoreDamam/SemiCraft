// SemiCraft v0.4.0
// Testbench: axil_regblock_tb (config hash: 9e0a82cbd583)
// Smoke testbench (stub, compile-checked only) for axil_regblock
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_regblock_tb;
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
    logic p_ctrl0Enable;
    logic [1:0] p_ctrl0Mode;
    logic [3:0] p_ctrl0Level;
    logic p_status0Busy;
    logic [3:0] p_status0Code;
    logic [3:0] p_irq0Flags;
    logic [3:0] p_irq0FlagsSet;
    logic p_cmd0Go;
    logic [2:0] p_cmd0Code;
    logic [31:0] p_scratchValue;

    // Free-running clock
    initial p_aclk = 1'b0;
    always #5 p_aclk = ~p_aclk;

    // Device under test
    axil_regblock dut (
        .p_aclk         (p_aclk),
        .p_areset_n     (p_areset_n),
        .p_awaddr       (p_awaddr),
        .p_awvalid      (p_awvalid),
        .p_awready      (p_awready),
        .p_wdata        (p_wdata),
        .p_wstrb        (p_wstrb),
        .p_wvalid       (p_wvalid),
        .p_wready       (p_wready),
        .p_bresp        (p_bresp),
        .p_bvalid       (p_bvalid),
        .p_bready       (p_bready),
        .p_araddr       (p_araddr),
        .p_arvalid      (p_arvalid),
        .p_arready      (p_arready),
        .p_rdata        (p_rdata),
        .p_rresp        (p_rresp),
        .p_rvalid       (p_rvalid),
        .p_rready       (p_rready),
        .p_ctrl0Enable  (p_ctrl0Enable),
        .p_ctrl0Mode    (p_ctrl0Mode),
        .p_ctrl0Level   (p_ctrl0Level),
        .p_status0Busy  (p_status0Busy),
        .p_status0Code  (p_status0Code),
        .p_irq0Flags    (p_irq0Flags),
        .p_irq0FlagsSet (p_irq0FlagsSet),
        .p_cmd0Go       (p_cmd0Go),
        .p_cmd0Code     (p_cmd0Code),
        .p_scratchValue (p_scratchValue)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 408; watchdog_i++) @(posedge p_aclk);
                $fatal(1, "TIMEOUT: axil_regblock_tb exceeded 408 cycles");
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
        p_status0Busy = 1'd0;
        p_status0Code = 4'd0;
        p_irq0FlagsSet = 4'd0;
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
        if (p_wready !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_wready at cycle 0 expected 1, got %0d", p_wready);
        end
        if (p_arready !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_arready at cycle 0 expected 1, got %0d", p_arready);
        end
        if (p_ctrl0Enable !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Enable at cycle 0 expected 1, got %0d", p_ctrl0Enable);
        end
        if (p_ctrl0Mode !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Mode at cycle 0 expected 0, got %0d", p_ctrl0Mode);
        end
        if (p_ctrl0Level !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Level at cycle 0 expected 0, got %0d", p_ctrl0Level);
        end
        if (p_irq0Flags !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: p_irq0Flags at cycle 0 expected 0, got %0d", p_irq0Flags);
        end
        if (p_cmd0Go !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_cmd0Go at cycle 0 expected 0, got %0d", p_cmd0Go);
        end
        if (p_cmd0Code !== 3'd0) begin
            $fatal(1, "SMOKE FAIL: p_cmd0Code at cycle 0 expected 0, got %0d", p_cmd0Code);
        end
        if (p_scratchValue !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: p_scratchValue at cycle 0 expected 0, got %0d", p_scratchValue);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd0;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd246;
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
        if (p_ctrl0Enable !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Enable at cycle 3 expected 0, got %0d", p_ctrl0Enable);
        end
        if (p_ctrl0Mode !== 2'd3) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Mode at cycle 3 expected 3, got %0d", p_ctrl0Mode);
        end
        if (p_ctrl0Level !== 4'd15) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Level at cycle 3 expected 15, got %0d", p_ctrl0Level);
        end
        @(negedge p_aclk);
        p_araddr = 5'd0;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 4 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 5 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd246) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 5 expected 246, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 5 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_araddr = 5'd1;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 7 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 7 expected 0, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 7 expected 2, got %0d", p_rresp);
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
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 10 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 10 expected 2, got %0d", p_bresp);
        end
        if (p_ctrl0Enable !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Enable at cycle 10 expected 0, got %0d", p_ctrl0Enable);
        end
        if (p_ctrl0Mode !== 2'd3) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Mode at cycle 10 expected 3, got %0d", p_ctrl0Mode);
        end
        if (p_ctrl0Level !== 4'd15) begin
            $fatal(1, "SMOKE FAIL: p_ctrl0Level at cycle 10 expected 15, got %0d", p_ctrl0Level);
        end
        @(negedge p_aclk);
        p_irq0FlagsSet = 4'd15;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 11 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_irq0FlagsSet = 4'd0;
        #1;
        if (p_irq0Flags !== 4'd15) begin
            $fatal(1, "SMOKE FAIL: p_irq0Flags at cycle 12 expected 15, got %0d", p_irq0Flags);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd8;
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
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 15 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 15 expected 0, got %0d", p_bresp);
        end
        if (p_irq0Flags !== 4'd7) begin
            $fatal(1, "SMOKE FAIL: p_irq0Flags at cycle 15 expected 7, got %0d", p_irq0Flags);
        end
        @(negedge p_aclk);
        p_araddr = 5'd8;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 16 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 17 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd7) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 17 expected 7, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 17 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd16;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd2694947491;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 20 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 20 expected 0, got %0d", p_bresp);
        end
        if (p_scratchValue !== 32'd2694947491) begin
            $fatal(1, "SMOKE FAIL: p_scratchValue at cycle 20 expected 2694947491, got %0d", p_scratchValue);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd16;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd1600019804;
        p_wstrb = 4'd5;
        p_wvalid = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 21 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 23 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 23 expected 0, got %0d", p_bresp);
        end
        if (p_scratchValue !== 32'd2690556508) begin
            $fatal(1, "SMOKE FAIL: p_scratchValue at cycle 23 expected 2690556508, got %0d", p_scratchValue);
        end
        @(negedge p_aclk);
        p_araddr = 5'd16;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 24 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 25 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd2690556508) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 25 expected 2690556508, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 25 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_araddr = 5'd4;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        p_status0Busy = 1'd1;
        p_status0Code = 4'd15;
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 27 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd241) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 27 expected 241, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 27 expected 0, got %0d", p_rresp);
        end
        @(negedge p_aclk);
        p_awaddr = 5'd12;
        p_awvalid = 1'd1;
        p_bready = 1'd1;
        p_wdata = 32'd15;
        p_wstrb = 4'd15;
        p_wvalid = 1'd1;
        @(negedge p_aclk);
        p_awvalid = 1'd0;
        p_wvalid = 1'd0;
        @(negedge p_aclk);
        #1;
        if (p_bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 30 expected 1, got %0d", p_bvalid);
        end
        if (p_bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_bresp at cycle 30 expected 0, got %0d", p_bresp);
        end
        if (p_cmd0Go !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_cmd0Go at cycle 30 expected 1, got %0d", p_cmd0Go);
        end
        if (p_cmd0Code !== 3'd7) begin
            $fatal(1, "SMOKE FAIL: p_cmd0Code at cycle 30 expected 7, got %0d", p_cmd0Code);
        end
        @(negedge p_aclk);
        p_araddr = 5'd12;
        p_arvalid = 1'd1;
        p_rready = 1'd1;
        #1;
        if (p_bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: p_bvalid at cycle 31 expected 0, got %0d", p_bvalid);
        end
        @(negedge p_aclk);
        p_arvalid = 1'd0;
        #1;
        if (p_rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: p_rvalid at cycle 32 expected 1, got %0d", p_rvalid);
        end
        if (p_rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: p_rdata at cycle 32 expected 0, got %0d", p_rdata);
        end
        if (p_rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: p_rresp at cycle 32 expected 0, got %0d", p_rresp);
        end
        $display("SMOKE PASS: axil_regblock");
        $finish;
    end

    // Concurrent assertions (SVA)
    bvalid_idle_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");
    rvalid_idle_after_reset: assert property (@(posedge p_aclk) $rose(p_areset_n) |-> p_rvalid == 1'd0)
        else $fatal(1, "SVA FAIL: rvalid_idle_after_reset");

endmodule
