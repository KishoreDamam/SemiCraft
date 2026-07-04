// SemiCraft v0.1.0
// Snippet: register (config hash: 2c4fcf87c6a4)
// 8-bit synchronous register
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module register #(
    parameter WIDTH = 8
) (
    input  wire             clk,   // Clock
    input  wire             rst,   // Sync reset, active-high
    input  wire             en,    // Load enable (holds value when low)
    input  wire [WIDTH-1:0] d,     // Data input
    output reg  [WIDTH-1:0] q      // Registered data output
);

    always @(posedge clk) begin
        if (rst) begin
            q <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                q <= d;
            end
        end
    end

endmodule
