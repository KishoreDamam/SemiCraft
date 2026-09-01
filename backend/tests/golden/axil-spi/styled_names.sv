// SemiCraft v0.4.0
// Snippet: axil_spi (config hash: bea2ab0054b1)
// AXI4-Lite SPI master, mode 00
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_spi (
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
    input  logic        p_miso,       // Serial input from the slave
    output logic        p_sclk,       // Serial clock, idles 0
    output logic        p_mosi,       // Serial output to the slave, MSB first
    output logic        p_csN         // Chip select, active low, driven by CTRL.cs_assert
);

    logic p_statusBusy;  // STATUS.busy (RO) — sampled on read
    logic p_statusRxValid;  // STATUS.rx_valid (W1C) — current value
    logic p_statusRxValidSet;  // STATUS.rx_valid (W1C) — set request; a set beats a same-cycle clear
    logic p_ctrlCsAssert;  // CTRL.cs_assert (RW)
    logic [7:0] p_txdataData;  // TXDATA.data (WO) — reads back as 0
    logic [7:0] p_rxdataData;  // RXDATA.data (RO) — sampled on read
    logic [15:0] p_clkdivDiv;  // CLKDIV.div (RW)
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

    logic p_wrAddrStatus;  // Write address selects STATUS

    assign p_wrAddrStatus = p_wrExec && (p_awaddrQ == 5'h0);

    logic p_wrAddrCtrl;  // Write address selects CTRL

    assign p_wrAddrCtrl = p_wrExec && (p_awaddrQ == 5'h4);

    logic p_wrAddrTxdata;  // Write address selects TXDATA

    assign p_wrAddrTxdata = p_wrExec && (p_awaddrQ == 5'h8);

    logic p_wrAddrRxdata;  // Write address selects RXDATA

    assign p_wrAddrRxdata = p_wrExec && (p_awaddrQ == 5'hC);

    logic p_wrAddrClkdiv;  // Write address selects CLKDIV

    assign p_wrAddrClkdiv = p_wrExec && (p_awaddrQ == 5'h10);

    logic p_wrHit;  // The write address matched a register

    assign p_wrHit = (((p_wrAddrStatus || p_wrAddrCtrl) || p_wrAddrTxdata) || p_wrAddrRxdata) || p_wrAddrClkdiv;

    logic [31:0] p_wrRsvdMask;  // Bits the addressed register does not implement

    assign p_wrRsvdMask = ((((p_wrAddrStatus ? 32'hFFFFFFFD : 32'b0) | (p_wrAddrCtrl ? 32'hFFFFFFFE : 32'b0)) | (p_wrAddrTxdata ? 32'hFFFFFF00 : 32'b0)) | (p_wrAddrRxdata ? 32'hFFFFFFFF : 32'b0)) | (p_wrAddrClkdiv ? 32'hFFFF0000 : 32'b0);

    logic p_wrReserved;  // The write tries to set a reserved bit

    assign p_wrReserved = |((p_wdataQ & p_wmask) & p_wrRsvdMask);

    logic p_wrSelStatus;  // Write updates STATUS

    assign p_wrSelStatus = p_wrAddrStatus && (!p_wrReserved);

    logic p_wrSelCtrl;  // Write updates CTRL

    assign p_wrSelCtrl = p_wrAddrCtrl && (!p_wrReserved);

    logic p_wrSelTxdata;  // Write updates TXDATA

    assign p_wrSelTxdata = p_wrAddrTxdata && (!p_wrReserved);

    logic p_wrSelClkdiv;  // Write updates CLKDIV

    assign p_wrSelClkdiv = p_wrAddrClkdiv && (!p_wrReserved);

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_awHs <= 1'b0;
            p_wHs <= 1'b0;
            p_bvalid <= 1'b0;
            p_bresp <= 2'b0;
            p_rvalid <= 1'b0;
            p_rresp <= 2'b0;
            p_rdata <= 32'b0;
            p_statusRxValid <= 1'd0;
            p_ctrlCsAssert <= 1'd0;
            p_txdataData <= 8'd0;
            p_clkdivDiv <= 16'd2;
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
            if (p_wrSelStatus) begin
                p_statusRxValid <= (p_statusRxValid & (~(p_wdataQ[1] & p_wmask[1]))) | p_statusRxValidSet;
            end else begin
                p_statusRxValid <= p_statusRxValid | p_statusRxValidSet;
            end
            if (p_wrSelCtrl) begin
                p_ctrlCsAssert <= (p_wdataQ[0] & p_wmask[0]) | (p_ctrlCsAssert & (~p_wmask[0]));
            end
            if (p_wrSelTxdata) begin
                p_txdataData <= (p_wdataQ[7:0] & p_wmask[7:0]) | (p_txdataData & (~p_wmask[7:0]));
            end
            if (p_wrSelClkdiv) begin
                p_clkdivDiv <= (p_wdataQ[15:0] & p_wmask[15:0]) | (p_clkdivDiv & (~p_wmask[15:0]));
            end
            if (p_arvalid && p_arready) begin
                p_rvalid <= 1'b1;
                case (p_araddr)
                    5'h0: begin
                        p_rdata <= {30'b0, p_statusRxValid, p_statusBusy};
                        p_rresp <= 2'b0;
                    end
                    5'h4: begin
                        p_rdata <= {31'b0, p_ctrlCsAssert};
                        p_rresp <= 2'b0;
                    end
                    5'h8: begin
                        p_rdata <= {24'b0, 8'b0};
                        p_rresp <= 2'b0;
                    end
                    5'hC: begin
                        p_rdata <= {24'b0, p_rxdataData};
                        p_rresp <= 2'b0;
                    end
                    5'h10: begin
                        p_rdata <= {16'b0, p_clkdivDiv};
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

    logic p_misoSync0;  // miso synchroniser stage 0
    logic p_misoSync1;  // miso synchroniser stage 1
    logic p_spiActive;  // An exchange is in progress
    logic p_spiGo;  // TXDATA write strobe, delayed one cycle
    logic p_sclkInt;  // Clock before the CPOL inversion; idles low
    logic [15:0] p_halfCnt;  // aclk cycles within one sclk half period
    logic [4:0] p_edgeCnt;  // sclk edges so far, 0..15
    logic [7:0] p_txShift;  // Transmit shift register, empties from the MSB
    logic [7:0] p_rxShift;  // Receive shift register, fills from the LSB

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_spiActive <= 1'b0;
            p_spiGo <= 1'b0;
            p_sclkInt <= 1'b0;
            p_mosi <= 1'b0;
            p_halfCnt <= 16'b0;
            p_edgeCnt <= 5'b0;
            p_txShift <= 8'b0;
            p_rxShift <= 8'b0;
            p_rxdataData <= 8'b0;
            p_statusRxValidSet <= 1'b0;
            p_misoSync0 <= 1'b0;
            p_misoSync1 <= 1'b0;
        end else begin
            p_statusRxValidSet <= 1'b0;
            p_misoSync0 <= p_miso;
            p_misoSync1 <= p_misoSync0;
            p_spiGo <= p_wrSelTxdata;
            if (!p_spiActive) begin
                if (p_spiGo) begin
                    p_spiActive <= 1'b1;
                    p_halfCnt <= 16'b0;
                    p_edgeCnt <= 5'b0;
                    p_rxShift <= 8'b0;
                    p_mosi <= p_txdataData[7];
                    p_txShift <= {p_txdataData[6:0], 1'b0};
                end
            end else begin
                if (p_halfCnt == (p_clkdivDiv - 16'b1)) begin
                    p_halfCnt <= 16'b0;
                    p_sclkInt <= !p_sclkInt;
                    if (p_edgeCnt == 5'd15) begin
                        p_spiActive <= 1'b0;
                        p_rxdataData <= p_rxShift;
                        p_statusRxValidSet <= 1'b1;
                    end else begin
                        if (p_edgeCnt[0] == 1'b0) begin
                            p_rxShift <= {p_rxShift[6:0], p_misoSync1};
                        end else begin
                            p_mosi <= p_txShift[7];
                            p_txShift <= {p_txShift[6:0], 1'b0};
                        end
                        p_edgeCnt <= p_edgeCnt + 5'b1;
                    end
                end else begin
                    p_halfCnt <= p_halfCnt + 16'b1;
                end
            end
        end
    end

    assign p_statusBusy = p_spiActive;

    assign p_csN = !p_ctrlCsAssert;

    assign p_sclk = p_sclkInt;

endmodule
