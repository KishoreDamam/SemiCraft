// SemiCraft v0.3.0
// Snippet: sync_fifo (config hash: ac4b61ce8c0b)
// 256-entry x 8-bit synchronous FIFO
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_fifo (
    input  wire       clk,       // Clock; both ports are synchronous to it
    input  wire       rst_n,     // Sync reset, active-low; empties the FIFO
    input  wire       wr_en,     // Write enable; ignored while full
    input  wire [7:0] wr_data,   // Write data
    output wire       full,      // No space remains; writes are ignored
    input  wire       rd_en,     // Read enable; ignored while empty
    output reg  [7:0] rd_data,   // Read data, valid the cycle after rd_en
    output wire       empty      // No entries remain; reads are ignored
);

    reg [7:0] mem [0:255];  // Storage array
    reg [8:0] wptr;  // Write pointer with wrap bit
    reg [8:0] rptr;  // Read pointer with wrap bit

    assign empty = wptr == rptr;

    assign full = (wptr[8] != rptr[8]) && (wptr[7:0] == rptr[7:0]);

    always @(posedge clk) begin
        if (!rst_n) begin
            wptr <= 9'd0;
            rptr <= 9'd0;
            rd_data <= 8'd0;
        end else begin
            if (wr_en && (!full)) begin
                mem[wptr[7:0]] <= wr_data;
                wptr <= wptr + 1'b1;
            end
            if (rd_en && (!empty)) begin
                rd_data <= mem[rptr[7:0]];
                rptr <= rptr + 1'b1;
            end
        end
    end

endmodule
