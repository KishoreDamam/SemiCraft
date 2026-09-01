// SemiCraft v0.4.0
// Snippet: axil_i2c (config hash: 0023434d01dd)
// AXI4-Lite I2C master, quarter-period divisor 2
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_i2c (
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
    input  logic        p_sclIn,      // Level sensed on SCL (low while a slave stretches)
    input  logic        p_sdaIn,      // Level sensed on SDA
    output logic        p_sclOe,      // Pull SCL low; the line is never driven high
    output logic        p_sdaOe       // Pull SDA low; the line is never driven high
);

    logic p_statusBusy;  // STATUS.busy (RO) — sampled on read
    logic p_statusDone;  // STATUS.done (W1C) — current value
    logic p_statusDoneSet;  // STATUS.done (W1C) — set request; a set beats a same-cycle clear
    logic p_statusAckErr;  // STATUS.ack_err (W1C) — current value
    logic p_statusAckErrSet;  // STATUS.ack_err (W1C) — set request; a set beats a same-cycle clear
    logic p_statusRxValid;  // STATUS.rx_valid (W1C) — current value
    logic p_statusRxValidSet;  // STATUS.rx_valid (W1C) — set request; a set beats a same-cycle clear
    logic p_cmdStart;  // CMD.start (WO) — reads back as 0
    logic p_cmdWrite;  // CMD.write (WO) — reads back as 0
    logic p_cmdRead;  // CMD.read (WO) — reads back as 0
    logic p_cmdAck;  // CMD.ack (WO) — reads back as 0
    logic p_cmdStop;  // CMD.stop (WO) — reads back as 0
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

    logic p_wrAddrCmd;  // Write address selects CMD

    assign p_wrAddrCmd = p_wrExec && (p_awaddrQ == 5'h4);

    logic p_wrAddrTxdata;  // Write address selects TXDATA

    assign p_wrAddrTxdata = p_wrExec && (p_awaddrQ == 5'h8);

    logic p_wrAddrRxdata;  // Write address selects RXDATA

    assign p_wrAddrRxdata = p_wrExec && (p_awaddrQ == 5'hC);

    logic p_wrAddrClkdiv;  // Write address selects CLKDIV

    assign p_wrAddrClkdiv = p_wrExec && (p_awaddrQ == 5'h10);

    logic p_wrHit;  // The write address matched a register

    assign p_wrHit = (((p_wrAddrStatus || p_wrAddrCmd) || p_wrAddrTxdata) || p_wrAddrRxdata) || p_wrAddrClkdiv;

    logic [31:0] p_wrRsvdMask;  // Bits the addressed register does not implement

    assign p_wrRsvdMask = ((((p_wrAddrStatus ? 32'hFFFFFFF1 : 32'b0) | (p_wrAddrCmd ? 32'hFFFFFFE0 : 32'b0)) | (p_wrAddrTxdata ? 32'hFFFFFF00 : 32'b0)) | (p_wrAddrRxdata ? 32'hFFFFFFFF : 32'b0)) | (p_wrAddrClkdiv ? 32'hFFFF0000 : 32'b0);

    logic p_wrReserved;  // The write tries to set a reserved bit

    assign p_wrReserved = |((p_wdataQ & p_wmask) & p_wrRsvdMask);

    logic p_wrSelStatus;  // Write updates STATUS

    assign p_wrSelStatus = p_wrAddrStatus && (!p_wrReserved);

    logic p_wrSelCmd;  // Write updates CMD

    assign p_wrSelCmd = p_wrAddrCmd && (!p_wrReserved);

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
            p_statusDone <= 1'd0;
            p_statusAckErr <= 1'd0;
            p_statusRxValid <= 1'd0;
            p_cmdStart <= 1'd0;
            p_cmdWrite <= 1'd0;
            p_cmdRead <= 1'd0;
            p_cmdAck <= 1'd0;
            p_cmdStop <= 1'd0;
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
                p_statusDone <= (p_statusDone & (~(p_wdataQ[1] & p_wmask[1]))) | p_statusDoneSet;
                p_statusAckErr <= (p_statusAckErr & (~(p_wdataQ[2] & p_wmask[2]))) | p_statusAckErrSet;
                p_statusRxValid <= (p_statusRxValid & (~(p_wdataQ[3] & p_wmask[3]))) | p_statusRxValidSet;
            end else begin
                p_statusDone <= p_statusDone | p_statusDoneSet;
                p_statusAckErr <= p_statusAckErr | p_statusAckErrSet;
                p_statusRxValid <= p_statusRxValid | p_statusRxValidSet;
            end
            if (p_wrSelCmd) begin
                p_cmdStart <= (p_wdataQ[0] & p_wmask[0]) | (p_cmdStart & (~p_wmask[0]));
                p_cmdWrite <= (p_wdataQ[1] & p_wmask[1]) | (p_cmdWrite & (~p_wmask[1]));
                p_cmdRead <= (p_wdataQ[2] & p_wmask[2]) | (p_cmdRead & (~p_wmask[2]));
                p_cmdAck <= (p_wdataQ[3] & p_wmask[3]) | (p_cmdAck & (~p_wmask[3]));
                p_cmdStop <= (p_wdataQ[4] & p_wmask[4]) | (p_cmdStop & (~p_wmask[4]));
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
                        p_rdata <= {28'b0, p_statusRxValid, p_statusAckErr, p_statusDone, p_statusBusy};
                        p_rresp <= 2'b0;
                    end
                    5'h4: begin
                        p_rdata <= {27'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
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

    logic p_sclSync0;  // SCL synchroniser
    logic p_sclSync1;  // SCL synchroniser
    logic p_sdaSync0;  // SDA synchroniser
    logic p_sdaSync1;  // SDA synchroniser
    logic [2:0] p_state;  // 0 IDLE, 1 START, 2 BIT, 3 ACK, 4 STOP, 5 DONE
    logic [1:0] p_phase;  // Quarter of the bit period, 0..3
    logic [15:0] p_qCnt;  // aclk cycles within one quarter
    logic [2:0] p_bitCnt;  // Bits transferred so far
    logic [7:0] p_txShift;  // Outgoing byte, empties from the MSB
    logic [7:0] p_rxShift;  // Incoming byte, fills from the LSB
    logic p_cmdGo;  // CMD write strobe, delayed one cycle
    logic p_sclSensed;  // Synchronised SCL
    logic p_sdaSensed;  // Synchronised SDA

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_state <= 3'b0;
            p_phase <= 2'b0;
            p_qCnt <= 16'b0;
            p_bitCnt <= 3'b0;
            p_txShift <= 8'b0;
            p_rxShift <= 8'b0;
            p_cmdGo <= 1'b0;
            p_rxdataData <= 8'b0;
            p_statusDoneSet <= 1'b0;
            p_statusAckErrSet <= 1'b0;
            p_statusRxValidSet <= 1'b0;
            p_sclSync0 <= 1'b1;
            p_sclSync1 <= 1'b1;
            p_sdaSync0 <= 1'b1;
            p_sdaSync1 <= 1'b1;
        end else begin
            p_statusDoneSet <= 1'b0;
            p_statusAckErrSet <= 1'b0;
            p_statusRxValidSet <= 1'b0;
            p_sclSync0 <= p_sclIn;
            p_sclSync1 <= p_sclSync0;
            p_sdaSync0 <= p_sdaIn;
            p_sdaSync1 <= p_sdaSync0;
            p_cmdGo <= p_wrSelCmd;
            if (p_state == 3'b0) begin
                if (p_cmdGo) begin
                    p_qCnt <= 16'b0;
                    p_phase <= 2'b0;
                    p_bitCnt <= 3'b0;
                    p_rxShift <= 8'b0;
                    p_txShift <= p_txdataData;
                    p_state <= p_cmdStart ? 3'b1 : ((p_cmdWrite || p_cmdRead) ? 3'b10 : (p_cmdStop ? 3'b100 : 3'b101));
                end
            end else begin
                if (p_state == 3'b101) begin
                    p_state <= 3'b0;
                    p_statusDoneSet <= 1'b1;
                    if (p_cmdRead) begin
                        p_rxdataData <= p_rxShift;
                        p_statusRxValidSet <= 1'b1;
                    end
                end else begin
                    if ((p_qCnt == (p_clkdivDiv - 16'b1)) && ((!(p_phase == 2'b10)) || p_sclSensed)) begin
                        p_qCnt <= 16'b0;
                        if (p_phase == 2'b10) begin
                            if ((p_state == 3'b10) && p_cmdRead) begin
                                p_rxShift <= {p_rxShift[6:0], p_sdaSensed};
                            end
                            if ((p_state == 3'b11) && p_cmdWrite) begin
                                p_statusAckErrSet <= p_sdaSensed;
                            end
                        end
                        if (p_phase == 2'b11) begin
                            p_phase <= 2'b0;
                            if (p_state == 3'b1) begin
                                p_state <= (p_cmdWrite || p_cmdRead) ? 3'b10 : (p_cmdStop ? 3'b100 : 3'b101);
                            end else begin
                                if (p_state == 3'b10) begin
                                    p_state <= (p_bitCnt == 3'd7) ? 3'b11 : 3'b10;
                                    p_bitCnt <= p_bitCnt + 3'b1;
                                    p_txShift <= {p_txShift[6:0], 1'b0};
                                end else begin
                                    if (p_state == 3'b11) begin
                                        p_state <= p_cmdStop ? 3'b100 : 3'b101;
                                    end else begin
                                        p_state <= 3'b101;
                                    end
                                end
                            end
                        end else begin
                            p_phase <= p_phase + 2'b1;
                        end
                    end else begin
                        if (!(p_qCnt == (p_clkdivDiv - 16'b1))) begin
                            p_qCnt <= p_qCnt + 16'b1;
                        end
                    end
                end
            end
        end
    end

    assign p_sclSensed = p_sclSync1;

    assign p_sdaSensed = p_sdaSync1;

    assign p_statusBusy = !(p_state == 3'b0);

    assign p_sclOe = ((p_state == 3'b10) || (p_state == 3'b11)) ? ((p_phase == 2'b0) || (p_phase == 2'b11)) : ((p_state == 3'b1) ? (p_phase == 2'b11) : ((p_state == 3'b100) ? (p_phase == 2'b0) : 1'b0));

    assign p_sdaOe = (p_state == 3'b1) ? ((p_phase == 2'b10) || (p_phase == 2'b11)) : ((p_state == 3'b10) ? (p_cmdWrite ? (!p_txShift[7]) : 1'b0) : ((p_state == 3'b11) ? (p_cmdWrite ? 1'b0 : p_cmdAck) : ((p_state == 3'b100) ? (!(p_phase == 2'b11)) : 1'b0)));

endmodule
