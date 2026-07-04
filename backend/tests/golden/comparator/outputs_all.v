// SemiCraft v0.1.0
// Snippet: comparator (config hash: e07757e3c679)
// 8-bit unsigned comparator (eq, ne, lt, le, gt, ge)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module comparator #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0] a,    // First comparison operand
    input  wire [WIDTH-1:0] b,    // Second comparison operand
    output wire             eq,   // Comparison result: 1 when a is equal to b, else 0.
    output wire             ne,   // Comparison result: 1 when a is not equal to b, else 0.
    output wire             lt,   // Comparison result: 1 when a is less than b, else 0.
    output wire             le,   // Comparison result: 1 when a is less than or equal to b, else 0.
    output wire             gt,   // Comparison result: 1 when a is greater than b, else 0.
    output wire             ge    // Comparison result: 1 when a is greater than or equal to b, else 0.
);

    assign eq = a == b;

    assign ne = a != b;

    assign lt = a < b;

    assign le = a <= b;

    assign gt = a > b;

    assign ge = a >= b;

endmodule
