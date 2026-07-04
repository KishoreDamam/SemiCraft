// SemiCraft v0.1.0
// Snippet: mux (config hash: 8cbd25daa9e0)
// 16-input 8-bit multiplexer (ternary)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module mux #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0]     in0,    // Data input in0
    input  wire [WIDTH-1:0]     in1,    // Data input in1
    input  wire [WIDTH-1:0]     in2,    // Data input in2
    input  wire [WIDTH-1:0]     in3,    // Data input in3
    input  wire [WIDTH-1:0]     in4,    // Data input in4
    input  wire [WIDTH-1:0]     in5,    // Data input in5
    input  wire [WIDTH-1:0]     in6,    // Data input in6
    input  wire [WIDTH-1:0]     in7,    // Data input in7
    input  wire [WIDTH-1:0]     in8,    // Data input in8
    input  wire [WIDTH-1:0]     in9,    // Data input in9
    input  wire [WIDTH-1:0]     in10,   // Data input in10
    input  wire [WIDTH-1:0]     in11,   // Data input in11
    input  wire [WIDTH-1:0]     in12,   // Data input in12
    input  wire [WIDTH-1:0]     in13,   // Data input in13
    input  wire [WIDTH-1:0]     in14,   // Data input in14
    input  wire [WIDTH-1:0]     in15,   // Data input in15
    input  wire [SEL_WIDTH-1:0] sel,    // Input select
    output wire [WIDTH-1:0]     out     // Selected data output
);

    localparam SEL_WIDTH = 4;

    assign out = (sel == {{(SEL_WIDTH-1){1'b0}}, 1'b1}) ? in1 : ((sel == {{(SEL_WIDTH-2){1'b0}}, 2'b10}) ? in2 : ((sel == {{(SEL_WIDTH-2){1'b0}}, 2'b11}) ? in3 : ((sel == {{(SEL_WIDTH-3){1'b0}}, 3'b100}) ? in4 : ((sel == {{(SEL_WIDTH-3){1'b0}}, 3'b101}) ? in5 : ((sel == {{(SEL_WIDTH-3){1'b0}}, 3'b110}) ? in6 : ((sel == {{(SEL_WIDTH-3){1'b0}}, 3'b111}) ? in7 : ((sel == {{(SEL_WIDTH-4){1'b0}}, 4'b1000}) ? in8 : ((sel == {{(SEL_WIDTH-4){1'b0}}, 4'b1001}) ? in9 : ((sel == {{(SEL_WIDTH-4){1'b0}}, 4'b1010}) ? in10 : ((sel == {{(SEL_WIDTH-4){1'b0}}, 4'b1011}) ? in11 : ((sel == {{(SEL_WIDTH-4){1'b0}}, 4'b1100}) ? in12 : ((sel == {{(SEL_WIDTH-4){1'b0}}, 4'b1101}) ? in13 : ((sel == {{(SEL_WIDTH-4){1'b0}}, 4'b1110}) ? in14 : ((sel == {{(SEL_WIDTH-4){1'b0}}, 4'b1111}) ? in15 : in0))))))))))))));

endmodule
