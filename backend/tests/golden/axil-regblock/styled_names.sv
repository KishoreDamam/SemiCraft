// SemiCraft v0.4.0
// Snippet: axil_regblock (config hash: 9e0a82cbd583)
// AXI4-Lite register block, 32-bit data, 5 register(s)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_regblock (
    input  logic        p_aclk,           // AXI clock; everything is synchronous to it
    input  logic        p_areset_n,       // AXI reset, active-low (spec: ARESETn)
    input  logic [4:0]  p_awaddr,         // Write address (byte address)
    input  logic        p_awvalid,        // Write address valid
    output logic        p_awready,        // Write address ready
    input  logic [31:0] p_wdata,          // Write data
    input  logic [3:0]  p_wstrb,          // Write byte strobes, one bit per byte
    input  logic        p_wvalid,         // Write data valid
    output logic        p_wready,         // Write data ready
    output logic [1:0]  p_bresp,          // Write response: OKAY, or SLVERR if unmapped
    output logic        p_bvalid,         // Write response valid
    input  logic        p_bready,         // Write response ready
    input  logic [4:0]  p_araddr,         // Read address (byte address)
    input  logic        p_arvalid,        // Read address valid
    output logic        p_arready,        // Read address ready
    output logic [31:0] p_rdata,          // Read data
    output logic [1:0]  p_rresp,          // Read response: OKAY, or SLVERR if unmapped
    output logic        p_rvalid,         // Read data valid
    input  logic        p_rready,         // Read data ready
    output logic        p_ctrl0Enable,    // CTRL0.enable (RW)
    output logic [1:0]  p_ctrl0Mode,      // CTRL0.mode (RW)
    output logic [3:0]  p_ctrl0Level,     // CTRL0.level (RW)
    input  logic        p_status0Busy,    // STATUS0.busy (RO) — sampled on read
    input  logic [3:0]  p_status0Code,    // STATUS0.code (RO) — sampled on read
    output logic [3:0]  p_irq0Flags,      // IRQ0.flags (W1C) — current value
    input  logic [3:0]  p_irq0FlagsSet,   // IRQ0.flags (W1C) — set request; a set beats a same-cycle clear
    output logic        p_cmd0Go,         // CMD0.go (WO) — reads back as 0
    output logic [2:0]  p_cmd0Code,       // CMD0.code (WO) — reads back as 0
    output logic [31:0] p_scratchValue    // SCRATCH.value (RW)
);

    logic p_awHs;  // Write address captured, awaiting the data beat
    logic p_wHs;  // Write data captured, awaiting the address beat
    logic [4:0] p_awaddrQ;  // Captured write address
    logic [31:0] p_wdataQ;  // Captured write data
    logic [3:0] p_wstrbQ;  // Captured write byte strobes
    logic [31:0] p_wmask;  // Captured strobes expanded to a bit mask

    assign p_awready = (!p_awHs) && (!p_bvalid);

    assign p_wready = (!p_wHs) && (!p_bvalid);

    assign p_arready = !p_rvalid;

    assign p_wmask = {{8{p_wstrbQ[3]}}, {8{p_wstrbQ[2]}}, {8{p_wstrbQ[1]}}, {8{p_wstrbQ[0]}}};

    logic p_wrExec;  // Both write channels captured and no response pending

    assign p_wrExec = (p_awHs && p_wHs) && (!p_bvalid);

    logic p_wrAddrCtrl0;  // Write address selects CTRL0

    assign p_wrAddrCtrl0 = p_wrExec && (p_awaddrQ == 5'h0);

    logic p_wrAddrStatus0;  // Write address selects STATUS0

    assign p_wrAddrStatus0 = p_wrExec && (p_awaddrQ == 5'h4);

    logic p_wrAddrIrq0;  // Write address selects IRQ0

    assign p_wrAddrIrq0 = p_wrExec && (p_awaddrQ == 5'h8);

    logic p_wrAddrCmd0;  // Write address selects CMD0

    assign p_wrAddrCmd0 = p_wrExec && (p_awaddrQ == 5'hC);

    logic p_wrAddrScratch;  // Write address selects SCRATCH

    assign p_wrAddrScratch = p_wrExec && (p_awaddrQ == 5'h10);

    logic p_wrHit;  // The write address matched a register

    assign p_wrHit = (((p_wrAddrCtrl0 || p_wrAddrStatus0) || p_wrAddrIrq0) || p_wrAddrCmd0) || p_wrAddrScratch;

    logic [31:0] p_wrRsvdMask;  // Bits the addressed register does not implement

    assign p_wrRsvdMask = ((((p_wrAddrCtrl0 ? 32'hFFFFFF08 : 32'b0) | (p_wrAddrStatus0 ? 32'hFFFFFFFF : 32'b0)) | (p_wrAddrIrq0 ? 32'hFFFFFFF0 : 32'b0)) | (p_wrAddrCmd0 ? 32'hFFFFFFF0 : 32'b0)) | (p_wrAddrScratch ? 32'h0 : 32'b0);

    logic p_wrReserved;  // The write tries to set a reserved bit

    assign p_wrReserved = |((p_wdataQ & p_wmask) & p_wrRsvdMask);

    logic p_wrSelCtrl0;  // Write updates CTRL0

    assign p_wrSelCtrl0 = p_wrAddrCtrl0 && (!p_wrReserved);

    logic p_wrSelIrq0;  // Write updates IRQ0

    assign p_wrSelIrq0 = p_wrAddrIrq0 && (!p_wrReserved);

    logic p_wrSelCmd0;  // Write updates CMD0

    assign p_wrSelCmd0 = p_wrAddrCmd0 && (!p_wrReserved);

    logic p_wrSelScratch;  // Write updates SCRATCH

    assign p_wrSelScratch = p_wrAddrScratch && (!p_wrReserved);

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_awHs <= 1'b0;
            p_wHs <= 1'b0;
            p_bvalid <= 1'b0;
            p_bresp <= 2'b0;
            p_rvalid <= 1'b0;
            p_rresp <= 2'b0;
            p_rdata <= 32'b0;
            p_ctrl0Enable <= 1'd1;
            p_ctrl0Mode <= 2'd0;
            p_ctrl0Level <= 4'd0;
            p_irq0Flags <= 4'd0;
            p_cmd0Go <= 1'd0;
            p_cmd0Code <= 3'd0;
            p_scratchValue <= 32'd0;
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
            if (p_wrSelCtrl0) begin
                p_ctrl0Enable <= (p_wdataQ[0] & p_wmask[0]) | (p_ctrl0Enable & (~p_wmask[0]));
                p_ctrl0Mode <= (p_wdataQ[2:1] & p_wmask[2:1]) | (p_ctrl0Mode & (~p_wmask[2:1]));
                p_ctrl0Level <= (p_wdataQ[7:4] & p_wmask[7:4]) | (p_ctrl0Level & (~p_wmask[7:4]));
            end
            if (p_wrSelIrq0) begin
                p_irq0Flags <= (p_irq0Flags & (~(p_wdataQ[3:0] & p_wmask[3:0]))) | p_irq0FlagsSet;
            end else begin
                p_irq0Flags <= p_irq0Flags | p_irq0FlagsSet;
            end
            if (p_wrSelCmd0) begin
                p_cmd0Go <= (p_wdataQ[0] & p_wmask[0]) | (p_cmd0Go & (~p_wmask[0]));
                p_cmd0Code <= (p_wdataQ[3:1] & p_wmask[3:1]) | (p_cmd0Code & (~p_wmask[3:1]));
            end
            if (p_wrSelScratch) begin
                p_scratchValue <= (p_wdataQ[31:0] & p_wmask[31:0]) | (p_scratchValue & (~p_wmask[31:0]));
            end
            if (p_arvalid && p_arready) begin
                p_rvalid <= 1'b1;
                case (p_araddr)
                    5'h0: begin
                        p_rdata <= {24'b0, p_ctrl0Level, 1'b0, p_ctrl0Mode, p_ctrl0Enable};
                        p_rresp <= 2'b0;
                    end
                    5'h4: begin
                        p_rdata <= {24'b0, p_status0Code, 3'b0, p_status0Busy};
                        p_rresp <= 2'b0;
                    end
                    5'h8: begin
                        p_rdata <= {28'b0, p_irq0Flags};
                        p_rresp <= 2'b0;
                    end
                    5'hC: begin
                        p_rdata <= {28'b0, 3'b0, 1'b0};
                        p_rresp <= 2'b0;
                    end
                    5'h10: begin
                        p_rdata <= p_scratchValue;
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

endmodule
