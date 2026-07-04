// SemiCraft v0.1.0
// Snippet: mux (config hash: 614647aa6dc0)
// 8-input 8-bit multiplexer (case)
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
    input  logic [WIDTH-1:0]     in4,   // Data input in4
    input  logic [WIDTH-1:0]     in5,   // Data input in5
    input  logic [WIDTH-1:0]     in6,   // Data input in6
    input  logic [WIDTH-1:0]     in7,   // Data input in7
    input  logic [SEL_WIDTH-1:0] sel,   // Input select
    output logic [WIDTH-1:0]     out    // Selected data output
);

    localparam int unsigned SEL_WIDTH = 3;

    always_comb begin
        case (sel)
            {SEL_WIDTH{1'b0}}: out = in0;
            {{(SEL_WIDTH-1){1'b0}}, 1'b1}: out = in1;
            {{(SEL_WIDTH-2){1'b0}}, 2'b10}: out = in2;
            {{(SEL_WIDTH-2){1'b0}}, 2'b11}: out = in3;
            {{(SEL_WIDTH-3){1'b0}}, 3'b100}: out = in4;
            {{(SEL_WIDTH-3){1'b0}}, 3'b101}: out = in5;
            {{(SEL_WIDTH-3){1'b0}}, 3'b110}: out = in6;
            {{(SEL_WIDTH-3){1'b0}}, 3'b111}: out = in7;
            default: out = in0;
        endcase
    end

endmodule
