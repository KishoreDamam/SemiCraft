// SemiCraft v0.1.0
// Snippet: decoder (config hash: add15546080b)
// 8-output binary decoder, active-low
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module decoder #(
    parameter NUM_OUTPUTS = 8
) (
    input  wire [2:0]             sel,   // Binary select input
    output wire [NUM_OUTPUTS-1:0] dout   // One-hot active-low decoded output
);

    assign dout = ~({{(NUM_OUTPUTS-1){1'b0}}, 1'b1} << sel);

endmodule
