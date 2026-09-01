// SemiCraft v0.4.0
// Snippet: axil_regblock (config hash: dc8abcaae2e5)
// AXI4-Lite register block, 32-bit data, 5 register(s)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_regblock (
    input  wire        aclk,             // AXI clock; everything is synchronous to it
    input  wire        areset_n,         // AXI reset, active-low (spec: ARESETn)
    input  wire [4:0]  awaddr,           // Write address (byte address)
    input  wire        awvalid,          // Write address valid
    output wire        awready,          // Write address ready
    input  wire [31:0] wdata,            // Write data
    input  wire [3:0]  wstrb,            // Write byte strobes, one bit per byte
    input  wire        wvalid,           // Write data valid
    output wire        wready,           // Write data ready
    output reg  [1:0]  bresp,            // Write response: OKAY, or SLVERR if unmapped
    output reg         bvalid,           // Write response valid
    input  wire        bready,           // Write response ready
    input  wire [4:0]  araddr,           // Read address (byte address)
    input  wire        arvalid,          // Read address valid
    output wire        arready,          // Read address ready
    output reg  [31:0] rdata,            // Read data
    output reg  [1:0]  rresp,            // Read response: OKAY, or SLVERR if unmapped
    output reg         rvalid,           // Read data valid
    input  wire        rready,           // Read data ready
    output reg         ctrl0_enable,     // CTRL0.enable (RW)
    output reg  [1:0]  ctrl0_mode,       // CTRL0.mode (RW)
    output reg  [3:0]  ctrl0_level,      // CTRL0.level (RW)
    input  wire        status0_busy,     // STATUS0.busy (RO) — sampled on read
    input  wire [3:0]  status0_code,     // STATUS0.code (RO) — sampled on read
    output reg  [3:0]  irq0_flags,       // IRQ0.flags (W1C) — current value
    input  wire [3:0]  irq0_flags_set,   // IRQ0.flags (W1C) — set request; a set beats a same-cycle clear
    output reg         cmd0_go,          // CMD0.go (WO) — reads back as 0
    output reg  [2:0]  cmd0_code,        // CMD0.code (WO) — reads back as 0
    output reg  [31:0] scratch_value     // SCRATCH.value (RW)
);

    reg aw_hs;  // Write address captured, awaiting the data beat
    reg w_hs;  // Write data captured, awaiting the address beat
    reg [4:0] awaddr_q;  // Captured write address
    reg [31:0] wdata_q;  // Captured write data
    reg [3:0] wstrb_q;  // Captured write byte strobes
    wire [31:0] wmask;  // Captured strobes expanded to a bit mask

    assign awready = (!aw_hs) && (!bvalid);

    assign wready = (!w_hs) && (!bvalid);

    assign arready = !rvalid;

    assign wmask = {{8{wstrb_q[3]}}, {8{wstrb_q[2]}}, {8{wstrb_q[1]}}, {8{wstrb_q[0]}}};

    wire wr_exec;  // Both write channels captured and no response pending

    assign wr_exec = (aw_hs && w_hs) && (!bvalid);

    wire wr_addr_ctrl0;  // Write address selects CTRL0

    assign wr_addr_ctrl0 = wr_exec && (awaddr_q == 5'h0);

    wire wr_addr_status0;  // Write address selects STATUS0

    assign wr_addr_status0 = wr_exec && (awaddr_q == 5'h4);

    wire wr_addr_irq0;  // Write address selects IRQ0

    assign wr_addr_irq0 = wr_exec && (awaddr_q == 5'h8);

    wire wr_addr_cmd0;  // Write address selects CMD0

    assign wr_addr_cmd0 = wr_exec && (awaddr_q == 5'hC);

    wire wr_addr_scratch;  // Write address selects SCRATCH

    assign wr_addr_scratch = wr_exec && (awaddr_q == 5'h10);

    wire wr_hit;  // The write address matched a register

    assign wr_hit = (((wr_addr_ctrl0 || wr_addr_status0) || wr_addr_irq0) || wr_addr_cmd0) || wr_addr_scratch;

    wire [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = ((((wr_addr_ctrl0 ? 32'hFFFFFF08 : 32'b0) | (wr_addr_status0 ? 32'hFFFFFFFF : 32'b0)) | (wr_addr_irq0 ? 32'hFFFFFFF0 : 32'b0)) | (wr_addr_cmd0 ? 32'hFFFFFFF0 : 32'b0)) | (wr_addr_scratch ? 32'h0 : 32'b0);

    wire wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    wire wr_sel_ctrl0;  // Write updates CTRL0

    assign wr_sel_ctrl0 = wr_addr_ctrl0 && (!wr_reserved);

    wire wr_sel_irq0;  // Write updates IRQ0

    assign wr_sel_irq0 = wr_addr_irq0 && (!wr_reserved);

    wire wr_sel_cmd0;  // Write updates CMD0

    assign wr_sel_cmd0 = wr_addr_cmd0 && (!wr_reserved);

    wire wr_sel_scratch;  // Write updates SCRATCH

    assign wr_sel_scratch = wr_addr_scratch && (!wr_reserved);

    always @(posedge aclk) begin
        if (!areset_n) begin
            aw_hs <= 1'b0;
            w_hs <= 1'b0;
            bvalid <= 1'b0;
            bresp <= 2'b0;
            rvalid <= 1'b0;
            rresp <= 2'b0;
            rdata <= 32'b0;
            ctrl0_enable <= 1'd1;
            ctrl0_mode <= 2'd0;
            ctrl0_level <= 4'd0;
            irq0_flags <= 4'd0;
            cmd0_go <= 1'd0;
            cmd0_code <= 3'd0;
            scratch_value <= 32'd0;
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
            if (wr_sel_ctrl0) begin
                ctrl0_enable <= (wdata_q[0] & wmask[0]) | (ctrl0_enable & (~wmask[0]));
                ctrl0_mode <= (wdata_q[2:1] & wmask[2:1]) | (ctrl0_mode & (~wmask[2:1]));
                ctrl0_level <= (wdata_q[7:4] & wmask[7:4]) | (ctrl0_level & (~wmask[7:4]));
            end
            if (wr_sel_irq0) begin
                irq0_flags <= (irq0_flags & (~(wdata_q[3:0] & wmask[3:0]))) | irq0_flags_set;
            end else begin
                irq0_flags <= irq0_flags | irq0_flags_set;
            end
            if (wr_sel_cmd0) begin
                cmd0_go <= (wdata_q[0] & wmask[0]) | (cmd0_go & (~wmask[0]));
                cmd0_code <= (wdata_q[3:1] & wmask[3:1]) | (cmd0_code & (~wmask[3:1]));
            end
            if (wr_sel_scratch) begin
                scratch_value <= (wdata_q[31:0] & wmask[31:0]) | (scratch_value & (~wmask[31:0]));
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    5'h0: begin
                        rdata <= {24'b0, ctrl0_level, 1'b0, ctrl0_mode, ctrl0_enable};
                        rresp <= 2'b0;
                    end
                    5'h4: begin
                        rdata <= {24'b0, status0_code, 3'b0, status0_busy};
                        rresp <= 2'b0;
                    end
                    5'h8: begin
                        rdata <= {28'b0, irq0_flags};
                        rresp <= 2'b0;
                    end
                    5'hC: begin
                        rdata <= {28'b0, 3'b0, 1'b0};
                        rresp <= 2'b0;
                    end
                    5'h10: begin
                        rdata <= scratch_value;
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

endmodule
