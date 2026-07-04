// SemiCraft v0.1.0
// Snippet: register (config hash: c0bd370eec20)
// 8-bit synchronous register
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module register #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Async reset, active-low
    input  logic             en,      // Load enable (holds value when low)
    input  logic [WIDTH-1:0] d,       // Data input
    output logic [WIDTH-1:0] q        // Registered data output
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                q <= d;
            end
        end
    end

endmodule
