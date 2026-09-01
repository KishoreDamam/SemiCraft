// SemiCraft v0.4.0
// Snippet: register (config hash: 80510f67aebf)
// 8-bit synchronous register
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module register #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             p_clk,     // Clock
    input  logic             p_rst_n,   // Sync reset, active-low
    input  logic             p_en,      // Load enable (holds value when low)
    input  logic [WIDTH-1:0] p_d,       // Data input
    output logic [WIDTH-1:0] p_q        // Registered data output
);

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_q <= {WIDTH{1'b0}};
        end else begin
            if (p_en) begin
                p_q <= p_d;
            end
        end
    end

endmodule
