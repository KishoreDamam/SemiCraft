// SemiCraft v0.1.0
// Snippet: counter (config hash: c75d0b6e7aea)
// Up counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Async reset, active-low
    input  logic             en,      // Count enable (holds when low)
    output logic [WIDTH-1:0] count    // Current count value
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
