// SemiCraft v0.3.0
// Snippet: axil_spi (config hash: fc5b9c778b84)
// AXI4-Lite SPI master, mode 00
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_spi (
    input  logic        aclk,       // AXI clock; everything is synchronous to it
    input  logic        areset_n,   // AXI reset, active-low (spec: ARESETn)
    input  logic [4:0]  awaddr,     // Write address (byte address)
    input  logic        awvalid,    // Write address valid
    output logic        awready,    // Write address ready
    input  logic [31:0] wdata,      // Write data
    input  logic [3:0]  wstrb,      // Write byte strobes, one bit per byte
    input  logic        wvalid,     // Write data valid
    output logic        wready,     // Write data ready
    output logic [1:0]  bresp,      // Write response: OKAY, or SLVERR if unmapped
    output logic        bvalid,     // Write response valid
    input  logic        bready,     // Write response ready
    input  logic [4:0]  araddr,     // Read address (byte address)
    input  logic        arvalid,    // Read address valid
    output logic        arready,    // Read address ready
    output logic [31:0] rdata,      // Read data
    output logic [1:0]  rresp,      // Read response: OKAY, or SLVERR if unmapped
    output logic        rvalid,     // Read data valid
    input  logic        rready,     // Read data ready
    input  logic        miso,       // Serial input from the slave
    output logic        sclk,       // Serial clock, idles 0
    output logic        mosi,       // Serial output to the slave, MSB first
    output logic        cs_n        // Chip select, active low, driven by CTRL.cs_assert
);

    logic status_busy;  // STATUS.busy (RO) — sampled on read
    logic status_rx_valid;  // STATUS.rx_valid (W1C) — current value
    logic status_rx_valid_set;  // STATUS.rx_valid (W1C) — set request; a set beats a same-cycle clear
    logic ctrl_cs_assert;  // CTRL.cs_assert (RW)
    logic [7:0] txdata_data;  // TXDATA.data (WO) — reads back as 0
    logic [7:0] rxdata_data;  // RXDATA.data (RO) — sampled on read
    logic [15:0] clkdiv_div;  // CLKDIV.div (RW)
    logic aw_hs;  // Write address captured, awaiting the data beat
    logic w_hs;  // Write data captured, awaiting the address beat
    logic [4:0] awaddr_q;  // Captured write address
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

    assign wr_addr_status = wr_exec && (awaddr_q == 5'h0);

    logic wr_addr_ctrl;  // Write address selects CTRL

    assign wr_addr_ctrl = wr_exec && (awaddr_q == 5'h4);

    logic wr_addr_txdata;  // Write address selects TXDATA

    assign wr_addr_txdata = wr_exec && (awaddr_q == 5'h8);

    logic wr_addr_rxdata;  // Write address selects RXDATA

    assign wr_addr_rxdata = wr_exec && (awaddr_q == 5'hC);

    logic wr_addr_clkdiv;  // Write address selects CLKDIV

    assign wr_addr_clkdiv = wr_exec && (awaddr_q == 5'h10);

    logic wr_hit;  // The write address matched a register

    assign wr_hit = (((wr_addr_status || wr_addr_ctrl) || wr_addr_txdata) || wr_addr_rxdata) || wr_addr_clkdiv;

    logic [31:0] wr_rsvd_mask;  // Bits the addressed register does not implement

    assign wr_rsvd_mask = ((((wr_addr_status ? 32'hFFFFFFFD : 32'b0) | (wr_addr_ctrl ? 32'hFFFFFFFE : 32'b0)) | (wr_addr_txdata ? 32'hFFFFFF00 : 32'b0)) | (wr_addr_rxdata ? 32'hFFFFFFFF : 32'b0)) | (wr_addr_clkdiv ? 32'hFFFF0000 : 32'b0);

    logic wr_reserved;  // The write tries to set a reserved bit

    assign wr_reserved = |((wdata_q & wmask) & wr_rsvd_mask);

    logic wr_sel_status;  // Write updates STATUS

    assign wr_sel_status = wr_addr_status && (!wr_reserved);

    logic wr_sel_ctrl;  // Write updates CTRL

    assign wr_sel_ctrl = wr_addr_ctrl && (!wr_reserved);

    logic wr_sel_txdata;  // Write updates TXDATA

    assign wr_sel_txdata = wr_addr_txdata && (!wr_reserved);

    logic wr_sel_clkdiv;  // Write updates CLKDIV

    assign wr_sel_clkdiv = wr_addr_clkdiv && (!wr_reserved);

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
            ctrl_cs_assert <= 1'd0;
            txdata_data <= 8'd0;
            clkdiv_div <= 16'd2;
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
            end else begin
                status_rx_valid <= status_rx_valid | status_rx_valid_set;
            end
            if (wr_sel_ctrl) begin
                ctrl_cs_assert <= (wdata_q[0] & wmask[0]) | (ctrl_cs_assert & (~wmask[0]));
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
                        rdata <= {30'b0, status_rx_valid, status_busy};
                        rresp <= 2'b0;
                    end
                    5'h4: begin
                        rdata <= {31'b0, ctrl_cs_assert};
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

    logic miso_sync0;  // miso synchroniser stage 0
    logic miso_sync1;  // miso synchroniser stage 1
    logic miso_sync2;  // miso synchroniser stage 2
    logic miso_sync3;  // miso synchroniser stage 3
    logic spi_active;  // An exchange is in progress
    logic spi_go;  // TXDATA write strobe, delayed one cycle
    logic sclk_int;  // Clock before the CPOL inversion; idles low
    logic [15:0] half_cnt;  // aclk cycles within one sclk half period
    logic [4:0] edge_cnt;  // sclk edges so far, 0..15
    logic [7:0] tx_shift;  // Transmit shift register, empties from the MSB
    logic [7:0] rx_shift;  // Receive shift register, fills from the LSB

    always_ff @(posedge aclk) begin
        if (!areset_n) begin
            spi_active <= 1'b0;
            spi_go <= 1'b0;
            sclk_int <= 1'b0;
            mosi <= 1'b0;
            half_cnt <= 16'b0;
            edge_cnt <= 5'b0;
            tx_shift <= 8'b0;
            rx_shift <= 8'b0;
            rxdata_data <= 8'b0;
            status_rx_valid_set <= 1'b0;
            miso_sync0 <= 1'b0;
            miso_sync1 <= 1'b0;
            miso_sync2 <= 1'b0;
            miso_sync3 <= 1'b0;
        end else begin
            status_rx_valid_set <= 1'b0;
            miso_sync0 <= miso;
            miso_sync1 <= miso_sync0;
            miso_sync2 <= miso_sync1;
            miso_sync3 <= miso_sync2;
            spi_go <= wr_sel_txdata;
            if (!spi_active) begin
                if (spi_go) begin
                    spi_active <= 1'b1;
                    half_cnt <= 16'b0;
                    edge_cnt <= 5'b0;
                    rx_shift <= 8'b0;
                    mosi <= txdata_data[7];
                    tx_shift <= {txdata_data[6:0], 1'b0};
                end
            end else begin
                if (half_cnt == (clkdiv_div - 16'b1)) begin
                    half_cnt <= 16'b0;
                    sclk_int <= !sclk_int;
                    if (edge_cnt == 5'd15) begin
                        spi_active <= 1'b0;
                        rxdata_data <= rx_shift;
                        status_rx_valid_set <= 1'b1;
                    end else begin
                        if (edge_cnt[0] == 1'b0) begin
                            rx_shift <= {rx_shift[6:0], miso_sync3};
                        end else begin
                            mosi <= tx_shift[7];
                            tx_shift <= {tx_shift[6:0], 1'b0};
                        end
                        edge_cnt <= edge_cnt + 5'b1;
                    end
                end else begin
                    half_cnt <= half_cnt + 16'b1;
                end
            end
        end
    end

    assign status_busy = spi_active;

    assign cs_n = !ctrl_cs_assert;

    assign sclk = sclk_int;

endmodule
