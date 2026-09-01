// SemiCraft v0.4.0
// Testbench: axil_regblock_tb (config hash: 763ad261e462)
// Smoke testbench (stub, compile-checked only) for axil_regblock
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_regblock_tb;
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
    logic [31:0] ctrl0_value;
    logic [31:0] status0_value;
    logic [31:0] irq0_value;
    logic [31:0] irq0_value_set;
    logic [31:0] cmd0_value;
    logic [31:0] scratch_value;

    // Free-running clock
    initial aclk = 1'b0;
    always #5 aclk = ~aclk;

    // Device under test
    axil_regblock dut (
        .aclk           (aclk),
        .areset_n       (areset_n),
        .awaddr         (awaddr),
        .awvalid        (awvalid),
        .awready        (awready),
        .wdata          (wdata),
        .wstrb          (wstrb),
        .wvalid         (wvalid),
        .wready         (wready),
        .bresp          (bresp),
        .bvalid         (bvalid),
        .bready         (bready),
        .araddr         (araddr),
        .arvalid        (arvalid),
        .arready        (arready),
        .rdata          (rdata),
        .rresp          (rresp),
        .rvalid         (rvalid),
        .rready         (rready),
        .ctrl0_value    (ctrl0_value),
        .status0_value  (status0_value),
        .irq0_value     (irq0_value),
        .irq0_value_set (irq0_value_set),
        .cmd0_value     (cmd0_value),
        .scratch_value  (scratch_value)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 384; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_regblock_tb exceeded 384 cycles");
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
        status0_value = 32'd0;
        irq0_value_set = 32'd0;
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
        if (wready !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: wready at cycle 0 expected 1, got %0d", wready);
        end
        if (arready !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: arready at cycle 0 expected 1, got %0d", arready);
        end
        if (ctrl0_value !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: ctrl0_value at cycle 0 expected 0, got %0d", ctrl0_value);
        end
        if (irq0_value !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: irq0_value at cycle 0 expected 0, got %0d", irq0_value);
        end
        if (cmd0_value !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: cmd0_value at cycle 0 expected 0, got %0d", cmd0_value);
        end
        if (scratch_value !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: scratch_value at cycle 0 expected 0, got %0d", scratch_value);
        end
        @(negedge aclk);
        awaddr = 5'd0;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd4294967295;
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
        if (ctrl0_value !== 32'd4294967295) begin
            $fatal(1, "SMOKE FAIL: ctrl0_value at cycle 3 expected 4294967295, got %0d", ctrl0_value);
        end
        @(negedge aclk);
        araddr = 5'd0;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 4 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 5 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd4294967295) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 5 expected 4294967295, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 5 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 5'd1;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 7 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 7 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 7 expected 2, got %0d", rresp);
        end
        @(negedge aclk);
        irq0_value_set = 32'd4294967295;
        @(negedge aclk);
        irq0_value_set = 32'd0;
        #1;
        if (irq0_value !== 32'd4294967295) begin
            $fatal(1, "SMOKE FAIL: irq0_value at cycle 9 expected 4294967295, got %0d", irq0_value);
        end
        @(negedge aclk);
        awaddr = 5'd8;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd2147483648;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 12 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 12 expected 0, got %0d", bresp);
        end
        if (irq0_value !== 32'd2147483647) begin
            $fatal(1, "SMOKE FAIL: irq0_value at cycle 12 expected 2147483647, got %0d", irq0_value);
        end
        @(negedge aclk);
        araddr = 5'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 13 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 14 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd2147483647) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 14 expected 2147483647, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 14 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 5'd16;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd2694947491;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 17 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 17 expected 0, got %0d", bresp);
        end
        if (scratch_value !== 32'd2694947491) begin
            $fatal(1, "SMOKE FAIL: scratch_value at cycle 17 expected 2694947491, got %0d", scratch_value);
        end
        @(negedge aclk);
        awaddr = 5'd16;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd1600019804;
        wstrb = 4'd5;
        wvalid = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 18 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 20 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 20 expected 0, got %0d", bresp);
        end
        if (scratch_value !== 32'd2690556508) begin
            $fatal(1, "SMOKE FAIL: scratch_value at cycle 20 expected 2690556508, got %0d", scratch_value);
        end
        @(negedge aclk);
        araddr = 5'd16;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 21 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 22 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd2690556508) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 22 expected 2690556508, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 22 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 5'd4;
        arvalid = 1'd1;
        rready = 1'd1;
        status0_value = 32'd4294967295;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 24 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd4294967295) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 24 expected 4294967295, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 24 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 5'd12;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 32'd4294967295;
        wstrb = 4'd15;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 27 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 27 expected 0, got %0d", bresp);
        end
        if (cmd0_value !== 32'd4294967295) begin
            $fatal(1, "SMOKE FAIL: cmd0_value at cycle 27 expected 4294967295, got %0d", cmd0_value);
        end
        @(negedge aclk);
        araddr = 5'd12;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 28 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 29 expected 1, got %0d", rvalid);
        end
        if (rdata !== 32'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 29 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 29 expected 0, got %0d", rresp);
        end
        $display("SMOKE PASS: axil_regblock");
        $finish;
    end

    // Concurrent assertions (SVA)
    bvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> bvalid == 1'd0)
        else $fatal(1, "SVA FAIL: bvalid_idle_after_reset");
    rvalid_idle_after_reset: assert property (@(posedge aclk) $rose(areset_n) |-> rvalid == 1'd0)
        else $fatal(1, "SVA FAIL: rvalid_idle_after_reset");

endmodule
