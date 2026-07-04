// SemiCraft v0.1.0
// Snippet: decoder (config hash: 8a9789f448fe)
// 8-output binary decoder, active-high
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module decoder #(
    parameter int unsigned NUM_OUTPUTS = 8
) (
    input  logic [2:0]             sel,   // Binary select input
    input  logic                   en,    // Decoder enable; when low all outputs go to their disabled state
    output logic [NUM_OUTPUTS-1:0] dout   // One-hot active-high decoded output
);

    assign dout = en ? ({{(NUM_OUTPUTS-1){1'b0}}, 1'b1} << sel) : {NUM_OUTPUTS{1'b0}};

endmodule
