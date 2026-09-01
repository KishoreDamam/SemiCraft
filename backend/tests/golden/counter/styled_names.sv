// SemiCraft v0.4.0
// Snippet: counter (config hash: d1b258572f61)
// Up counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             p_clk,     // Clock
    input  logic             p_rst_n,   // Sync reset, active-low
    input  logic             p_en,      // Count enable (holds when low)
    output logic [WIDTH-1:0] p_count    // Current count value
);

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_count <= {WIDTH{1'b0}};
        end else begin
            if (p_en) begin
                p_count <= p_count + 1'b1;
            end
        end
    end

endmodule
