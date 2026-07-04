// SemiCraft v0.1.0
// Snippet: counter (config hash: 3c5657217c39)
// Up/down counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter WIDTH = 8
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    input  wire             en,      // Count enable (holds when low)
    input  wire             up_dn,   // Direction select (1 = up, 0 = down)
    output reg  [WIDTH-1:0] count    // Current count value
);

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                if (up_dn) begin
                    if (count != {{(WIDTH-8){1'b0}}, 8'b11111111}) begin
                        count <= count + 1'b1;
                    end
                end else begin
                    if (count != {WIDTH{1'b0}}) begin
                        count <= count - 1'b1;
                    end
                end
            end
        end
    end

endmodule
