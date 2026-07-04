// SemiCraft v0.1.0
// Snippet: counter (config hash: 20115cb4f57f)
// Up counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter WIDTH = 8
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    output reg  [WIDTH-1:0] count    // Current count value
);

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else begin
            count <= count + 1'b1;
        end
    end

endmodule
