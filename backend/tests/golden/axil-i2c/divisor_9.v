// SemiCraft v0.3.0
// Snippet: axil_i2c (config hash: 932323353f5c)
// AXI4-Lite I2C master, quarter-period divisor 9
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_i2c (
    input  wire        aclk,       // AXI clock; everything is synchronous to it
    input  wire        areset_n,   // AXI reset, active-low (spec: ARESETn)
    input  wire [4:0]  awaddr,     // Write address (byte address)
    input  wire        awvalid,    // Write address valid
    output wire        awready,    // Write address ready
    input  wire [31:0] wdata,      // Write data
    input  wire [3:0]  wstrb,      // Write byte strobes, one bit per byte
    input  wire        wvalid,     // Write data valid
    output wire        wready,     // Write data ready
    output reg  [1:0]  bresp,      // Write response: OKAY, or SLVERR if unmapped
    output reg         bvalid,     // Write response valid
    input  wire        bready,     // Write response ready
    input  wire [4:0]  araddr,     // Read address (byte address)
    input  wire        arvalid,    // Read address valid
    output wire        arready,    // Read address ready
    output reg  [31:0] rdata,      // Read data
    output reg  [1:0]  rresp,      // Read response: OKAY, or SLVERR if unmapped
    output reg         rvalid,     // Read data valid
    input  wire        rready,     // Read data ready
    input  wire        scl_in,     // Level sensed on SCL (low while a slave stretches)
    input  wire        sda_in,     // Level sensed on SDA
    output wire        scl_oe,     // Pull SCL low; the line is never driven high
    output wire        sda_oe      // Pull SDA low; the line is never driven high
);

    wire status_busy;  // STATUS.busy (RO) — sampled on read
    reg status_done;  // STATUS.done (W1C) — current value
    reg status_done_set;  // STATUS.done (W1C) — set request; a set beats a same-cycle clear
    reg status_ack_err;  // STATUS.ack_err (W1C) — current value
    reg status_ack_err_set;  // STATUS.ack_err (W1C) — set request; a set beats a same-cycle clear
    reg status_rx_valid;  // STATUS.rx_valid (W1C) — current value
    reg status_rx_valid_set;  // STATUS.rx_valid (W1C) — set request; a set beats a same-cycle clear
    reg cmd_start;  // CMD.start (WO) — reads back as 0
    reg cmd_write;  // CMD.write (WO) — reads back as 0
    reg cmd_read;  // CMD.read (WO) — reads back as 0
    reg cmd_ack;  // CMD.ack (WO) — reads back as 0
    reg cmd_stop;  // CMD.stop (WO) — reads back as 0
    reg [7:0] txdata_data;  // TXDATA.data (WO) — reads back as 0
    reg [7:0] rxdata_data;  // RXDATA.data (RO) — sampled on read
    reg [15:0] clkdiv_div;  // CLKDIV.div (RW)
    reg aw_hs;  // Write address captured, awaiting the data beat
    reg w_hs;  // Write data captured, awaiting the address beat
    reg [4:0] awaddr_q;  // Captured write address
    reg [31:0] wdata_q;  // Captured write data
    reg [3:0] wstrb_q;  // Captured write byte strobes
    wire [31:0] wmask;  // Captured strobes expanded to a bit mask

    assign awready = (!aw_hs) && (!bvalid);

    assign wready = (!w_hs) && (!bvalid);

    assign arready = !rvalid;

    assign wmask = {{8{wstrb_q[3]}}, {8{wstrb_q[2]}}, {8{wstrb_q[1]}}, {8{wstrb_q[0]}}};

    wire wr_exec;  // Both write channels captured and no response pending

    assign wr_exec = (aw_hs && w_hs) && (!bvalid);

    wire wr_addr_status;  // Write address selects STATUS

    assign wr_addr_status = wr_exec && (awaddr_q == 5'h0);

    wire wr_addr_cmd;  // Write address selects CMD

    assign wr_addr_cmd = wr_exec && (awaddr_q == 5'h4);

    wire wr_addr_txdata;  // Write address selects TXDATA

    assign wr_addr_txdata = wr_exec && (awaddr_q == 5'h8);

    wire wr_addr_rxdata;  // Write address selects RXDATA

    assign wr_addr_rxdata = wr_exec && (awaddr_q == 5'hC);

    wire wr_addr_clkdiv;  // Write address selects CLKDIV

    assign wr_addr_clkdiv = wr_exec && (awaddr_q == 5'h10);

    wire wr_hit;  // The write address matched a register

    assign wr_hit = (((wr_addr_status || wr_addr_cmd) || wr_addr_txdata) || wr_addr_rxdata) || wr_addr_clkdiv;

    wire [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = ((((wr_addr_status ? 32'hFFFFFFF1 : 32'b0) | (wr_addr_cmd ? 32'hFFFFFFE0 : 32'b0)) | (wr_addr_txdata ? 32'hFFFFFF00 : 32'b0)) | (wr_addr_rxdata ? 32'hFFFFFFFF : 32'b0)) | (wr_addr_clkdiv ? 32'hFFFF0000 : 32'b0);

    wire wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    wire wr_sel_status;  // Write updates STATUS

    assign wr_sel_status = wr_addr_status && (!wr_reserved);

    wire wr_sel_cmd;  // Write updates CMD

    assign wr_sel_cmd = wr_addr_cmd && (!wr_reserved);

    wire wr_sel_txdata;  // Write updates TXDATA

    assign wr_sel_txdata = wr_addr_txdata && (!wr_reserved);

    wire wr_sel_clkdiv;  // Write updates CLKDIV

    assign wr_sel_clkdiv = wr_addr_clkdiv && (!wr_reserved);

    always @(posedge aclk) begin
        if (!areset_n) begin
            aw_hs <= 1'b0;
            w_hs <= 1'b0;
            bvalid <= 1'b0;
            bresp <= 2'b0;
            rvalid <= 1'b0;
            rresp <= 2'b0;
            rdata <= 32'b0;
            status_done <= 1'd0;
            status_ack_err <= 1'd0;
            status_rx_valid <= 1'd0;
            cmd_start <= 1'd0;
            cmd_write <= 1'd0;
            cmd_read <= 1'd0;
            cmd_ack <= 1'd0;
            cmd_stop <= 1'd0;
            txdata_data <= 8'd0;
            clkdiv_div <= 16'd9;
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
                status_done <= (status_done & (~(wdata_q[1] & wmask[1]))) | status_done_set;
                status_ack_err <= (status_ack_err & (~(wdata_q[2] & wmask[2]))) | status_ack_err_set;
                status_rx_valid <= (status_rx_valid & (~(wdata_q[3] & wmask[3]))) | status_rx_valid_set;
            end else begin
                status_done <= status_done | status_done_set;
                status_ack_err <= status_ack_err | status_ack_err_set;
                status_rx_valid <= status_rx_valid | status_rx_valid_set;
            end
            if (wr_sel_cmd) begin
                cmd_start <= (wdata_q[0] & wmask[0]) | (cmd_start & (~wmask[0]));
                cmd_write <= (wdata_q[1] & wmask[1]) | (cmd_write & (~wmask[1]));
                cmd_read <= (wdata_q[2] & wmask[2]) | (cmd_read & (~wmask[2]));
                cmd_ack <= (wdata_q[3] & wmask[3]) | (cmd_ack & (~wmask[3]));
                cmd_stop <= (wdata_q[4] & wmask[4]) | (cmd_stop & (~wmask[4]));
            end
            if (wr_sel_txdata) begin
                txdata_data <= (wdata_q[7:0] & wmask[7:0]) | (txdata_data & (~wmask[7:0]));
            end
            if (wr_sel_clkdiv) begin
                clkdiv_div <= (wdata_q[15:0] & wmask[15:0]) | (clkdiv_div & (~wmask[15:0]));
            end
            if (arvalid && arready) begin
                rvalid <= 1'b1;
                case (araddr)
                    5'h0: begin
                        rdata <= {28'b0, status_rx_valid, status_ack_err, status_done, status_busy};
                        rresp <= 2'b0;
                    end
                    5'h4: begin
                        rdata <= {27'b0, 1'b0, 1'b0, 1'b0, 1'b0, 1'b0};
                        rresp <= 2'b0;
                    end
                    5'h8: begin
                        rdata <= {24'b0, 8'b0};
                        rresp <= 2'b0;
                    end
                    5'hC: begin
                        rdata <= {24'b0, rxdata_data};
                        rresp <= 2'b0;
                    end
                    5'h10: begin
                        rdata <= {16'b0, clkdiv_div};
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

    reg scl_sync0;  // SCL synchroniser
    reg scl_sync1;  // SCL synchroniser
    reg sda_sync0;  // SDA synchroniser
    reg sda_sync1;  // SDA synchroniser
    reg [2:0] state;  // 0 IDLE, 1 START, 2 BIT, 3 ACK, 4 STOP, 5 DONE
    reg [1:0] phase;  // Quarter of the bit period, 0..3
    reg [15:0] q_cnt;  // aclk cycles within one quarter
    reg [2:0] bit_cnt;  // Bits transferred so far
    reg [7:0] tx_shift;  // Outgoing byte, empties from the MSB
    reg [7:0] rx_shift;  // Incoming byte, fills from the LSB
    reg cmd_go;  // CMD write strobe, delayed one cycle
    wire scl_sensed;  // Synchronised SCL
    wire sda_sensed;  // Synchronised SDA

    always @(posedge aclk) begin
        if (!areset_n) begin
            state <= 3'b0;
            phase <= 2'b0;
            q_cnt <= 16'b0;
            bit_cnt <= 3'b0;
            tx_shift <= 8'b0;
            rx_shift <= 8'b0;
            cmd_go <= 1'b0;
            rxdata_data <= 8'b0;
            status_done_set <= 1'b0;
            status_ack_err_set <= 1'b0;
            status_rx_valid_set <= 1'b0;
            scl_sync0 <= 1'b1;
            scl_sync1 <= 1'b1;
            sda_sync0 <= 1'b1;
            sda_sync1 <= 1'b1;
        end else begin
            status_done_set <= 1'b0;
            status_ack_err_set <= 1'b0;
            status_rx_valid_set <= 1'b0;
            scl_sync0 <= scl_in;
            scl_sync1 <= scl_sync0;
            sda_sync0 <= sda_in;
            sda_sync1 <= sda_sync0;
            cmd_go <= wr_sel_cmd;
            if (state == 3'b0) begin
                if (cmd_go) begin
                    q_cnt <= 16'b0;
                    phase <= 2'b0;
                    bit_cnt <= 3'b0;
                    rx_shift <= 8'b0;
                    tx_shift <= txdata_data;
                    state <= cmd_start ? 3'b1 : ((cmd_write || cmd_read) ? 3'b10 : (cmd_stop ? 3'b100 : 3'b101));
                end
            end else begin
                if (state == 3'b101) begin
                    state <= 3'b0;
                    status_done_set <= 1'b1;
                    if (cmd_read) begin
                        rxdata_data <= rx_shift;
                        status_rx_valid_set <= 1'b1;
                    end
                end else begin
                    if ((q_cnt == (clkdiv_div - 16'b1)) && ((!(phase == 2'b10)) || scl_sensed)) begin
                        q_cnt <= 16'b0;
                        if (phase == 2'b10) begin
                            if ((state == 3'b10) && cmd_read) begin
                                rx_shift <= {rx_shift[6:0], sda_sensed};
                            end
                            if ((state == 3'b11) && cmd_write) begin
                                status_ack_err_set <= sda_sensed;
                            end
                        end
                        if (phase == 2'b11) begin
                            phase <= 2'b0;
                            if (state == 3'b1) begin
                                state <= (cmd_write || cmd_read) ? 3'b10 : (cmd_stop ? 3'b100 : 3'b101);
                            end else begin
                                if (state == 3'b10) begin
                                    state <= (bit_cnt == 3'd7) ? 3'b11 : 3'b10;
                                    bit_cnt <= bit_cnt + 3'b1;
                                    tx_shift <= {tx_shift[6:0], 1'b0};
                                end else begin
                                    if (state == 3'b11) begin
                                        state <= cmd_stop ? 3'b100 : 3'b101;
                                    end else begin
                                        state <= 3'b101;
                                    end
                                end
                            end
                        end else begin
                            phase <= phase + 2'b1;
                        end
                    end else begin
                        if (!(q_cnt == (clkdiv_div - 16'b1))) begin
                            q_cnt <= q_cnt + 16'b1;
                        end
                    end
                end
            end
        end
    end

    assign scl_sensed = scl_sync1;

    assign sda_sensed = sda_sync1;

    assign status_busy = !(state == 3'b0);

    assign scl_oe = ((state == 3'b10) || (state == 3'b11)) ? ((phase == 2'b0) || (phase == 2'b11)) : ((state == 3'b1) ? (phase == 2'b11) : ((state == 3'b100) ? (phase == 2'b0) : 1'b0));

    assign sda_oe = (state == 3'b1) ? ((phase == 2'b10) || (phase == 2'b11)) : ((state == 3'b10) ? (cmd_write ? (!tx_shift[7]) : 1'b0) : ((state == 3'b11) ? (cmd_write ? 1'b0 : cmd_ack) : ((state == 3'b100) ? (!(phase == 2'b11)) : 1'b0)));

endmodule
