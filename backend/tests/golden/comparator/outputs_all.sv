// SemiCraft v0.1.0
// Snippet: comparator (config hash: d153da301dc9)
// 8-bit unsigned comparator (eq, ne, lt, le, gt, ge)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module comparator #(
    parameter int unsigned WIDTH = 8
) (
    input  logic [WIDTH-1:0] a,    // First comparison operand
    input  logic [WIDTH-1:0] b,    // Second comparison operand
    output logic             eq,   // Comparison result: 1 when a is equal to b, else 0.
    output logic             ne,   // Comparison result: 1 when a is not equal to b, else 0.
    output logic             lt,   // Comparison result: 1 when a is less than b, else 0.
    output logic             le,   // Comparison result: 1 when a is less than or equal to b, else 0.
    output logic             gt,   // Comparison result: 1 when a is greater than b, else 0.
    output logic             ge    // Comparison result: 1 when a is greater than or equal to b, else 0.
);

    assign eq = a == b;

    assign ne = a != b;

    assign lt = a < b;

    assign le = a <= b;

    assign gt = a > b;

    assign ge = a >= b;

endmodule
