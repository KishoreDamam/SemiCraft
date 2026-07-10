// SemiCraft v0.1.0
// Snippet: gray_counter (config hash: e39b440a9b20)
// 24-bit Gray-code counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module gray_counter #(
    parameter int unsigned WIDTH = 24
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    output logic [WIDTH-1:0] gray     // Gray-coded output, combinational (bin ^ (bin >> 1)) from the binary counter
);

    logic [WIDTH-1:0] bin;  // Free-running binary counter (registered)

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            bin <= {WIDTH{1'b0}};
        end else begin
            bin <= bin + 1'b1;
        end
    end

    assign gray = bin ^ (bin >> 1'b1);

endmodule
