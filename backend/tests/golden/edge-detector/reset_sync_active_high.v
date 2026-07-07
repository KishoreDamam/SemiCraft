// SemiCraft v0.1.0
// Snippet: edge_detector (config hash: 82a8831988fa)
// Rising-edge detector, one-cycle pulse
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module edge_detector (
    input  wire clk,    // Clock
    input  wire rst,    // Sync reset, active-high
    input  wire d,      // Input signal to detect edges on
    output reg  pulse   // One-cycle rising-edge pulse (registered output)
);

    reg d_q;  // Previous-cycle value of d (delay register)

    always @(posedge clk) begin
        if (rst) begin
            d_q <= 1'b0;
            pulse <= 1'b0;
        end else begin
            d_q <= d;
            pulse <= d & (~d_q);
        end
    end

endmodule
