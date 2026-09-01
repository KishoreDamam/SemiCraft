// SemiCraft v0.4.0
// Snippet: axil_intc (config hash: 75a8ad364387)
// AXI4-Lite interrupt controller, 8 source(s), edge-triggered
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_intc (
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
    input  logic [7:0]  p_irqIn,      // Asynchronous interrupt requests
    output logic        p_irqOut      // Masked request; high while any enabled source pends
);

    logic [7:0] p_pendingValue;  // PENDING.value (W1C) — current value
    logic [7:0] p_pendingValueSet;  // PENDING.value (W1C) — set request; a set beats a same-cycle clear
    logic [7:0] p_enableValue;  // ENABLE.value (RW)
    logic [7:0] p_statusValue;  // STATUS.value (RO) — sampled on read
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

    logic p_wrAddrPending;  // Write address selects PENDING

    assign p_wrAddrPending = p_wrExec && (p_awaddrQ == 4'h0);

    logic p_wrAddrEnable;  // Write address selects ENABLE

    assign p_wrAddrEnable = p_wrExec && (p_awaddrQ == 4'h4);

    logic p_wrAddrStatus;  // Write address selects STATUS

    assign p_wrAddrStatus = p_wrExec && (p_awaddrQ == 4'h8);

    logic p_wrHit;  // The write address matched a register

    assign p_wrHit = (p_wrAddrPending || p_wrAddrEnable) || p_wrAddrStatus;

    logic [31:0] p_wrRsvdMask;  // Bits the addressed register does not implement

    assign p_wrRsvdMask = ((p_wrAddrPending ? 32'hFFFFFF00 : 32'b0) | (p_wrAddrEnable ? 32'hFFFFFF00 : 32'b0)) | (p_wrAddrStatus ? 32'hFFFFFFFF : 32'b0);

    logic p_wrReserved;  // The write tries to set a reserved bit

    assign p_wrReserved = |((p_wdataQ & p_wmask) & p_wrRsvdMask);

    logic p_wrSelPending;  // Write updates PENDING

    assign p_wrSelPending = p_wrAddrPending && (!p_wrReserved);

    logic p_wrSelEnable;  // Write updates ENABLE

    assign p_wrSelEnable = p_wrAddrEnable && (!p_wrReserved);

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_awHs <= 1'b0;
            p_wHs <= 1'b0;
            p_bvalid <= 1'b0;
            p_bresp <= 2'b0;
            p_rvalid <= 1'b0;
            p_rresp <= 2'b0;
            p_rdata <= 32'b0;
            p_pendingValue <= 8'd0;
            p_enableValue <= 8'd0;
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
            if (p_wrSelPending) begin
                p_pendingValue <= (p_pendingValue & (~(p_wdataQ[7:0] & p_wmask[7:0]))) | p_pendingValueSet;
            end else begin
                p_pendingValue <= p_pendingValue | p_pendingValueSet;
            end
            if (p_wrSelEnable) begin
                p_enableValue <= (p_wdataQ[7:0] & p_wmask[7:0]) | (p_enableValue & (~p_wmask[7:0]));
            end
            if (p_arvalid && p_arready) begin
                p_rvalid <= 1'b1;
                case (p_araddr)
                    4'h0: begin
                        p_rdata <= {24'b0, p_pendingValue};
                        p_rresp <= 2'b0;
                    end
                    4'h4: begin
                        p_rdata <= {24'b0, p_enableValue};
                        p_rresp <= 2'b0;
                    end
                    4'h8: begin
                        p_rdata <= {24'b0, p_statusValue};
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

    logic [7:0] p_irqSync0;  // Request synchroniser stage 0
    logic [7:0] p_irqSync1;  // Request synchroniser stage 1
    logic [7:0] p_irqHist;  // Previous settled request, for edge detection

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_irqSync0 <= 8'b0;
            p_irqSync1 <= 8'b0;
            p_irqHist <= 8'b0;
        end else begin
            p_irqSync0 <= p_irqIn;
            p_irqSync1 <= p_irqSync0;
            p_irqHist <= p_irqSync1;
        end
    end

    assign p_pendingValueSet = p_irqSync1 & (~p_irqHist);

    assign p_statusValue = p_pendingValue & p_enableValue;

    assign p_irqOut = |p_statusValue;

endmodule
