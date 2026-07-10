// SemiCraft v0.1.0
// Snippet: lfsr (config hash: 594668799f7f)
// 16-bit Fibonacci LFSR, parallel output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter WIDTH = 16,
    parameter INIT = 1
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    input  wire             en,      // Shift enable (holds when low)
    output reg  [WIDTH-1:0] q        // LFSR register state
);

    always @(posedge clk) begin
        if (!rst_n) begin
            q <= INIT[WIDTH-1:0];
        end else begin
            if (en) begin
                q <= {(((q[15] ^ q[14]) ^ q[12]) ^ q[3]), q[WIDTH-1:1]};
            end
        end
    end

endmodule
