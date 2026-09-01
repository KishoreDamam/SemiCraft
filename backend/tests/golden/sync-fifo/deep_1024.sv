// SemiCraft v0.4.0
// Snippet: sync_fifo (config hash: 042a7b1b4ddc)
// 1024-entry x 16-bit synchronous FIFO
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_fifo (
    input  logic        clk,       // Clock; both ports are synchronous to it
    input  logic        rst_n,     // Sync reset, active-low; empties the FIFO
    input  logic        wr_en,     // Write enable; ignored while full
    input  logic [15:0] wr_data,   // Write data
    output logic        full,      // No space remains; writes are ignored
    input  logic        rd_en,     // Read enable; ignored while empty
    output logic [15:0] rd_data,   // Read data, valid the cycle after rd_en
    output logic        empty,     // No entries remain; reads are ignored
    output logic [10:0] count      // Current occupancy, 0..1024
);

    logic [15:0] mem [1024];  // Storage array
    logic [10:0] wptr;  // Write pointer with wrap bit
    logic [10:0] rptr;  // Read pointer with wrap bit

    assign empty = wptr == rptr;

    assign full = (wptr[10] != rptr[10]) && (wptr[9:0] == rptr[9:0]);

    assign count = wptr - rptr;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            wptr <= 11'd0;
            rptr <= 11'd0;
            rd_data <= 16'd0;
        end else begin
            if (wr_en && (!full)) begin
                mem[wptr[9:0]] <= wr_data;
                wptr <= wptr + 1'b1;
            end
            if (rd_en && (!empty)) begin
                rd_data <= mem[rptr[9:0]];
                rptr <= rptr + 1'b1;
            end
        end
    end

endmodule
