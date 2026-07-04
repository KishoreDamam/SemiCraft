// SemiCraft v0.1.0
// Snippet: mux (config hash: 651c0a8bcada)
// 4-input 32-bit multiplexer (ternary)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module mux #(
    parameter WIDTH = 32
) (
    input  wire [WIDTH-1:0]     in0,   // Data input in0
    input  wire [WIDTH-1:0]     in1,   // Data input in1
    input  wire [WIDTH-1:0]     in2,   // Data input in2
    input  wire [WIDTH-1:0]     in3,   // Data input in3
    input  wire [SEL_WIDTH-1:0] sel,   // Input select
    output wire [WIDTH-1:0]     out    // Selected data output
);

    localparam SEL_WIDTH = 2;

    assign out = (sel == {{(SEL_WIDTH-1){1'b0}}, 1'b1}) ? in1 : ((sel == {{(SEL_WIDTH-2){1'b0}}, 2'b10}) ? in2 : ((sel == {{(SEL_WIDTH-2){1'b0}}, 2'b11}) ? in3 : in0));

endmodule
