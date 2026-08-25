// SemiCraft v0.3.0
// Snippet: sync_fifo (config hash: 498769a7cb86)
// 2-entry x 1-bit synchronous FIFO
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_fifo (
    input  wire       clk,       // Clock; both ports are synchronous to it
    input  wire       rst_n,     // Sync reset, active-low; empties the FIFO
    input  wire       wr_en,     // Write enable; ignored while full
    input  wire [0:0] wr_data,   // Write data
    output wire       full,      // No space remains; writes are ignored
    input  wire       rd_en,     // Read enable; ignored while empty
    output reg  [0:0] rd_data,   // Read data, valid the cycle after rd_en
    output wire       empty,     // No entries remain; reads are ignored
    output wire [1:0] count      // Current occupancy, 0..2
);

    reg [0:0] mem [0:1];  // Storage array
    reg [1:0] wptr;  // Write pointer with wrap bit
    reg [1:0] rptr;  // Read pointer with wrap bit

    assign empty = wptr == rptr;

    assign full = (wptr[1] != rptr[1]) && (wptr[0:0] == rptr[0:0]);

    assign count = wptr - rptr;

    always @(posedge clk) begin
        if (!rst_n) begin
            wptr <= 2'd0;
            rptr <= 2'd0;
            rd_data <= 1'd0;
        end else begin
            if (wr_en && (!full)) begin
                mem[wptr[0:0]] <= wr_data;
                wptr <= wptr + 1'b1;
            end
            if (rd_en && (!empty)) begin
                rd_data <= mem[rptr[0:0]];
                rptr <= rptr + 1'b1;
            end
        end
    end

endmodule
