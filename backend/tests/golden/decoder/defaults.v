// SemiCraft v0.1.0
// Snippet: decoder (config hash: dfac9200ec92)
// 8-output binary decoder, active-high
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module decoder #(
    parameter NUM_OUTPUTS = 8
) (
    input  wire [2:0]             sel,   // Binary select input
    input  wire                   en,    // Decoder enable; when low all outputs go to their disabled state
    output wire [NUM_OUTPUTS-1:0] dout   // One-hot active-high decoded output
);

    assign dout = en ? ({{(NUM_OUTPUTS-1){1'b0}}, 1'b1} << sel) : {NUM_OUTPUTS{1'b0}};

endmodule
