// SemiCraft v0.1.0
// Snippet: lfsr (config hash: 5f0e2ee34e84)
// 24-bit Fibonacci LFSR, parallel output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter WIDTH = 24,
    parameter INIT = {{(WIDTH-24){1'b0}}, 24'b101010111100110111100001}
) (
    input  wire             clk,   // Clock
    input  wire             rst,   // Async reset, active-high
    input  wire             en,    // Shift enable (holds when low)
    output reg  [WIDTH-1:0] q      // LFSR register state
);

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            q <= INIT;
        end else begin
            if (en) begin
                q <= {(((q[23] ^ q[22]) ^ q[21]) ^ q[16]), q[WIDTH-1:1]};
            end
        end
    end

endmodule
