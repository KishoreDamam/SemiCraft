// SemiCraft v0.4.0
// Snippet: decoder (config hash: f1cc1c320f0d)
// 8-output binary decoder, active-high
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module decoder #(
    parameter int unsigned NUM_OUTPUTS = 8
) (
    input  logic [2:0]             p_sel,   // Binary select input
    input  logic                   p_en,    // Decoder enable; when low all outputs go to their disabled state
    output logic [NUM_OUTPUTS-1:0] p_dout   // One-hot active-high decoded output
);

    assign p_dout = p_en ? ({{(NUM_OUTPUTS-1){1'b0}}, 1'b1} << p_sel) : {NUM_OUTPUTS{1'b0}};

endmodule
