// SemiCraft v0.1.0
// Snippet: gray_counter (config hash: 481026d1af2e)
// 2-bit Gray-code counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module gray_counter #(
    parameter int unsigned WIDTH = 2
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    input  logic             en,      // Count enable (holds when low)
    output logic [WIDTH-1:0] gray     // Gray-coded output, combinational (bin ^ (bin >> 1)) from the binary counter
);

    logic [WIDTH-1:0] bin;  // Free-running binary counter (registered)

    always_ff @(posedge clk) begin
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
