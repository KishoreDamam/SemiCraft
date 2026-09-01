// SemiCraft v0.4.0
// Snippet: comparator (config hash: ba3f41ec86d0)
// 8-bit unsigned comparator (eq, lt, gt)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module comparator #(
    parameter int unsigned WIDTH = 8
) (
    input  logic [WIDTH-1:0] p_a,    // First comparison operand
    input  logic [WIDTH-1:0] p_b,    // Second comparison operand
    output logic             p_eq,   // Comparison result: 1 when a is equal to b, else 0.
    output logic             p_lt,   // Comparison result: 1 when a is less than b, else 0.
    output logic             p_gt    // Comparison result: 1 when a is greater than b, else 0.
);

    assign p_eq = p_a == p_b;

    assign p_lt = p_a < p_b;

    assign p_gt = p_a > p_b;

endmodule
