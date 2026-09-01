// SemiCraft v0.4.0
// Snippet: axil_gpio (config hash: 28458bc0a6db)
// AXI4-Lite GPIO, 8 pin(s)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_gpio (
    input  logic        p_aclk,       // AXI clock; everything is synchronous to it
    input  logic        p_areset_n,   // AXI reset, active-low (spec: ARESETn)
    input  logic [3:0]  p_awaddr,     // Write address (byte address)
    input  logic        p_awvalid,    // Write address valid
    output logic        p_awready,    // Write address ready
    input  logic [31:0] p_wdata,      // Write data
    input  logic [3:0]  p_wstrb,      // Write byte strobes, one bit per byte
    input  logic        p_wvalid,     // Write data valid
    output logic        p_wready,     // Write data ready
    output logic [1:0]  p_bresp,      // Write response: OKAY, or SLVERR if unmapped
    output logic        p_bvalid,     // Write response valid
    input  logic        p_bready,     // Write response ready
    input  logic [3:0]  p_araddr,     // Read address (byte address)
    input  logic        p_arvalid,    // Read address valid
    output logic        p_arready,    // Read address ready
    output logic [31:0] p_rdata,      // Read data
    output logic [1:0]  p_rresp,      // Read response: OKAY, or SLVERR if unmapped
    output logic        p_rvalid,     // Read data valid
    input  logic        p_rready,     // Read data ready
    input  logic [7:0]  p_gpioIn,     // Asynchronous pin inputs
    output logic [7:0]  p_gpioOut,    // Pin output values
    output logic [7:0]  p_gpioOe      // Pin output enables (1 = drive)
);

    logic [7:0] p_dirValue;  // DIR.value (RW)
    logic [7:0] p_outValue;  // OUT.value (RW)
    logic [7:0] p_inValue;  // IN.value (RO) — sampled on read
    logic p_awHs;  // Write address captured, awaiting the data beat
    logic p_wHs;  // Write data captured, awaiting the address beat
    logic [3:0] p_awaddrQ;  // Captured write address
    logic [31:0] p_wdataQ;  // Captured write data
    logic [3:0] p_wstrbQ;  // Captured write byte strobes
    logic [31:0] p_wmask;  // Captured strobes expanded to a bit mask

    assign p_awready = (!p_awHs) && (!p_bvalid);

    assign p_wready = (!p_wHs) && (!p_bvalid);

    assign p_arready = !p_rvalid;

    assign p_wmask = {{8{p_wstrbQ[3]}}, {8{p_wstrbQ[2]}}, {8{p_wstrbQ[1]}}, {8{p_wstrbQ[0]}}};

    logic p_wrExec;  // Both write channels captured and no response pending

    assign p_wrExec = (p_awHs && p_wHs) && (!p_bvalid);

    logic p_wrAddrDir;  // Write address selects DIR

    assign p_wrAddrDir = p_wrExec && (p_awaddrQ == 4'h0);

    logic p_wrAddrOut;  // Write address selects OUT

    assign p_wrAddrOut = p_wrExec && (p_awaddrQ == 4'h4);

    logic p_wrAddrIn;  // Write address selects IN

    assign p_wrAddrIn = p_wrExec && (p_awaddrQ == 4'h8);

    logic p_wrHit;  // The write address matched a register

    assign p_wrHit = (p_wrAddrDir || p_wrAddrOut) || p_wrAddrIn;

    logic [31:0] p_wrRsvdMask;  // Bits the addressed register does not implement

    assign p_wrRsvdMask = ((p_wrAddrDir ? 32'hFFFFFF00 : 32'b0) | (p_wrAddrOut ? 32'hFFFFFF00 : 32'b0)) | (p_wrAddrIn ? 32'hFFFFFFFF : 32'b0);

    logic p_wrReserved;  // The write tries to set a reserved bit

    assign p_wrReserved = |((p_wdataQ & p_wmask) & p_wrRsvdMask);

    logic p_wrSelDir;  // Write updates DIR

    assign p_wrSelDir = p_wrAddrDir && (!p_wrReserved);

    logic p_wrSelOut;  // Write updates OUT

    assign p_wrSelOut = p_wrAddrOut && (!p_wrReserved);

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_awHs <= 1'b0;
            p_wHs <= 1'b0;
            p_bvalid <= 1'b0;
            p_bresp <= 2'b0;
            p_rvalid <= 1'b0;
            p_rresp <= 2'b0;
            p_rdata <= 32'b0;
            p_dirValue <= 8'd0;
            p_outValue <= 8'd0;
        end else begin
            if (p_awvalid && p_awready) begin
                p_awHs <= 1'b1;
                p_awaddrQ <= p_awaddr;
            end
            if (p_wvalid && p_wready) begin
                p_wHs <= 1'b1;
                p_wdataQ <= p_wdata;
                p_wstrbQ <= p_wstrb;
            end
            if (p_wrExec) begin
                p_awHs <= 1'b0;
                p_wHs <= 1'b0;
                p_bvalid <= 1'b1;
                p_bresp <= (p_wrHit && (!p_wrReserved)) ? 2'b0 : 2'b10;
            end
            if (p_bvalid && p_bready) begin
                p_bvalid <= 1'b0;
            end
            if (p_wrSelDir) begin
                p_dirValue <= (p_wdataQ[7:0] & p_wmask[7:0]) | (p_dirValue & (~p_wmask[7:0]));
            end
            if (p_wrSelOut) begin
                p_outValue <= (p_wdataQ[7:0] & p_wmask[7:0]) | (p_outValue & (~p_wmask[7:0]));
            end
            if (p_arvalid && p_arready) begin
                p_rvalid <= 1'b1;
                case (p_araddr)
                    4'h0: begin
                        p_rdata <= {24'b0, p_dirValue};
                        p_rresp <= 2'b0;
                    end
                    4'h4: begin
                        p_rdata <= {24'b0, p_outValue};
                        p_rresp <= 2'b0;
                    end
                    4'h8: begin
                        p_rdata <= {24'b0, p_inValue};
                        p_rresp <= 2'b0;
                    end
                    default: begin
                        p_rdata <= 32'b0;
                        p_rresp <= 2'b10;
                    end
                endcase
            end
            if (p_rvalid && p_rready) begin
                p_rvalid <= 1'b0;
            end
        end
    end

    logic [7:0] p_inSync0;  // Input synchroniser stage 0
    logic [7:0] p_inSync1;  // Input synchroniser stage 1

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_inSync0 <= 8'd0;
            p_inSync1 <= 8'd0;
        end else begin
            p_inSync0 <= p_gpioIn;
            p_inSync1 <= p_inSync0;
        end
    end

    assign p_gpioOe = p_dirValue;

    assign p_gpioOut = p_outValue;

    assign p_inValue = p_inSync1;

endmodule
