// SemiCraft v0.1.0
// Snippet: counter (config hash: 1b516fd7f888)
// Up counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter WIDTH = 8
) (
    input  wire             clk,    // Clock
    input  wire             rst,    // Sync reset, active-high
    input  wire             en,     // Count enable (holds when low)
    output reg  [WIDTH-1:0] count   // Current count value
);

    always @(posedge clk) begin
        if (rst) begin
            count <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
