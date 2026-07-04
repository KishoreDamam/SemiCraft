// SemiCraft v0.1.0
// Snippet: encoder (config hash: d9737b31af98)
// One-hot encoder, 8 inputs
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
        // One-hot encoder: din is assumed one-hot; exactly one bit set maps to its index. Non-one-hot din (zero or multiple bits set) hits the default arm.
        case (din)
            {{(NUM_INPUTS-1){1'b0}}, 1'b1}: dout = {OUT_WIDTH{1'b0}};
            {{(NUM_INPUTS-2){1'b0}}, 2'b10}: dout = {{(OUT_WIDTH-1){1'b0}}, 1'b1};
            {{(NUM_INPUTS-3){1'b0}}, 3'b100}: dout = {{(OUT_WIDTH-2){1'b0}}, 2'b10};
            {{(NUM_INPUTS-4){1'b0}}, 4'b1000}: dout = {{(OUT_WIDTH-2){1'b0}}, 2'b11};
            {{(NUM_INPUTS-5){1'b0}}, 5'b10000}: dout = {{(OUT_WIDTH-3){1'b0}}, 3'b100};
            {{(NUM_INPUTS-6){1'b0}}, 6'b100000}: dout = {{(OUT_WIDTH-3){1'b0}}, 3'b101};
            {{(NUM_INPUTS-7){1'b0}}, 7'b1000000}: dout = {{(OUT_WIDTH-3){1'b0}}, 3'b110};
            {{(NUM_INPUTS-8){1'b0}}, 8'b10000000}: dout = {{(OUT_WIDTH-3){1'b0}}, 3'b111};
            default: dout = {OUT_WIDTH{1'b0}};
        endcase
    end

endmodule
