// SemiCraft v0.1.0
// Snippet: decoder (config hash: f3d8b72c7db1)
// 8-output binary decoder, active-high
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module decoder #(
    parameter NUM_OUTPUTS = 8
) (
    input  wire [2:0]             sel,   // Binary select input
    output wire [NUM_OUTPUTS-1:0] dout   // One-hot active-high decoded output
);

    assign dout = {{(NUM_OUTPUTS-1){1'b0}}, 1'b1} << sel;

endmodule
