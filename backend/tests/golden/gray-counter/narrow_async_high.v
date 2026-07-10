// SemiCraft v0.1.0
// Snippet: gray_counter (config hash: 2fea13b6cbc4)
// 3-bit Gray-code counter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module gray_counter #(
    parameter WIDTH = 3
) (
    input  wire             clk,   // Clock
    input  wire             rst,   // Async reset, active-high
    input  wire             en,    // Count enable (holds when low)
    output wire [WIDTH-1:0] gray   // Gray-coded output, combinational (bin ^ (bin >> 1)) from the binary counter
);

    reg [WIDTH-1:0] bin;  // Free-running binary counter (registered)

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            bin <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                bin <= bin + 1'b1;
            end
        end
    end

    assign gray = bin ^ (bin >> 1'b1);

endmodule
