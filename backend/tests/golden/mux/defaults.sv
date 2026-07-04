// SemiCraft v0.1.0
// Snippet: mux (config hash: 7ec728682a6e)
// 4-input 8-bit multiplexer (case)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module mux #(
    parameter int unsigned WIDTH = 8
) (
    input  logic [WIDTH-1:0]     in0,   // Data input in0
    input  logic [WIDTH-1:0]     in1,   // Data input in1
    input  logic [WIDTH-1:0]     in2,   // Data input in2
    input  logic [WIDTH-1:0]     in3,   // Data input in3
    input  logic [SEL_WIDTH-1:0] sel,   // Input select
    output logic [WIDTH-1:0]     out    // Selected data output
);

    localparam int unsigned SEL_WIDTH = 2;

    always_comb begin
        case (sel)
            {SEL_WIDTH{1'b0}}: out = in0;
            {{(SEL_WIDTH-1){1'b0}}, 1'b1}: out = in1;
            {{(SEL_WIDTH-2){1'b0}}, 2'b10}: out = in2;
            {{(SEL_WIDTH-2){1'b0}}, 2'b11}: out = in3;
            default: out = in0;
        endcase
    end

endmodule
