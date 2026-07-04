// SemiCraft v0.1.0
// Snippet: decoder (config hash: f50c15c73165)
// 16-output binary decoder, active-high
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module decoder #(
    parameter NUM_OUTPUTS = 16
) (
    input  wire [3:0]             sel,   // Binary select input
    input  wire                   en,    // Decoder enable; when low all outputs go to their disabled state
    output wire [NUM_OUTPUTS-1:0] dout   // One-hot active-high decoded output
);

    assign dout = en ? ({{(NUM_OUTPUTS-1){1'b0}}, 1'b1} << sel) : {NUM_OUTPUTS{1'b0}};

endmodule
