// SemiCraft v0.3.0
// Snippet: axil_intc (config hash: e7377999e02a)
// AXI4-Lite interrupt controller, 1 source(s), edge-triggered
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_intc (
    input  logic        aclk,       // AXI clock; everything is synchronous to it
    input  logic        areset_n,   // AXI reset, active-low (spec: ARESETn)
    input  logic [3:0]  awaddr,     // Write address (byte address)
    input  logic        awvalid,    // Write address valid
    output logic        awready,    // Write address ready
    input  logic [31:0] wdata,      // Write data
    input  logic [3:0]  wstrb,      // Write byte strobes, one bit per byte
    input  logic        wvalid,     // Write data valid
    output logic        wready,     // Write data ready
    output logic [1:0]  bresp,      // Write response: OKAY, or SLVERR if unmapped
    output logic        bvalid,     // Write response valid
    input  logic        bready,     // Write response ready
    input  logic [3:0]  araddr,     // Read address (byte address)
    input  logic        arvalid,    // Read address valid
    output logic        arready,    // Read address ready
    output logic [31:0] rdata,      // Read data
    output logic [1:0]  rresp,      // Read response: OKAY, or SLVERR if unmapped
    output logic        rvalid,     // Read data valid
    input  logic        rready,     // Read data ready
    input  logic        irq_in,     // Asynchronous interrupt requests
    output logic        irq_out     // Masked request; high while any enabled source pends
);

    logic pending_value;  // PENDING.value (W1C) — current value
    logic pending_value_set;  // PENDING.value (W1C) — set request; a set beats a same-cycle clear
    logic enable_value;  // ENABLE.value (RW)
    logic status_value;  // STATUS.value (RO) — sampled on read
    logic aw_hs;  // Write address captured, awaiting the data beat
    logic w_hs;  // Write data captured, awaiting the address beat
    logic [3:0] awaddr_q;  // Captured write address
    logic [31:0] wdata_q;  // Captured write data
    logic [3:0] wstrb_q;  // Captured write byte strobes
    logic [31:0] wmask;  // Captured strobes expanded to a bit mask

    assign awready = (!aw_hs) && (!bvalid);

    assign wready = (!w_hs) && (!bvalid);

    assign arready = !rvalid;

    assign wmask = {{8{wstrb_q[3]}}, {8{wstrb_q[2]}}, {8{wstrb_q[1]}}, {8{wstrb_q[0]}}};

    logic wr_exec;  // Both write channels captured and no response pending

    assign wr_exec = (aw_hs && w_hs) && (!bvalid);

    logic wr_addr_pending;  // Write address selects PENDING

    assign wr_addr_pending = wr_exec && (awaddr_q == 4'h0);

    logic wr_addr_enable;  // Write address selects ENABLE

    assign wr_addr_enable = wr_exec && (awaddr_q == 4'h4);

    logic wr_addr_status;  // Write address selects STATUS

    assign wr_addr_status = wr_exec && (awaddr_q == 4'h8);

    logic wr_hit;  // The write address matched a register

    assign wr_hit = (wr_addr_pending || wr_addr_enable) || wr_addr_status;

    logic [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = ((wr_addr_pending ? 32'hFFFFFFFE : 32'b0) | (wr_addr_enable ? 32'hFFFFFFFE : 32'b0)) | (wr_addr_status ? 32'hFFFFFFFF : 32'b0);

    logic wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    logic wr_sel_pending;  // Write updates PENDING

    assign wr_sel_pending = wr_addr_pending && (!wr_reserved);

    logic wr_sel_enable;  // Write updates ENABLE

    assign wr_sel_enable = wr_addr_enable && (!wr_reserved);

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            aw_hs <= 1'b0;
            w_hs <= 1'b0;
            bvalid <= 1'b0;
            bresp <= 2'b0;
            rvalid <= 1'b0;
            rresp <= 2'b0;
            rdata <= 32'b0;
            pending_value <= 1'd0;
            enable_value <= 1'd0;
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
            if (wr_sel_pending) begin
                pending_value <= (pending_value & (~(wdata_q[0] & wmask[0]))) | pending_value_set;
            end else begin
                pending_value <= pending_value | pending_value_set;
            end
            if (wr_sel_enable) begin
                enable_value <= (wdata_q[0] & wmask[0]) | (enable_value & (~wmask[0]));
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    4'h0: begin
                        rdata <= {31'b0, pending_value};
                        rresp <= 2'b0;
                    end
                    4'h4: begin
                        rdata <= {31'b0, enable_value};
                        rresp <= 2'b0;
                    end
                    4'h8: begin
                        rdata <= {31'b0, status_value};
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

    logic irq_sync0;  // Request synchroniser stage 0
    logic irq_sync1;  // Request synchroniser stage 1
    logic irq_hist;  // Previous settled request, for edge detection

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            irq_sync0 <= 1'b0;
            irq_sync1 <= 1'b0;
            irq_hist <= 1'b0;
        end else begin
            irq_sync0 <= irq_in;
            irq_sync1 <= irq_sync0;
            irq_hist <= irq_sync1;
        end
    end

    assign pending_value_set = irq_sync1 & (~irq_hist);

    assign status_value = pending_value & enable_value;

    assign irq_out = |status_value;

endmodule
