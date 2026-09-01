// SemiCraft v0.4.0
// Testbench: axil_regblock_tb (config hash: d9042ecb56c6)
// Smoke testbench (stub, compile-checked only) for axil_regblock
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

`timescale 1ns/1ps

module axil_regblock_tb;
    logic aclk;
    logic areset_n;
    logic [5:0] awaddr;
    logic awvalid;
    logic awready;
    logic [63:0] wdata;
    logic [7:0] wstrb;
    logic wvalid;
    logic wready;
    logic [1:0] bresp;
    logic bvalid;
    logic bready;
    logic [5:0] araddr;
    logic arvalid;
    logic arready;
    logic [63:0] rdata;
    logic [1:0] rresp;
    logic rvalid;
    logic rready;
    logic ctrl0_enable;
    logic [1:0] ctrl0_mode;
    logic [3:0] ctrl0_level;
    logic status0_busy;
    logic [3:0] status0_code;
    logic [3:0] irq0_flags;
    logic [3:0] irq0_flags_set;
    logic cmd0_go;
    logic [2:0] cmd0_code;
    logic [63:0] scratch_value;

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
        .ctrl0_enable   (ctrl0_enable),
        .ctrl0_mode     (ctrl0_mode),
        .ctrl0_level    (ctrl0_level),
        .status0_busy   (status0_busy),
        .status0_code   (status0_code),
        .irq0_flags     (irq0_flags),
        .irq0_flags_set (irq0_flags_set),
        .cmd0_go        (cmd0_go),
        .cmd0_code      (cmd0_code),
        .scratch_value  (scratch_value)
    );

    // Stimulus and self-checking assertions
    initial begin
        // Watchdog: fail loudly if the run hangs
        fork
            begin
                static int watchdog_i;
                for (watchdog_i = 0; watchdog_i < 408; watchdog_i++) @(posedge aclk);
                $fatal(1, "TIMEOUT: axil_regblock_tb exceeded 408 cycles");
            end
        join_none
        // Initialise inputs and assert reset
        awaddr = 6'd0;
        awvalid = 1'd0;
        wdata = 64'd0;
        wstrb = 8'd0;
        wvalid = 1'd0;
        bready = 1'd0;
        araddr = 6'd0;
        arvalid = 1'd0;
        rready = 1'd0;
        status0_busy = 1'd0;
        status0_code = 4'd0;
        irq0_flags_set = 4'd0;
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
        if (ctrl0_enable !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: ctrl0_enable at cycle 0 expected 1, got %0d", ctrl0_enable);
        end
        if (ctrl0_mode !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: ctrl0_mode at cycle 0 expected 0, got %0d", ctrl0_mode);
        end
        if (ctrl0_level !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: ctrl0_level at cycle 0 expected 0, got %0d", ctrl0_level);
        end
        if (irq0_flags !== 4'd0) begin
            $fatal(1, "SMOKE FAIL: irq0_flags at cycle 0 expected 0, got %0d", irq0_flags);
        end
        if (cmd0_go !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: cmd0_go at cycle 0 expected 0, got %0d", cmd0_go);
        end
        if (cmd0_code !== 3'd0) begin
            $fatal(1, "SMOKE FAIL: cmd0_code at cycle 0 expected 0, got %0d", cmd0_code);
        end
        if (scratch_value !== 64'd0) begin
            $fatal(1, "SMOKE FAIL: scratch_value at cycle 0 expected 0, got %0d", scratch_value);
        end
        @(negedge aclk);
        awaddr = 6'd0;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 64'd246;
        wstrb = 8'd255;
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
        if (ctrl0_enable !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: ctrl0_enable at cycle 3 expected 0, got %0d", ctrl0_enable);
        end
        if (ctrl0_mode !== 2'd3) begin
            $fatal(1, "SMOKE FAIL: ctrl0_mode at cycle 3 expected 3, got %0d", ctrl0_mode);
        end
        if (ctrl0_level !== 4'd15) begin
            $fatal(1, "SMOKE FAIL: ctrl0_level at cycle 3 expected 15, got %0d", ctrl0_level);
        end
        @(negedge aclk);
        araddr = 6'd0;
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
        if (rdata !== 64'd246) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 5 expected 246, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 5 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 6'd1;
        arvalid = 1'd1;
        rready = 1'd1;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 7 expected 1, got %0d", rvalid);
        end
        if (rdata !== 64'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 7 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 7 expected 2, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 6'd0;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 64'd8;
        wstrb = 8'd255;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 10 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd2) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 10 expected 2, got %0d", bresp);
        end
        if (ctrl0_enable !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: ctrl0_enable at cycle 10 expected 0, got %0d", ctrl0_enable);
        end
        if (ctrl0_mode !== 2'd3) begin
            $fatal(1, "SMOKE FAIL: ctrl0_mode at cycle 10 expected 3, got %0d", ctrl0_mode);
        end
        if (ctrl0_level !== 4'd15) begin
            $fatal(1, "SMOKE FAIL: ctrl0_level at cycle 10 expected 15, got %0d", ctrl0_level);
        end
        @(negedge aclk);
        irq0_flags_set = 4'd15;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 11 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        irq0_flags_set = 4'd0;
        #1;
        if (irq0_flags !== 4'd15) begin
            $fatal(1, "SMOKE FAIL: irq0_flags at cycle 12 expected 15, got %0d", irq0_flags);
        end
        @(negedge aclk);
        awaddr = 6'd16;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 64'd8;
        wstrb = 8'd255;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 15 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 15 expected 0, got %0d", bresp);
        end
        if (irq0_flags !== 4'd7) begin
            $fatal(1, "SMOKE FAIL: irq0_flags at cycle 15 expected 7, got %0d", irq0_flags);
        end
        @(negedge aclk);
        araddr = 6'd16;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 16 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 17 expected 1, got %0d", rvalid);
        end
        if (rdata !== 64'd7) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 17 expected 7, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 17 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 6'd32;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 64'd11574711341044573863;
        wstrb = 8'd255;
        wvalid = 1'd1;
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
        if (scratch_value !== 64'd11574711341044573863) begin
            $fatal(1, "SMOKE FAIL: scratch_value at cycle 20 expected 11574711341044573863, got %0d", scratch_value);
        end
        @(negedge aclk);
        awaddr = 6'd32;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 64'd6872032732664977752;
        wstrb = 8'd85;
        wvalid = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 21 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 23 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 23 expected 0, got %0d", bresp);
        end
        if (scratch_value !== 64'd11555852212657366616) begin
            $fatal(1, "SMOKE FAIL: scratch_value at cycle 23 expected 11555852212657366616, got %0d", scratch_value);
        end
        @(negedge aclk);
        araddr = 6'd32;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 24 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 25 expected 1, got %0d", rvalid);
        end
        if (rdata !== 64'd11555852212657366616) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 25 expected 11555852212657366616, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 25 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        araddr = 6'd8;
        arvalid = 1'd1;
        rready = 1'd1;
        status0_busy = 1'd1;
        status0_code = 4'd15;
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 27 expected 1, got %0d", rvalid);
        end
        if (rdata !== 64'd241) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 27 expected 241, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 27 expected 0, got %0d", rresp);
        end
        @(negedge aclk);
        awaddr = 6'd24;
        awvalid = 1'd1;
        bready = 1'd1;
        wdata = 64'd15;
        wstrb = 8'd255;
        wvalid = 1'd1;
        @(negedge aclk);
        awvalid = 1'd0;
        wvalid = 1'd0;
        @(negedge aclk);
        #1;
        if (bvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 30 expected 1, got %0d", bvalid);
        end
        if (bresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: bresp at cycle 30 expected 0, got %0d", bresp);
        end
        if (cmd0_go !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: cmd0_go at cycle 30 expected 1, got %0d", cmd0_go);
        end
        if (cmd0_code !== 3'd7) begin
            $fatal(1, "SMOKE FAIL: cmd0_code at cycle 30 expected 7, got %0d", cmd0_code);
        end
        @(negedge aclk);
        araddr = 6'd24;
        arvalid = 1'd1;
        rready = 1'd1;
        #1;
        if (bvalid !== 1'd0) begin
            $fatal(1, "SMOKE FAIL: bvalid at cycle 31 expected 0, got %0d", bvalid);
        end
        @(negedge aclk);
        arvalid = 1'd0;
        #1;
        if (rvalid !== 1'd1) begin
            $fatal(1, "SMOKE FAIL: rvalid at cycle 32 expected 1, got %0d", rvalid);
        end
        if (rdata !== 64'd0) begin
            $fatal(1, "SMOKE FAIL: rdata at cycle 32 expected 0, got %0d", rdata);
        end
        if (rresp !== 2'd0) begin
            $fatal(1, "SMOKE FAIL: rresp at cycle 32 expected 0, got %0d", rresp);
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
