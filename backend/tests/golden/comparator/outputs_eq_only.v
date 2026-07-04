// SemiCraft v0.1.0
// Snippet: comparator (config hash: 4e08219c6079)
// 8-bit unsigned comparator (eq)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module comparator #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0] a,   // First comparison operand
    input  wire [WIDTH-1:0] b,   // Second comparison operand
    output wire             eq   // Comparison result: 1 when a is equal to b, else 0.
);

    assign eq = a == b;

endmodule
