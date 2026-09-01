// SemiCraft v0.4.0
// Snippet: gray_counter (config hash: 0b6953eb14f8)
// 8-bit Gray-code counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module gray_counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             p_clk,     // Clock
    input  logic             p_rst_n,   // Sync reset, active-low
    input  logic             p_en,      // Count enable (holds when low)
    output logic [WIDTH-1:0] p_gray     // Gray-coded output, combinational (bin ^ (bin >> 1)) from the binary counter
);

    logic [WIDTH-1:0] p_bin;  // Free-running binary counter (registered)

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_bin <= {WIDTH{1'b0}};
        end else begin
            if (p_en) begin
                p_bin <= p_bin + 1'b1;
            end
        end
    end

    assign p_gray = p_bin ^ (p_bin >> 1'b1);

endmodule
