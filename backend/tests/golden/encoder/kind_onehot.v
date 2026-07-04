// SemiCraft v0.1.0
// Snippet: encoder (config hash: 84400de3ff40)
// One-hot encoder, 8 inputs
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module encoder #(
    parameter NUM_INPUTS = 8
) (
    input  wire [NUM_INPUTS-1:0] din,    // 8-bit input vector
    output reg  [OUT_WIDTH-1:0]  dout,   // Encoded index output
    output reg                   valid   // High when dout reflects a valid encoded input
);

    localparam OUT_WIDTH = 3;

    always @(*) begin
        // One-hot encoder: din is assumed one-hot; exactly one bit set maps to its index. Non-one-hot din (zero or multiple bits set) hits the default arm.
        case (din)
            {{(NUM_INPUTS-1){1'b0}}, 1'b1}: begin
                dout = {OUT_WIDTH{1'b0}};
                valid = 1'b1;
            end
            {{(NUM_INPUTS-2){1'b0}}, 2'b10}: begin
                dout = {{(OUT_WIDTH-1){1'b0}}, 1'b1};
                valid = 1'b1;
            end
            {{(NUM_INPUTS-3){1'b0}}, 3'b100}: begin
                dout = {{(OUT_WIDTH-2){1'b0}}, 2'b10};
                valid = 1'b1;
            end
            {{(NUM_INPUTS-4){1'b0}}, 4'b1000}: begin
                dout = {{(OUT_WIDTH-2){1'b0}}, 2'b11};
                valid = 1'b1;
            end
            {{(NUM_INPUTS-5){1'b0}}, 5'b10000}: begin
                dout = {{(OUT_WIDTH-3){1'b0}}, 3'b100};
                valid = 1'b1;
            end
            {{(NUM_INPUTS-6){1'b0}}, 6'b100000}: begin
                dout = {{(OUT_WIDTH-3){1'b0}}, 3'b101};
                valid = 1'b1;
            end
            {{(NUM_INPUTS-7){1'b0}}, 7'b1000000}: begin
                dout = {{(OUT_WIDTH-3){1'b0}}, 3'b110};
                valid = 1'b1;
            end
            {{(NUM_INPUTS-8){1'b0}}, 8'b10000000}: begin
                dout = {{(OUT_WIDTH-3){1'b0}}, 3'b111};
                valid = 1'b1;
            end
            default: begin
                dout = {OUT_WIDTH{1'b0}};
                valid = 1'b0;
            end
        endcase
    end

endmodule
