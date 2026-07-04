// SemiCraft v0.1.0
// Snippet: encoder (config hash: a199a4924cb5)
// Priority encoder, 8 inputs
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module encoder #(
    parameter NUM_INPUTS = 8
) (
    input  wire [NUM_INPUTS-1:0] din,   // 8-bit input vector
    output reg  [OUT_WIDTH-1:0]  dout   // Encoded index output
);

    localparam OUT_WIDTH = 3;

    always @(*) begin
        // Priority encoder: highest-indexed set bit wins (din[7] is highest priority, din[0] is lowest priority).
        dout = {OUT_WIDTH{1'b0}};
        if (din[7]) begin
            dout = {{(OUT_WIDTH-3){1'b0}}, 3'b111};
        end else if (din[6]) begin
            dout = {{(OUT_WIDTH-3){1'b0}}, 3'b110};
        end else if (din[5]) begin
            dout = {{(OUT_WIDTH-3){1'b0}}, 3'b101};
        end else if (din[4]) begin
            dout = {{(OUT_WIDTH-3){1'b0}}, 3'b100};
        end else if (din[3]) begin
            dout = {{(OUT_WIDTH-2){1'b0}}, 2'b11};
        end else if (din[2]) begin
            dout = {{(OUT_WIDTH-2){1'b0}}, 2'b10};
        end else if (din[1]) begin
            dout = {{(OUT_WIDTH-1){1'b0}}, 1'b1};
        end else if (din[0]) begin
            dout = {OUT_WIDTH{1'b0}};
        end
    end

endmodule
