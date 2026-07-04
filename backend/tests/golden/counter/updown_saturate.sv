// SemiCraft v0.1.0
// Snippet: counter (config hash: 00d4b8531841)
// Up/down counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    input  logic             en,      // Count enable (holds when low)
    input  logic             up_dn,   // Direction select (1 = up, 0 = down)
    output logic [WIDTH-1:0] count    // Current count value
);

    always_ff @(posedge clk) begin
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
