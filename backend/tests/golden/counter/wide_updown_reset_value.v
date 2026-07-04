// SemiCraft v0.1.0
// Snippet: counter (config hash: b303ebbd8531)
// Up/down counter, 32-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter WIDTH = 32
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    input  wire             en,      // Count enable (holds when low)
    input  wire             up_dn,   // Direction select (1 = up, 0 = down)
    output reg  [WIDTH-1:0] count    // Current count value
);

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= {{(WIDTH-6){1'b0}}, 6'b101010};
        end else begin
            if (en) begin
                count <= up_dn ? (count + 1'b1) : (count - 1'b1);
            end
        end
    end

endmodule
