// SemiCraft v0.4.0
// Snippet: sync_fifo (config hash: aa4576c29109)
// 8-entry x 8-bit synchronous FIFO
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_fifo (
    input  logic       p_clk,      // Clock; both ports are synchronous to it
    input  logic       p_rst_n,    // Sync reset, active-low; empties the FIFO
    input  logic       p_wrEn,     // Write enable; ignored while full
    input  logic [7:0] p_wrData,   // Write data
    output logic       p_full,     // No space remains; writes are ignored
    input  logic       p_rdEn,     // Read enable; ignored while empty
    output logic [7:0] p_rdData,   // Read data, valid the cycle after rd_en
    output logic       p_empty,    // No entries remain; reads are ignored
    output logic [3:0] p_count     // Current occupancy, 0..8
);

    logic [7:0] p_mem [8];  // Storage array
    logic [3:0] p_wptr;  // Write pointer with wrap bit
    logic [3:0] p_rptr;  // Read pointer with wrap bit

    assign p_empty = p_wptr == p_rptr;

    assign p_full = (p_wptr[3] != p_rptr[3]) && (p_wptr[2:0] == p_rptr[2:0]);

    assign p_count = p_wptr - p_rptr;

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_wptr <= 4'd0;
            p_rptr <= 4'd0;
            p_rdData <= 8'd0;
        end else begin
            if (p_wrEn && (!p_full)) begin
                p_mem[p_wptr[2:0]] <= p_wrData;
                p_wptr <= p_wptr + 1'b1;
            end
            if (p_rdEn && (!p_empty)) begin
                p_rdData <= p_mem[p_rptr[2:0]];
                p_rptr <= p_rptr + 1'b1;
            end
        end
    end

endmodule
