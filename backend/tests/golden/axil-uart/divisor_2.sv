// SemiCraft v0.4.0
// Snippet: axil_uart (config hash: bc1dcff66931)
// AXI4-Lite UART, 8N1, reset divisor 2
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_uart (
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
    input  logic        uart_rx,    // Serial input, asynchronous; idles high
    output logic        uart_tx     // Serial output; idles high
);

    logic status_tx_busy;  // STATUS.tx_busy (RO) — sampled on read
    logic status_rx_valid;  // STATUS.rx_valid (W1C) — current value
    logic status_rx_valid_set;  // STATUS.rx_valid (W1C) — set request; a set beats a same-cycle clear
    logic status_rx_overrun;  // STATUS.rx_overrun (W1C) — current value
    logic status_rx_overrun_set;  // STATUS.rx_overrun (W1C) — set request; a set beats a same-cycle clear
    logic status_frame_error;  // STATUS.frame_error (W1C) — current value
    logic status_frame_error_set;  // STATUS.frame_error (W1C) — set request; a set beats a same-cycle clear
    logic [7:0] txdata_data;  // TXDATA.data (WO) — reads back as 0
    logic [7:0] rxdata_data;  // RXDATA.data (RO) — sampled on read
    logic [15:0] bauddiv_div;  // BAUDDIV.div (RW)
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

    logic wr_addr_status;  // Write address selects STATUS

    assign wr_addr_status = wr_exec && (awaddr_q == 4'h0);

    logic wr_addr_txdata;  // Write address selects TXDATA

    assign wr_addr_txdata = wr_exec && (awaddr_q == 4'h4);

    logic wr_addr_rxdata;  // Write address selects RXDATA

    assign wr_addr_rxdata = wr_exec && (awaddr_q == 4'h8);

    logic wr_addr_bauddiv;  // Write address selects BAUDDIV

    assign wr_addr_bauddiv = wr_exec && (awaddr_q == 4'hC);

    logic wr_hit;  // The write address matched a register

    assign wr_hit = ((wr_addr_status || wr_addr_txdata) || wr_addr_rxdata) || wr_addr_bauddiv;

    logic [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = (((wr_addr_status ? 32'hFFFFFFF1 : 32'b0) | (wr_addr_txdata ? 32'hFFFFFF00 : 32'b0)) | (wr_addr_rxdata ? 32'hFFFFFFFF : 32'b0)) | (wr_addr_bauddiv ? 32'hFFFF0000 : 32'b0);

    logic wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    logic wr_sel_status;  // Write updates STATUS

    assign wr_sel_status = wr_addr_status && (!wr_reserved);

    logic wr_sel_txdata;  // Write updates TXDATA

    assign wr_sel_txdata = wr_addr_txdata && (!wr_reserved);

    logic wr_sel_bauddiv;  // Write updates BAUDDIV

    assign wr_sel_bauddiv = wr_addr_bauddiv && (!wr_reserved);

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            aw_hs <= 1'b0;
            w_hs <= 1'b0;
            bvalid <= 1'b0;
            bresp <= 2'b0;
            rvalid <= 1'b0;
            rresp <= 2'b0;
            rdata <= 32'b0;
            status_rx_valid <= 1'd0;
            status_rx_overrun <= 1'd0;
            status_frame_error <= 1'd0;
            txdata_data <= 8'd0;
            bauddiv_div <= 16'd2;
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
            if (wr_sel_status) begin
                status_rx_valid <= (status_rx_valid & (~(wdata_q[1] & wmask[1]))) | status_rx_valid_set;
                status_rx_overrun <= (status_rx_overrun & (~(wdata_q[2] & wmask[2]))) | status_rx_overrun_set;
                status_frame_error <= (status_frame_error & (~(wdata_q[3] & wmask[3]))) | status_frame_error_set;
            end else begin
                status_rx_valid <= status_rx_valid | status_rx_valid_set;
                status_rx_overrun <= status_rx_overrun | status_rx_overrun_set;
                status_frame_error <= status_frame_error | status_frame_error_set;
            end
            if (wr_sel_txdata) begin
                txdata_data <= (wdata_q[7:0] & wmask[7:0]) | (txdata_data & (~wmask[7:0]));
            end
            if (wr_sel_bauddiv) begin
                bauddiv_div <= (wdata_q[15:0] & wmask[15:0]) | (bauddiv_div & (~wmask[15:0]));
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    4'h0: begin
                        rdata <= {28'b0, status_frame_error, status_rx_overrun, status_rx_valid, status_tx_busy};
                        rresp <= 2'b0;
                    end
                    4'h4: begin
                        rdata <= {24'b0, 8'b0};
                        rresp <= 2'b0;
                    end
                    4'h8: begin
                        rdata <= {24'b0, rxdata_data};
                        rresp <= 2'b0;
                    end
                    4'hC: begin
                        rdata <= {16'b0, bauddiv_div};
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

    logic rx_sync0;  // rx synchroniser stage 0
    logic rx_sync1;  // rx synchroniser stage 1
    logic [1:0] tx_state;  // Transmit FSM: 0 IDLE, 1 START, 2 DATA, 3 STOP
    logic [15:0] tx_cnt;  // Transmit baud counter
    logic [7:0] tx_shift;  // Transmit shift register, empties LSB first
    logic [2:0] tx_bit;  // Transmit bit index
    logic tx_go;  // TXDATA write strobe, delayed one cycle
    logic [1:0] rx_state;  // Receive FSM: 0 IDLE, 1 START, 2 DATA, 3 STOP
    logic [15:0] rx_cnt;  // Receive baud counter
    logic [7:0] rx_shift;  // Receive shift register, fills from the MSB
    logic [2:0] rx_bit;  // Receive bit index

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            uart_tx <= 1'b1;
            rx_sync0 <= 1'b1;
            rx_sync1 <= 1'b1;
            tx_state <= 2'b0;
            tx_cnt <= 16'b0;
            tx_shift <= 8'b0;
            tx_bit <= 3'b0;
            tx_go <= 1'b0;
            rx_state <= 2'b0;
            rx_cnt <= 16'b0;
            rx_shift <= 8'b0;
            rx_bit <= 3'b0;
            rxdata_data <= 8'b0;
            status_rx_valid_set <= 1'b0;
            status_rx_overrun_set <= 1'b0;
            status_frame_error_set <= 1'b0;
        end else begin
            status_rx_valid_set <= 1'b0;
            status_rx_overrun_set <= 1'b0;
            status_frame_error_set <= 1'b0;
            rx_sync0 <= uart_rx;
            rx_sync1 <= rx_sync0;
            tx_go <= wr_sel_txdata;
            case (tx_state)
                2'b0: begin
                    uart_tx <= 1'b1;
                    if (tx_go) begin
                        tx_state <= 2'b1;
                        tx_cnt <= 16'b0;
                        tx_shift <= txdata_data;
                        tx_bit <= 3'b0;
                        uart_tx <= 1'b0;
                    end
                end
                2'b1: begin
                    if (tx_cnt == (bauddiv_div - 16'b1)) begin
                        tx_cnt <= 16'b0;
                    end else begin
                        tx_cnt <= tx_cnt + 16'b1;
                    end
                    if (tx_cnt == (bauddiv_div - 16'b1)) begin
                        tx_state <= 2'b10;
                        uart_tx <= tx_shift[0];
                        tx_shift <= {1'b0, tx_shift[7:1]};
                    end
                end
                2'b10: begin
                    if (tx_cnt == (bauddiv_div - 16'b1)) begin
                        tx_cnt <= 16'b0;
                    end else begin
                        tx_cnt <= tx_cnt + 16'b1;
                    end
                    if (tx_cnt == (bauddiv_div - 16'b1)) begin
                        if (tx_bit == 3'd7) begin
                            tx_state <= 2'b11;
                            uart_tx <= 1'b1;
                        end else begin
                            tx_bit <= tx_bit + 3'b1;
                            uart_tx <= tx_shift[0];
                            tx_shift <= {1'b0, tx_shift[7:1]};
                        end
                    end
                end
                2'b11: begin
                    if (tx_cnt == (bauddiv_div - 16'b1)) begin
                        tx_cnt <= 16'b0;
                    end else begin
                        tx_cnt <= tx_cnt + 16'b1;
                    end
                    if (tx_cnt == (bauddiv_div - 16'b1)) begin
                        tx_state <= 2'b0;
                    end
                end
                default: tx_state <= 2'b0;
            endcase
            case (rx_state)
                2'b0: begin
                    if (!rx_sync1) begin
                        rx_state <= 2'b1;
                        rx_cnt <= 16'b0;
                    end
                end
                2'b1: begin
                    if (rx_cnt == ((bauddiv_div >> 1'b1) - 16'b1)) begin
                        rx_cnt <= 16'b0;
                    end else begin
                        rx_cnt <= rx_cnt + 16'b1;
                    end
                    if (rx_cnt == ((bauddiv_div >> 1'b1) - 16'b1)) begin
                        if (rx_sync1) begin
                            rx_state <= 2'b0;
                        end else begin
                            rx_state <= 2'b10;
                            rx_bit <= 3'b0;
                        end
                    end
                end
                2'b10: begin
                    if (rx_cnt == (bauddiv_div - 16'b1)) begin
                        rx_cnt <= 16'b0;
                    end else begin
                        rx_cnt <= rx_cnt + 16'b1;
                    end
                    if (rx_cnt == (bauddiv_div - 16'b1)) begin
                        rx_shift <= {rx_sync1, rx_shift[7:1]};
                        if (rx_bit == 3'd7) begin
                            rx_state <= 2'b11;
                        end else begin
                            rx_bit <= rx_bit + 3'b1;
                        end
                    end
                end
                2'b11: begin
                    if (rx_cnt == (bauddiv_div - 16'b1)) begin
                        rx_cnt <= 16'b0;
                    end else begin
                        rx_cnt <= rx_cnt + 16'b1;
                    end
                    if (rx_cnt == (bauddiv_div - 16'b1)) begin
                        rx_state <= 2'b0;
                        rxdata_data <= rx_shift;
                        status_rx_valid_set <= 1'b1;
                        status_rx_overrun_set <= status_rx_valid;
                        status_frame_error_set <= !rx_sync1;
                    end
                end
                default: rx_state <= 2'b0;
            endcase
        end
    end

    assign status_tx_busy = tx_state != 2'b0;

endmodule
