// SemiCraft v0.1.0
// Snippet: gray_counter (config hash: 4ba845f60dd2)
// 16-bit Gray-code counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module gray_counter #(
    parameter WIDTH = 16
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    output wire [WIDTH-1:0] gray     // Gray-coded output, combinational (bin ^ (bin >> 1)) from the binary counter
);

    reg [WIDTH-1:0] bin;  // Free-running binary counter (registered)

    always @(posedge clk) begin
        if (!rst_n) begin
            bin <= {WIDTH{1'b0}};
        end else begin
            bin <= bin + 1'b1;
        end
    end

    assign gray = bin ^ (bin >> 1'b1);

endmodule
