// SemiCraft v0.4.0
// Snippet: axil_uart (config hash: 46430409e63b)
// AXI4-Lite UART, 8N1, reset divisor 4
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_uart (
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
    input  logic        p_uartRx,     // Serial input, asynchronous; idles high
    output logic        p_uartTx      // Serial output; idles high
);

    logic p_statusTxBusy;  // STATUS.tx_busy (RO) — sampled on read
    logic p_statusRxValid;  // STATUS.rx_valid (W1C) — current value
    logic p_statusRxValidSet;  // STATUS.rx_valid (W1C) — set request; a set beats a same-cycle clear
    logic p_statusRxOverrun;  // STATUS.rx_overrun (W1C) — current value
    logic p_statusRxOverrunSet;  // STATUS.rx_overrun (W1C) — set request; a set beats a same-cycle clear
    logic p_statusFrameError;  // STATUS.frame_error (W1C) — current value
    logic p_statusFrameErrorSet;  // STATUS.frame_error (W1C) — set request; a set beats a same-cycle clear
    logic [7:0] p_txdataData;  // TXDATA.data (WO) — reads back as 0
    logic [7:0] p_rxdataData;  // RXDATA.data (RO) — sampled on read
    logic [15:0] p_bauddivDiv;  // BAUDDIV.div (RW)
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

    logic p_wrAddrStatus;  // Write address selects STATUS

    assign p_wrAddrStatus = p_wrExec && (p_awaddrQ == 4'h0);

    logic p_wrAddrTxdata;  // Write address selects TXDATA

    assign p_wrAddrTxdata = p_wrExec && (p_awaddrQ == 4'h4);

    logic p_wrAddrRxdata;  // Write address selects RXDATA

    assign p_wrAddrRxdata = p_wrExec && (p_awaddrQ == 4'h8);

    logic p_wrAddrBauddiv;  // Write address selects BAUDDIV

    assign p_wrAddrBauddiv = p_wrExec && (p_awaddrQ == 4'hC);

    logic p_wrHit;  // The write address matched a register

    assign p_wrHit = ((p_wrAddrStatus || p_wrAddrTxdata) || p_wrAddrRxdata) || p_wrAddrBauddiv;

    logic [31:0] p_wrRsvdMask;  // Bits the addressed register does not implement

    assign p_wrRsvdMask = (((p_wrAddrStatus ? 32'hFFFFFFF1 : 32'b0) | (p_wrAddrTxdata ? 32'hFFFFFF00 : 32'b0)) | (p_wrAddrRxdata ? 32'hFFFFFFFF : 32'b0)) | (p_wrAddrBauddiv ? 32'hFFFF0000 : 32'b0);

    logic p_wrReserved;  // The write tries to set a reserved bit

    assign p_wrReserved = |((p_wdataQ & p_wmask) & p_wrRsvdMask);

    logic p_wrSelStatus;  // Write updates STATUS

    assign p_wrSelStatus = p_wrAddrStatus && (!p_wrReserved);

    logic p_wrSelTxdata;  // Write updates TXDATA

    assign p_wrSelTxdata = p_wrAddrTxdata && (!p_wrReserved);

    logic p_wrSelBauddiv;  // Write updates BAUDDIV

    assign p_wrSelBauddiv = p_wrAddrBauddiv && (!p_wrReserved);

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
            p_statusRxOverrun <= 1'd0;
            p_statusFrameError <= 1'd0;
            p_txdataData <= 8'd0;
            p_bauddivDiv <= 16'd4;
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
                p_statusRxOverrun <= (p_statusRxOverrun & (~(p_wdataQ[2] & p_wmask[2]))) | p_statusRxOverrunSet;
                p_statusFrameError <= (p_statusFrameError & (~(p_wdataQ[3] & p_wmask[3]))) | p_statusFrameErrorSet;
            end else begin
                p_statusRxValid <= p_statusRxValid | p_statusRxValidSet;
                p_statusRxOverrun <= p_statusRxOverrun | p_statusRxOverrunSet;
                p_statusFrameError <= p_statusFrameError | p_statusFrameErrorSet;
            end
            if (p_wrSelTxdata) begin
                p_txdataData <= (p_wdataQ[7:0] & p_wmask[7:0]) | (p_txdataData & (~p_wmask[7:0]));
            end
            if (p_wrSelBauddiv) begin
                p_bauddivDiv <= (p_wdataQ[15:0] & p_wmask[15:0]) | (p_bauddivDiv & (~p_wmask[15:0]));
            end
            if (p_arvalid && p_arready) begin
                p_rvalid <= 1'b1;
                case (p_araddr)
                    4'h0: begin
                        p_rdata <= {28'b0, p_statusFrameError, p_statusRxOverrun, p_statusRxValid, p_statusTxBusy};
                        p_rresp <= 2'b0;
                    end
                    4'h4: begin
                        p_rdata <= {24'b0, 8'b0};
                        p_rresp <= 2'b0;
                    end
                    4'h8: begin
                        p_rdata <= {24'b0, p_rxdataData};
                        p_rresp <= 2'b0;
                    end
                    4'hC: begin
                        p_rdata <= {16'b0, p_bauddivDiv};
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

    logic p_rxSync0;  // rx synchroniser stage 0
    logic p_rxSync1;  // rx synchroniser stage 1
    logic [1:0] p_txState;  // Transmit FSM: 0 IDLE, 1 START, 2 DATA, 3 STOP
    logic [15:0] p_txCnt;  // Transmit baud counter
    logic [7:0] p_txShift;  // Transmit shift register, empties LSB first
    logic [2:0] p_txBit;  // Transmit bit index
    logic p_txGo;  // TXDATA write strobe, delayed one cycle
    logic [1:0] p_rxState;  // Receive FSM: 0 IDLE, 1 START, 2 DATA, 3 STOP
    logic [15:0] p_rxCnt;  // Receive baud counter
    logic [7:0] p_rxShift;  // Receive shift register, fills from the MSB
    logic [2:0] p_rxBit;  // Receive bit index

    always_ff @(posedge p_aclk) begin
        if (!p_areset_n) begin
            p_uartTx <= 1'b1;
            p_rxSync0 <= 1'b1;
            p_rxSync1 <= 1'b1;
            p_txState <= 2'b0;
            p_txCnt <= 16'b0;
            p_txShift <= 8'b0;
            p_txBit <= 3'b0;
            p_txGo <= 1'b0;
            p_rxState <= 2'b0;
            p_rxCnt <= 16'b0;
            p_rxShift <= 8'b0;
            p_rxBit <= 3'b0;
            p_rxdataData <= 8'b0;
            p_statusRxValidSet <= 1'b0;
            p_statusRxOverrunSet <= 1'b0;
            p_statusFrameErrorSet <= 1'b0;
        end else begin
            p_statusRxValidSet <= 1'b0;
            p_statusRxOverrunSet <= 1'b0;
            p_statusFrameErrorSet <= 1'b0;
            p_rxSync0 <= p_uartRx;
            p_rxSync1 <= p_rxSync0;
            p_txGo <= p_wrSelTxdata;
            case (p_txState)
                2'b0: begin
                    p_uartTx <= 1'b1;
                    if (p_txGo) begin
                        p_txState <= 2'b1;
                        p_txCnt <= 16'b0;
                        p_txShift <= p_txdataData;
                        p_txBit <= 3'b0;
                        p_uartTx <= 1'b0;
                    end
                end
                2'b1: begin
                    if (p_txCnt == (p_bauddivDiv - 16'b1)) begin
                        p_txCnt <= 16'b0;
                    end else begin
                        p_txCnt <= p_txCnt + 16'b1;
                    end
                    if (p_txCnt == (p_bauddivDiv - 16'b1)) begin
                        p_txState <= 2'b10;
                        p_uartTx <= p_txShift[0];
                        p_txShift <= {1'b0, p_txShift[7:1]};
                    end
                end
                2'b10: begin
                    if (p_txCnt == (p_bauddivDiv - 16'b1)) begin
                        p_txCnt <= 16'b0;
                    end else begin
                        p_txCnt <= p_txCnt + 16'b1;
                    end
                    if (p_txCnt == (p_bauddivDiv - 16'b1)) begin
                        if (p_txBit == 3'd7) begin
                            p_txState <= 2'b11;
                            p_uartTx <= 1'b1;
                        end else begin
                            p_txBit <= p_txBit + 3'b1;
                            p_uartTx <= p_txShift[0];
                            p_txShift <= {1'b0, p_txShift[7:1]};
                        end
                    end
                end
                2'b11: begin
                    if (p_txCnt == (p_bauddivDiv - 16'b1)) begin
                        p_txCnt <= 16'b0;
                    end else begin
                        p_txCnt <= p_txCnt + 16'b1;
                    end
                    if (p_txCnt == (p_bauddivDiv - 16'b1)) begin
                        p_txState <= 2'b0;
                    end
                end
                default: p_txState <= 2'b0;
            endcase
            case (p_rxState)
                2'b0: begin
                    if (!p_rxSync1) begin
                        p_rxState <= 2'b1;
                        p_rxCnt <= 16'b0;
                    end
                end
                2'b1: begin
                    if (p_rxCnt == ((p_bauddivDiv >> 1'b1) - 16'b1)) begin
                        p_rxCnt <= 16'b0;
                    end else begin
                        p_rxCnt <= p_rxCnt + 16'b1;
                    end
                    if (p_rxCnt == ((p_bauddivDiv >> 1'b1) - 16'b1)) begin
                        if (p_rxSync1) begin
                            p_rxState <= 2'b0;
                        end else begin
                            p_rxState <= 2'b10;
                            p_rxBit <= 3'b0;
                        end
                    end
                end
                2'b10: begin
                    if (p_rxCnt == (p_bauddivDiv - 16'b1)) begin
                        p_rxCnt <= 16'b0;
                    end else begin
                        p_rxCnt <= p_rxCnt + 16'b1;
                    end
                    if (p_rxCnt == (p_bauddivDiv - 16'b1)) begin
                        p_rxShift <= {p_rxSync1, p_rxShift[7:1]};
                        if (p_rxBit == 3'd7) begin
                            p_rxState <= 2'b11;
                        end else begin
                            p_rxBit <= p_rxBit + 3'b1;
                        end
                    end
                end
                2'b11: begin
                    if (p_rxCnt == (p_bauddivDiv - 16'b1)) begin
                        p_rxCnt <= 16'b0;
                    end else begin
                        p_rxCnt <= p_rxCnt + 16'b1;
                    end
                    if (p_rxCnt == (p_bauddivDiv - 16'b1)) begin
                        p_rxState <= 2'b0;
                        p_rxdataData <= p_rxShift;
                        p_statusRxValidSet <= 1'b1;
                        p_statusRxOverrunSet <= p_statusRxValid;
                        p_statusFrameErrorSet <= !p_rxSync1;
                    end
                end
                default: p_rxState <= 2'b0;
            endcase
        end
    end

    assign p_statusTxBusy = p_txState != 2'b0;

endmodule
