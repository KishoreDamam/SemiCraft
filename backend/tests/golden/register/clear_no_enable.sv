// SemiCraft v0.1.0
// Snippet: register (config hash: 9d4a33a7209b)
// 8-bit synchronous register
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module register #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    input  logic             clr,     // Synchronous clear (loads reset_value; beats enable)
    input  logic [WIDTH-1:0] d,       // Data input
    output logic [WIDTH-1:0] q        // Registered data output
);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            q <= {WIDTH{1'b0}};
        end else begin
            if (clr) begin
                q <= {WIDTH{1'b0}};
            end else begin
                q <= d;
            end
        end
    end

endmodule
