// SemiCraft v0.4.0
// Snippet: edge_detector (config hash: 6c652ad52515)
// Rising-edge detector, one-cycle pulse
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module edge_detector (
    input  logic p_clk,     // Clock
    input  logic p_rst_n,   // Sync reset, active-low
    input  logic p_d,       // Input signal to detect edges on
    output logic p_pulse    // One-cycle rising-edge pulse (registered output)
);

    logic p_dQ;  // Previous-cycle value of d (delay register)

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_dQ <= 1'b0;
            p_pulse <= 1'b0;
        end else begin
            p_dQ <= p_d;
            p_pulse <= p_d & (~p_dQ);
        end
    end

endmodule
