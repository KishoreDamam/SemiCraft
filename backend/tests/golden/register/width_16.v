// SemiCraft v0.1.0
// Snippet: register (config hash: d88b56e33974)
// 16-bit synchronous register
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module register #(
    parameter WIDTH = 16
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    input  wire             en,      // Load enable (holds value when low)
    input  wire [WIDTH-1:0] d,       // Data input
    output reg  [WIDTH-1:0] q        // Registered data output
);

    always @(posedge clk) begin
        if (!rst_n) begin
            q <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                q <= d;
            end
        end
    end

endmodule
