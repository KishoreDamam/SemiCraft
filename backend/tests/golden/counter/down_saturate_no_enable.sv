// SemiCraft v0.1.0
// Snippet: counter (config hash: e46b8b5bcc45)
// Down counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    output logic [WIDTH-1:0] count    // Current count value
);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else begin
            if (count != {WIDTH{1'b0}}) begin
                count <= count - 1'b1;
            end
        end
    end

endmodule
