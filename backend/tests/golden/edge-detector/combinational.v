// SemiCraft v0.1.0
// Snippet: edge_detector (config hash: 614e85730eb0)
// Rising-edge detector, one-cycle pulse
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module edge_detector (
    input  wire clk,     // Clock
    input  wire rst_n,   // Sync reset, active-low
    input  wire d,       // Input signal to detect edges on
    output wire pulse    // One-cycle rising-edge pulse (combinational output)
);

    reg d_q;  // Previous-cycle value of d (delay register)

    always @(posedge clk) begin
        if (!rst_n) begin
            d_q <= 1'b0;
        end else begin
            d_q <= d;
        end
    end

    assign pulse = d & (~d_q);

endmodule
