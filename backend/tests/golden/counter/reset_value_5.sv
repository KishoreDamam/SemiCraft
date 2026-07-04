// SemiCraft v0.1.0
// Snippet: counter (config hash: cf1455920669)
// Up counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    input  logic             en,      // Count enable (holds when low)
    output logic [WIDTH-1:0] count    // Current count value
);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            count <= {{(WIDTH-3){1'b0}}, 3'b101};
        end else begin
            if (en) begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
