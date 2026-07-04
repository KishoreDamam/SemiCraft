// SemiCraft v0.1.0
// Snippet: comparator (config hash: 1c068ff5b684)
// 32-bit signed comparator (eq, lt, gt)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module comparator #(
    parameter int unsigned WIDTH = 32
) (
    input  logic signed [WIDTH-1:0] a,    // First comparison operand
    input  logic signed [WIDTH-1:0] b,    // Second comparison operand
    output logic                    eq,   // Comparison result: 1 when a is equal to b, else 0.
    output logic                    lt,   // Comparison result: 1 when a is less than b, else 0.
    output logic                    gt    // Comparison result: 1 when a is greater than b, else 0.
);

    assign eq = a == b;

    assign lt = a < b;

    assign gt = a > b;

endmodule
