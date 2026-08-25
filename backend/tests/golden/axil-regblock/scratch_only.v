// SemiCraft v0.3.0
// Snippet: axil_regblock (config hash: 77eb4cb0dad0)
// AXI4-Lite register block, 32-bit data, 1 register(s)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_regblock (
    input  wire        aclk,           // AXI clock; everything is synchronous to it
    input  wire        areset_n,       // AXI reset, active-low (spec: ARESETn)
    input  wire [1:0]  awaddr,         // Write address (byte address)
    input  wire        awvalid,        // Write address valid
    output wire        awready,        // Write address ready
    input  wire [31:0] wdata,          // Write data
    input  wire [3:0]  wstrb,          // Write byte strobes, one bit per byte
    input  wire        wvalid,         // Write data valid
    output wire        wready,         // Write data ready
    output reg  [1:0]  bresp,          // Write response: OKAY, or SLVERR if unmapped
    output reg         bvalid,         // Write response valid
    input  wire        bready,         // Write response ready
    input  wire [1:0]  araddr,         // Read address (byte address)
    input  wire        arvalid,        // Read address valid
    output wire        arready,        // Read address ready
    output reg  [31:0] rdata,          // Read data
    output reg  [1:0]  rresp,          // Read response: OKAY, or SLVERR if unmapped
    output reg         rvalid,         // Read data valid
    input  wire        rready,         // Read data ready
    output reg  [31:0] scratch_value   // SCRATCH.value (RW)
);

    reg aw_hs;  // Write address captured, awaiting the data beat
    reg w_hs;  // Write data captured, awaiting the address beat
    reg [1:0] awaddr_q;  // Captured write address
    reg [31:0] wdata_q;  // Captured write data
    reg [3:0] wstrb_q;  // Captured write byte strobes
    wire [31:0] wmask;  // Captured strobes expanded to a bit mask

    assign awready = (!aw_hs) && (!bvalid);

    assign wready = (!w_hs) && (!bvalid);

    assign arready = !rvalid;

    assign wmask = {{8{wstrb_q[3]}}, {8{wstrb_q[2]}}, {8{wstrb_q[1]}}, {8{wstrb_q[0]}}};

    wire wr_exec;  // Both write channels captured and no response pending

    assign wr_exec = (aw_hs && w_hs) && (!bvalid);

    wire wr_addr_scratch;  // Write address selects SCRATCH

    assign wr_addr_scratch = wr_exec && (awaddr_q == 2'h0);

    wire wr_hit;  // The write address matched a register

    assign wr_hit = wr_addr_scratch;

    wire [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = wr_addr_scratch ? 32'h0 : 32'b0;

    wire wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

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
            if (wr_sel_scratch) begin
                scratch_value <= (wdata_q[31:0] & wmask[31:0]) | (scratch_value & (~wmask[31:0]));
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    2'h0: begin
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
