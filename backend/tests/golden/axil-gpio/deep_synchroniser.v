// SemiCraft v0.4.0
// Snippet: axil_gpio (config hash: 5d2cbe7cc1a5)
// AXI4-Lite GPIO, 8 pin(s)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_gpio (
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
    input  wire [7:0]  gpio_in,    // Asynchronous pin inputs
    output wire [7:0]  gpio_out,   // Pin output values
    output wire [7:0]  gpio_oe     // Pin output enables (1 = drive)
);

    reg [7:0] dir_value;  // DIR.value (RW)
    reg [7:0] out_value;  // OUT.value (RW)
    wire [7:0] in_value;  // IN.value (RO) — sampled on read
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

    wire wr_addr_dir;  // Write address selects DIR

    assign wr_addr_dir = wr_exec && (awaddr_q == 4'h0);

    wire wr_addr_out;  // Write address selects OUT

    assign wr_addr_out = wr_exec && (awaddr_q == 4'h4);

    wire wr_addr_in;  // Write address selects IN

    assign wr_addr_in = wr_exec && (awaddr_q == 4'h8);

    wire wr_hit;  // The write address matched a register

    assign wr_hit = (wr_addr_dir || wr_addr_out) || wr_addr_in;

    wire [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = ((wr_addr_dir ? 32'hFFFFFF00 : 32'b0) | (wr_addr_out ? 32'hFFFFFF00 : 32'b0)) | (wr_addr_in ? 32'hFFFFFFFF : 32'b0);

    wire wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    wire wr_sel_dir;  // Write updates DIR

    assign wr_sel_dir = wr_addr_dir && (!wr_reserved);

    wire wr_sel_out;  // Write updates OUT

    assign wr_sel_out = wr_addr_out && (!wr_reserved);

    always @(posedge aclk) begin
        if (!areset_n) begin
            aw_hs <= 1'b0;
            w_hs <= 1'b0;
            bvalid <= 1'b0;
            bresp <= 2'b0;
            rvalid <= 1'b0;
            rresp <= 2'b0;
            rdata <= 32'b0;
            dir_value <= 8'd0;
            out_value <= 8'd0;
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
            if (wr_sel_dir) begin
                dir_value <= (wdata_q[7:0] & wmask[7:0]) | (dir_value & (~wmask[7:0]));
            end
            if (wr_sel_out) begin
                out_value <= (wdata_q[7:0] & wmask[7:0]) | (out_value & (~wmask[7:0]));
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    4'h0: begin
                        rdata <= {24'b0, dir_value};
                        rresp <= 2'b0;
                    end
                    4'h4: begin
                        rdata <= {24'b0, out_value};
                        rresp <= 2'b0;
                    end
                    4'h8: begin
                        rdata <= {24'b0, in_value};
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

    reg [7:0] in_sync0;  // Input synchroniser stage 0
    reg [7:0] in_sync1;  // Input synchroniser stage 1
    reg [7:0] in_sync2;  // Input synchroniser stage 2
    reg [7:0] in_sync3;  // Input synchroniser stage 3

    always @(posedge aclk) begin
        if (!areset_n) begin
            in_sync0 <= 8'd0;
            in_sync1 <= 8'd0;
            in_sync2 <= 8'd0;
            in_sync3 <= 8'd0;
        end else begin
            in_sync0 <= gpio_in;
            in_sync1 <= in_sync0;
            in_sync2 <= in_sync1;
            in_sync3 <= in_sync2;
        end
    end

    assign gpio_oe = dir_value;

    assign gpio_out = out_value;

    assign in_value = in_sync3;

endmodule
