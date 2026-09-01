// SemiCraft v0.4.0
// Snippet: mux (config hash: dd744edd3657)
// 4-input 8-bit multiplexer (case)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module mux #(
    parameter int unsigned WIDTH = 8
) (
    input  logic [WIDTH-1:0]     p_in0,   // Data input in0
    input  logic [WIDTH-1:0]     p_in1,   // Data input in1
    input  logic [WIDTH-1:0]     p_in2,   // Data input in2
    input  logic [WIDTH-1:0]     p_in3,   // Data input in3
    input  logic [SEL_WIDTH-1:0] p_sel,   // Input select
    output logic [WIDTH-1:0]     p_out    // Selected data output
);

    localparam int unsigned SEL_WIDTH = 2;

    always_comb begin
        case (p_sel)
            {SEL_WIDTH{1'b0}}: p_out = p_in0;
            {{(SEL_WIDTH-1){1'b0}}, 1'b1}: p_out = p_in1;
            {{(SEL_WIDTH-2){1'b0}}, 2'b10}: p_out = p_in2;
            {{(SEL_WIDTH-2){1'b0}}, 2'b11}: p_out = p_in3;
            default: p_out = p_in0;
        endcase
    end

endmodule
