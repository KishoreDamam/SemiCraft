// SemiCraft v0.3.0
// Snippet: sync_fifo (config hash: ca906f6a8e24)
// 8-entry x 8-bit synchronous FIFO
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_fifo (
    input  logic       clk,       // Clock; both ports are synchronous to it
    input  logic       rst_n,     // Sync reset, active-low; empties the FIFO
    input  logic       wr_en,     // Write enable; ignored while full
    input  logic [7:0] wr_data,   // Write data
    output logic       full,      // No space remains; writes are ignored
    input  logic       rd_en,     // Read enable; ignored while empty
    output logic [7:0] rd_data,   // Read data, valid the cycle after rd_en
    output logic       empty      // No entries remain; reads are ignored
);

    logic [7:0] mem [8];  // Storage array
    logic [3:0] wptr;  // Write pointer with wrap bit
    logic [3:0] rptr;  // Read pointer with wrap bit

    assign empty = wptr == rptr;

    assign full = (wptr[3] != rptr[3]) && (wptr[2:0] == rptr[2:0]);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            wptr <= 4'd0;
            rptr <= 4'd0;
            rd_data <= 8'd0;
        end else begin
            if (wr_en && (!full)) begin
                mem[wptr[2:0]] <= wr_data;
                wptr <= wptr + 1'b1;
            end
            if (rd_en && (!empty)) begin
                rd_data <= mem[rptr[2:0]];
                rptr <= rptr + 1'b1;
            end
        end
    end

endmodule
