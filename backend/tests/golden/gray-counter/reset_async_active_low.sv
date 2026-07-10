// SemiCraft v0.1.0
// Snippet: gray_counter (config hash: 69255e5234b0)
// 8-bit Gray-code counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module gray_counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Async reset, active-low
    input  logic             en,      // Count enable (holds when low)
    output logic [WIDTH-1:0] gray     // Gray-coded output, combinational (bin ^ (bin >> 1)) from the binary counter
);

    logic [WIDTH-1:0] bin;  // Free-running binary counter (registered)

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bin <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                bin <= bin + 1'b1;
            end
        end
    end

    assign gray = bin ^ (bin >> 1'b1);

endmodule
