// SemiCraft v0.4.0
// Snippet: axil_intc (config hash: a56bc587e07c)
// AXI4-Lite interrupt controller, 24 source(s), level-triggered
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_intc (
    input  wire        aclk,       // AXI clock; everything is synchronous to it
    input  wire        areset_n,   // AXI reset, active-low (spec: ARESETn)
    input  wire [3:0]  awaddr,     // Write address (byte address)
    input  wire        awvalid,    // Write address valid
    output wire        awready,    // Write address ready
    input  wire [31:0] wdata,      // Write data
    input  wire [3:0]  wstrb,      // Write byte strobes, one bit per byte
    input  wire        wvalid,     // Write data valid
    output wire        wready,     // Write data ready
    output reg  [1:0]  bresp,      // Write response: OKAY, or SLVERR if unmapped
    output reg         bvalid,     // Write response valid
    input  wire        bready,     // Write response ready
    input  wire [3:0]  araddr,     // Read address (byte address)
    input  wire        arvalid,    // Read address valid
    output wire        arready,    // Read address ready
    output reg  [31:0] rdata,      // Read data
    output reg  [1:0]  rresp,      // Read response: OKAY, or SLVERR if unmapped
    output reg         rvalid,     // Read data valid
    input  wire        rready,     // Read data ready
    input  wire [23:0] irq_in,     // Asynchronous interrupt requests
    output wire        irq_out     // Masked request; high while any enabled source pends
);

    reg [23:0] pending_value;  // PENDING.value (W1C) — current value
    wire [23:0] pending_value_set;  // PENDING.value (W1C) — set request; a set beats a same-cycle clear
    reg [23:0] enable_value;  // ENABLE.value (RW)
    wire [23:0] status_value;  // STATUS.value (RO) — sampled on read
    reg aw_hs;  // Write address captured, awaiting the data beat
    reg w_hs;  // Write data captured, awaiting the address beat
    reg [3:0] awaddr_q;  // Captured write address
    reg [31:0] wdata_q;  // Captured write data
    reg [3:0] wstrb_q;  // Captured write byte strobes
    wire [31:0] wmask;  // Captured strobes expanded to a bit mask

    assign awready = (!aw_hs) && (!bvalid);

    assign wready = (!w_hs) && (!bvalid);

    assign arready = !rvalid;

    assign wmask = {{8{wstrb_q[3]}}, {8{wstrb_q[2]}}, {8{wstrb_q[1]}}, {8{wstrb_q[0]}}};

    wire wr_exec;  // Both write channels captured and no response pending

    assign wr_exec = (aw_hs && w_hs) && (!bvalid);

    wire wr_addr_pending;  // Write address selects PENDING

    assign wr_addr_pending = wr_exec && (awaddr_q == 4'h0);

    wire wr_addr_enable;  // Write address selects ENABLE

    assign wr_addr_enable = wr_exec && (awaddr_q == 4'h4);

    wire wr_addr_status;  // Write address selects STATUS

    assign wr_addr_status = wr_exec && (awaddr_q == 4'h8);

    wire wr_hit;  // The write address matched a register

    assign wr_hit = (wr_addr_pending || wr_addr_enable) || wr_addr_status;

    wire [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = ((wr_addr_pending ? 32'hFF000000 : 32'b0) | (wr_addr_enable ? 32'hFF000000 : 32'b0)) | (wr_addr_status ? 32'hFFFFFFFF : 32'b0);

    wire wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    wire wr_sel_pending;  // Write updates PENDING

    assign wr_sel_pending = wr_addr_pending && (!wr_reserved);

    wire wr_sel_enable;  // Write updates ENABLE

    assign wr_sel_enable = wr_addr_enable && (!wr_reserved);

    always @(posedge aclk) begin
        if (!areset_n) begin
            aw_hs <= 1'b0;
            w_hs <= 1'b0;
            bvalid <= 1'b0;
            bresp <= 2'b0;
            rvalid <= 1'b0;
            rresp <= 2'b0;
            rdata <= 32'b0;
            pending_value <= 24'd0;
            enable_value <= 24'd0;
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
                pending_value <= (pending_value & (~(wdata_q[23:0] & wmask[23:0]))) | pending_value_set;
            end else begin
                pending_value <= pending_value | pending_value_set;
            end
            if (wr_sel_enable) begin
                enable_value <= (wdata_q[23:0] & wmask[23:0]) | (enable_value & (~wmask[23:0]));
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    4'h0: begin
                        rdata <= {8'b0, pending_value};
                        rresp <= 2'b0;
                    end
                    4'h4: begin
                        rdata <= {8'b0, enable_value};
                        rresp <= 2'b0;
                    end
                    4'h8: begin
                        rdata <= {8'b0, status_value};
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

    reg [23:0] irq_sync0;  // Request synchroniser stage 0
    reg [23:0] irq_sync1;  // Request synchroniser stage 1
    reg [23:0] irq_sync2;  // Request synchroniser stage 2

    always @(posedge aclk) begin
        if (!areset_n) begin
            irq_sync0 <= 24'b0;
            irq_sync1 <= 24'b0;
            irq_sync2 <= 24'b0;
        end else begin
            irq_sync0 <= irq_in;
            irq_sync1 <= irq_sync0;
            irq_sync2 <= irq_sync1;
        end
    end

    assign pending_value_set = irq_sync2;

    assign status_value = pending_value & enable_value;

    assign irq_out = |status_value;

endmodule
