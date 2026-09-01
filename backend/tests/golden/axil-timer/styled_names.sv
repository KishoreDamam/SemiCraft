// SemiCraft v0.4.0
// Snippet: axil_timer (config hash: 0cd916fa1b61)
// AXI4-Lite timer, 32-bit counter, 16-bit prescaler
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_timer (
    input  logic        p_aclk,       // AXI clock; everything is synchronous to it
    input  logic        p_areset_n,   // AXI reset, active-low (spec: ARESETn)
    input  logic [4:0]  p_awaddr,     // Write address (byte address)
    input  logic        p_awvalid,    // Write address valid
    output logic        p_awready,    // Write address ready
    input  logic [31:0] p_wdata,      // Write data
    input  logic [3:0]  p_wstrb,      // Write byte strobes, one bit per byte
    input  logic        p_wvalid,     // Write data valid
    output logic        p_wready,     // Write data ready
    output logic [1:0]  p_bresp,      // Write response: OKAY, or SLVERR if unmapped
    output logic        p_bvalid,     // Write response valid
    input  logic        p_bready,     // Write response ready
    input  logic [4:0]  p_araddr,     // Read address (byte address)
    input  logic        p_arvalid,    // Read address valid
    output logic        p_arready,    // Read address ready
    output logic [31:0] p_rdata,      // Read data
    output logic [1:0]  p_rresp,      // Read response: OKAY, or SLVERR if unmapped
    output logic        p_rvalid,     // Read data valid
    input  logic        p_rready,     // Read data ready
    output logic        p_irq         // Interrupt request, level-sensitive
);

    logic p_ctrlEnable;  // CTRL.enable (RW)
    logic p_ctrlAutoReload;  // CTRL.auto_reload (RW)
    logic p_ctrlIrqEnable;  // CTRL.irq_enable (RW)
    logic [31:0] p_reloadValue;  // RELOAD.value (RW)
    logic [31:0] p_countValue;  // COUNT.value (RO) — sampled on read
    logic [15:0] p_prescaleValue;  // PRESCALE.value (RW)
    logic p_statusExpired;  // STATUS.expired (W1C) — current value
    logic p_statusExpiredSet;  // STATUS.expired (W1C) — set request; a set beats a same-cycle clear
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

    logic p_wrAddrCtrl;  // Write address selects CTRL

    assign p_wrAddrCtrl = p_wrExec && (p_awaddrQ == 5'h0);

    logic p_wrAddrReload;  // Write address selects RELOAD

    assign p_wrAddrReload = p_wrExec && (p_awaddrQ == 5'h4);

    logic p_wrAddrCount;  // Write address selects COUNT

    assign p_wrAddrCount = p_wrExec && (p_awaddrQ == 5'h8);

    logic p_wrAddrPrescale;  // Write address selects PRESCALE

    assign p_wrAddrPrescale = p_wrExec && (p_awaddrQ == 5'hC);

    logic p_wrAddrStatus;  // Write address selects STATUS

    assign p_wrAddrStatus = p_wrExec && (p_awaddrQ == 5'h10);

    logic p_wrHit;  // The write address matched a register

    assign p_wrHit = (((p_wrAddrCtrl || p_wrAddrReload) || p_wrAddrCount) || p_wrAddrPrescale) || p_wrAddrStatus;

    logic [31:0] p_wrRsvdMask;  // Bits the addressed register does not implement

    assign p_wrRsvdMask = ((((p_wrAddrCtrl ? 32'hFFFFFFF8 : 32'b0) | (p_wrAddrReload ? 32'h0 : 32'b0)) | (p_wrAddrCount ? 32'hFFFFFFFF : 32'b0)) | (p_wrAddrPrescale ? 32'hFFFF0000 : 32'b0)) | (p_wrAddrStatus ? 32'hFFFFFFFE : 32'b0);

    logic p_wrReserved;  // The write tries to set a reserved bit

    assign p_wrReserved = |((p_wdataQ & p_wmask) & p_wrRsvdMask);

    logic p_wrSelCtrl;  // Write updates CTRL

    assign p_wrSelCtrl = p_wrAddrCtrl && (!p_wrReserved);

    logic p_wrSelReload;  // Write updates RELOAD

    assign p_wrSelReload = p_wrAddrReload && (!p_wrReserved);

    logic p_wrSelPrescale;  // Write updates PRESCALE

    assign p_wrSelPrescale = p_wrAddrPrescale && (!p_wrReserved);

    logic p_wrSelStatus;  // Write updates STATUS

    assign p_wrSelStatus = p_wrAddrStatus && (!p_wrReserved);

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_awHs <= 1'b0;
            p_wHs <= 1'b0;
            p_bvalid <= 1'b0;
            p_bresp <= 2'b0;
            p_rvalid <= 1'b0;
            p_rresp <= 2'b0;
            p_rdata <= 32'b0;
            p_ctrlEnable <= 1'd0;
            p_ctrlAutoReload <= 1'd0;
            p_ctrlIrqEnable <= 1'd0;
            p_reloadValue <= 32'd0;
            p_prescaleValue <= 16'd0;
            p_statusExpired <= 1'd0;
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
            if (p_wrSelCtrl) begin
                p_ctrlEnable <= (p_wdataQ[0] & p_wmask[0]) | (p_ctrlEnable & (~p_wmask[0]));
                p_ctrlAutoReload <= (p_wdataQ[1] & p_wmask[1]) | (p_ctrlAutoReload & (~p_wmask[1]));
                p_ctrlIrqEnable <= (p_wdataQ[2] & p_wmask[2]) | (p_ctrlIrqEnable & (~p_wmask[2]));
            end
            if (p_wrSelReload) begin
                p_reloadValue <= (p_wdataQ[31:0] & p_wmask[31:0]) | (p_reloadValue & (~p_wmask[31:0]));
            end
            if (p_wrSelPrescale) begin
                p_prescaleValue <= (p_wdataQ[15:0] & p_wmask[15:0]) | (p_prescaleValue & (~p_wmask[15:0]));
            end
            if (p_wrSelStatus) begin
                p_statusExpired <= (p_statusExpired & (~(p_wdataQ[0] & p_wmask[0]))) | p_statusExpiredSet;
            end else begin
                p_statusExpired <= p_statusExpired | p_statusExpiredSet;
            end
            if (p_arvalid && p_arready) begin
                p_rvalid <= 1'b1;
                case (p_araddr)
                    5'h0: begin
                        p_rdata <= {29'b0, p_ctrlIrqEnable, p_ctrlAutoReload, p_ctrlEnable};
                        p_rresp <= 2'b0;
                    end
                    5'h4: begin
                        p_rdata <= p_reloadValue;
                        p_rresp <= 2'b0;
                    end
                    5'h8: begin
                        p_rdata <= p_countValue;
                        p_rresp <= 2'b0;
                    end
                    5'hC: begin
                        p_rdata <= {16'b0, p_prescaleValue};
                        p_rresp <= 2'b0;
                    end
                    5'h10: begin
                        p_rdata <= {31'b0, p_statusExpired};
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

    logic [15:0] p_preCnt;  // Prescaler counter
    logic p_running;  // Counter is armed; cleared by a one-shot expiry

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_preCnt <= 16'b0;
            p_countValue <= 32'b0;
            p_running <= 1'b1;
            p_statusExpiredSet <= 1'b0;
        end else begin
            p_statusExpiredSet <= 1'b0;
            if (!p_ctrlEnable) begin
                p_preCnt <= 16'b0;
                p_countValue <= p_reloadValue;
                p_running <= 1'b1;
            end else begin
                if (p_running) begin
                    if (p_preCnt == p_prescaleValue) begin
                        p_preCnt <= 16'b0;
                        if (p_countValue == 32'b0) begin
                            p_statusExpiredSet <= 1'b1;
                            if (p_ctrlAutoReload) begin
                                p_countValue <= p_reloadValue;
                            end else begin
                                p_running <= 1'b0;
                            end
                        end else begin
                            p_countValue <= p_countValue - 32'b1;
                        end
                    end else begin
                        p_preCnt <= p_preCnt + 16'b1;
                    end
                end
            end
        end
    end

    assign p_irq = p_statusExpired && p_ctrlIrqEnable;

endmodule
