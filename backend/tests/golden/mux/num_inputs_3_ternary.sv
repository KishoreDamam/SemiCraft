// SemiCraft v0.1.0
// Snippet: mux (config hash: 9a85696c6ee5)
// 3-input 8-bit multiplexer (ternary)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module mux #(
    parameter int unsigned WIDTH = 8
) (
    input  logic [WIDTH-1:0]     in0,   // Data input in0
    input  logic [WIDTH-1:0]     in1,   // Data input in1
    input  logic [WIDTH-1:0]     in2,   // Data input in2
    input  logic [SEL_WIDTH-1:0] sel,   // Input select
    output logic [WIDTH-1:0]     out    // Selected data output
);

    localparam int unsigned SEL_WIDTH = 2;

    assign out = (sel == {{(SEL_WIDTH-1){1'b0}}, 1'b1}) ? in1 : ((sel == {{(SEL_WIDTH-2){1'b0}}, 2'b10}) ? in2 : in0);

endmodule
