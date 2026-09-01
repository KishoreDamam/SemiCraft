// SemiCraft v0.4.0
// Snippet: axil_timer (config hash: c7d6b58fadfd)
// AXI4-Lite timer, 32-bit counter, 1-bit prescaler
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_timer (
    input  logic        aclk,       // AXI clock; everything is synchronous to it
    input  logic        areset_n,   // AXI reset, active-low (spec: ARESETn)
    input  logic [4:0]  awaddr,     // Write address (byte address)
    input  logic        awvalid,    // Write address valid
    output logic        awready,    // Write address ready
    input  logic [31:0] wdata,      // Write data
    input  logic [3:0]  wstrb,      // Write byte strobes, one bit per byte
    input  logic        wvalid,     // Write data valid
    output logic        wready,     // Write data ready
    output logic [1:0]  bresp,      // Write response: OKAY, or SLVERR if unmapped
    output logic        bvalid,     // Write response valid
    input  logic        bready,     // Write response ready
    input  logic [4:0]  araddr,     // Read address (byte address)
    input  logic        arvalid,    // Read address valid
    output logic        arready,    // Read address ready
    output logic [31:0] rdata,      // Read data
    output logic [1:0]  rresp,      // Read response: OKAY, or SLVERR if unmapped
    output logic        rvalid,     // Read data valid
    input  logic        rready,     // Read data ready
    output logic        irq         // Interrupt request, level-sensitive
);

    logic ctrl_enable;  // CTRL.enable (RW)
    logic ctrl_auto_reload;  // CTRL.auto_reload (RW)
    logic ctrl_irq_enable;  // CTRL.irq_enable (RW)
    logic [31:0] reload_value;  // RELOAD.value (RW)
    logic [31:0] count_value;  // COUNT.value (RO) — sampled on read
    logic prescale_value;  // PRESCALE.value (RW)
    logic status_expired;  // STATUS.expired (W1C) — current value
    logic status_expired_set;  // STATUS.expired (W1C) — set request; a set beats a same-cycle clear
    logic aw_hs;  // Write address captured, awaiting the data beat
    logic w_hs;  // Write data captured, awaiting the address beat
    logic [4:0] awaddr_q;  // Captured write address
    logic [31:0] wdata_q;  // Captured write data
    logic [3:0] wstrb_q;  // Captured write byte strobes
    logic [31:0] wmask;  // Captured strobes expanded to a bit mask

    assign awready = (!aw_hs) && (!bvalid);

    assign wready = (!w_hs) && (!bvalid);

    assign arready = !rvalid;

    assign wmask = {{8{wstrb_q[3]}}, {8{wstrb_q[2]}}, {8{wstrb_q[1]}}, {8{wstrb_q[0]}}};

    logic wr_exec;  // Both write channels captured and no response pending

    assign wr_exec = (aw_hs && w_hs) && (!bvalid);

    logic wr_addr_ctrl;  // Write address selects CTRL

    assign wr_addr_ctrl = wr_exec && (awaddr_q == 5'h0);

    logic wr_addr_reload;  // Write address selects RELOAD

    assign wr_addr_reload = wr_exec && (awaddr_q == 5'h4);

    logic wr_addr_count;  // Write address selects COUNT

    assign wr_addr_count = wr_exec && (awaddr_q == 5'h8);

    logic wr_addr_prescale;  // Write address selects PRESCALE

    assign wr_addr_prescale = wr_exec && (awaddr_q == 5'hC);

    logic wr_addr_status;  // Write address selects STATUS

    assign wr_addr_status = wr_exec && (awaddr_q == 5'h10);

    logic wr_hit;  // The write address matched a register

    assign wr_hit = (((wr_addr_ctrl || wr_addr_reload) || wr_addr_count) || wr_addr_prescale) || wr_addr_status;

    logic [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = ((((wr_addr_ctrl ? 32'hFFFFFFF8 : 32'b0) | (wr_addr_reload ? 32'h0 : 32'b0)) | (wr_addr_count ? 32'hFFFFFFFF : 32'b0)) | (wr_addr_prescale ? 32'hFFFFFFFE : 32'b0)) | (wr_addr_status ? 32'hFFFFFFFE : 32'b0);

    logic wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    logic wr_sel_ctrl;  // Write updates CTRL

    assign wr_sel_ctrl = wr_addr_ctrl && (!wr_reserved);

    logic wr_sel_reload;  // Write updates RELOAD

    assign wr_sel_reload = wr_addr_reload && (!wr_reserved);

    logic wr_sel_prescale;  // Write updates PRESCALE

    assign wr_sel_prescale = wr_addr_prescale && (!wr_reserved);

    logic wr_sel_status;  // Write updates STATUS

    assign wr_sel_status = wr_addr_status && (!wr_reserved);

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            aw_hs <= 1'b0;
            w_hs <= 1'b0;
            bvalid <= 1'b0;
            bresp <= 2'b0;
            rvalid <= 1'b0;
            rresp <= 2'b0;
            rdata <= 32'b0;
            ctrl_enable <= 1'd0;
            ctrl_auto_reload <= 1'd0;
            ctrl_irq_enable <= 1'd0;
            reload_value <= 32'd0;
            prescale_value <= 1'd0;
            status_expired <= 1'd0;
        end else begin
            if (awvalid && awready) begin
                aw_hs <= 1'b1;
                awaddr_q <= awaddr;
            end
            if (wvalid && wready) begin
                w_hs <= 1'b1;
                wdata_q <= wdata;
                wstrb_q <= wstrb;
            end
            if (wr_exec) begin
                aw_hs <= 1'b0;
                w_hs <= 1'b0;
                bvalid <= 1'b1;
                bresp <= (wr_hit && (!wr_reserved)) ? 2'b0 : 2'b10;
            end
            if (bvalid && bready) begin
                bvalid <= 1'b0;
            end
            if (wr_sel_ctrl) begin
                ctrl_enable <= (wdata_q[0] & wmask[0]) | (ctrl_enable & (~wmask[0]));
                ctrl_auto_reload <= (wdata_q[1] & wmask[1]) | (ctrl_auto_reload & (~wmask[1]));
                ctrl_irq_enable <= (wdata_q[2] & wmask[2]) | (ctrl_irq_enable & (~wmask[2]));
            end
            if (wr_sel_reload) begin
                reload_value <= (wdata_q[31:0] & wmask[31:0]) | (reload_value & (~wmask[31:0]));
            end
            if (wr_sel_prescale) begin
                prescale_value <= (wdata_q[0] & wmask[0]) | (prescale_value & (~wmask[0]));
            end
            if (wr_sel_status) begin
                status_expired <= (status_expired & (~(wdata_q[0] & wmask[0]))) | status_expired_set;
            end else begin
                status_expired <= status_expired | status_expired_set;
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    5'h0: begin
                        rdata <= {29'b0, ctrl_irq_enable, ctrl_auto_reload, ctrl_enable};
                        rresp <= 2'b0;
                    end
                    5'h4: begin
                        rdata <= reload_value;
                        rresp <= 2'b0;
                    end
                    5'h8: begin
                        rdata <= count_value;
                        rresp <= 2'b0;
                    end
                    5'hC: begin
                        rdata <= {31'b0, prescale_value};
                        rresp <= 2'b0;
                    end
                    5'h10: begin
                        rdata <= {31'b0, status_expired};
                        rresp <= 2'b0;
                    end
                    default: begin
                        rdata <= 32'b0;
                        rresp <= 2'b10;
                    end
                endcase
            end
            if (rvalid && rready) begin
                rvalid <= 1'b0;
            end
        end
    end

    logic [0:0] pre_cnt;  // Prescaler counter
    logic running;  // Counter is armed; cleared by a one-shot expiry

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            pre_cnt <= 1'b0;
            count_value <= 32'b0;
            running <= 1'b1;
            status_expired_set <= 1'b0;
        end else begin
            status_expired_set <= 1'b0;
            if (!ctrl_enable) begin
                pre_cnt <= 1'b0;
                count_value <= reload_value;
                running <= 1'b1;
            end else begin
                if (running) begin
                    if (pre_cnt == prescale_value) begin
                        pre_cnt <= 1'b0;
                        if (count_value == 32'b0) begin
                            status_expired_set <= 1'b1;
                            if (ctrl_auto_reload) begin
                                count_value <= reload_value;
                            end else begin
                                running <= 1'b0;
                            end
                        end else begin
                            count_value <= count_value - 32'b1;
                        end
                    end else begin
                        pre_cnt <= pre_cnt + 1'b1;
                    end
                end
            end
        end
    end

    assign irq = status_expired && ctrl_irq_enable;

endmodule
