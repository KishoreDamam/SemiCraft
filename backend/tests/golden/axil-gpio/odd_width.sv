// SemiCraft v0.4.0
// Snippet: axil_gpio (config hash: bc2d452f2b0e)
// AXI4-Lite GPIO, 13 pin(s)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_gpio (
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
    input  logic [12:0] gpio_in,    // Asynchronous pin inputs
    output logic [12:0] gpio_out,   // Pin output values
    output logic [12:0] gpio_oe     // Pin output enables (1 = drive)
);

    logic [12:0] dir_value;  // DIR.value (RW)
    logic [12:0] out_value;  // OUT.value (RW)
    logic [12:0] in_value;  // IN.value (RO) — sampled on read
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

    logic wr_addr_dir;  // Write address selects DIR

    assign wr_addr_dir = wr_exec && (awaddr_q == 4'h0);

    logic wr_addr_out;  // Write address selects OUT

    assign wr_addr_out = wr_exec && (awaddr_q == 4'h4);

    logic wr_addr_in;  // Write address selects IN

    assign wr_addr_in = wr_exec && (awaddr_q == 4'h8);

    logic wr_hit;  // The write address matched a register

    assign wr_hit = (wr_addr_dir || wr_addr_out) || wr_addr_in;

    logic [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = ((wr_addr_dir ? 32'hFFFFE000 : 32'b0) | (wr_addr_out ? 32'hFFFFE000 : 32'b0)) | (wr_addr_in ? 32'hFFFFFFFF : 32'b0);

    logic wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    logic wr_sel_dir;  // Write updates DIR

    assign wr_sel_dir = wr_addr_dir && (!wr_reserved);

    logic wr_sel_out;  // Write updates OUT

    assign wr_sel_out = wr_addr_out && (!wr_reserved);

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            aw_hs <= 1'b0;
            w_hs <= 1'b0;
            bvalid <= 1'b0;
            bresp <= 2'b0;
            rvalid <= 1'b0;
            rresp <= 2'b0;
            rdata <= 32'b0;
            dir_value <= 13'd0;
            out_value <= 13'd0;
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
                dir_value <= (wdata_q[12:0] & wmask[12:0]) | (dir_value & (~wmask[12:0]));
            end
            if (wr_sel_out) begin
                out_value <= (wdata_q[12:0] & wmask[12:0]) | (out_value & (~wmask[12:0]));
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    4'h0: begin
                        rdata <= {19'b0, dir_value};
                        rresp <= 2'b0;
                    end
                    4'h4: begin
                        rdata <= {19'b0, out_value};
                        rresp <= 2'b0;
                    end
                    4'h8: begin
                        rdata <= {19'b0, in_value};
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

    logic [12:0] in_sync0;  // Input synchroniser stage 0
    logic [12:0] in_sync1;  // Input synchroniser stage 1

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            in_sync0 <= 13'd0;
            in_sync1 <= 13'd0;
        end else begin
            in_sync0 <= gpio_in;
            in_sync1 <= in_sync0;
        end
    end

    assign gpio_oe = dir_value;

    assign gpio_out = out_value;

    assign in_value = in_sync1;

endmodule
