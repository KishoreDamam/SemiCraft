// SemiCraft v0.1.0
// Snippet: edge_detector (config hash: 83dc7562b8bf)
// Any (both)-edge detector, one-cycle pulse
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module edge_detector (
    input  logic clk,     // Clock
    input  logic rst_n,   // Sync reset, active-low
    input  logic d,       // Input signal to detect edges on
    output logic pulse    // One-cycle any (both)-edge pulse (registered output)
);

    logic d_q;  // Previous-cycle value of d (delay register)

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            d_q <= 1'b0;
            pulse <= 1'b0;
        end else begin
            d_q <= d;
            pulse <= d ^ d_q;
        end
    end

endmodule
