// SemiCraft v0.1.0
// Snippet: mux (config hash: fce955b9fdbd)
// 5-input 8-bit multiplexer (case)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module mux #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0]     in0,   // Data input in0
    input  wire [WIDTH-1:0]     in1,   // Data input in1
    input  wire [WIDTH-1:0]     in2,   // Data input in2
    input  wire [WIDTH-1:0]     in3,   // Data input in3
    input  wire [WIDTH-1:0]     in4,   // Data input in4
    input  wire [SEL_WIDTH-1:0] sel,   // Input select
    output reg  [WIDTH-1:0]     out    // Selected data output
);

    localparam SEL_WIDTH = 3;

    always @(*) begin
        case (sel)
            {SEL_WIDTH{1'b0}}: out = in0;
            {{(SEL_WIDTH-1){1'b0}}, 1'b1}: out = in1;
            {{(SEL_WIDTH-2){1'b0}}, 2'b10}: out = in2;
            {{(SEL_WIDTH-2){1'b0}}, 2'b11}: out = in3;
            {{(SEL_WIDTH-3){1'b0}}, 3'b100}: out = in4;
            default: out = in0;
        endcase
    end

endmodule
