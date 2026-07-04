// SemiCraft v0.1.0
// Snippet: counter (config hash: 03451d07e627)
// Up counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter WIDTH = 8
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Async reset, active-low
    input  wire             en,      // Count enable (holds when low)
    output reg  [WIDTH-1:0] count    // Current count value
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
