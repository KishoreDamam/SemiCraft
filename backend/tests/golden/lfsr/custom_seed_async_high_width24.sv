// SemiCraft v0.1.0
// Snippet: lfsr (config hash: 81c4bc40fac4)
// 24-bit Fibonacci LFSR, parallel output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter int unsigned WIDTH = 24,
    parameter int unsigned INIT = 11259361
) (
    input  logic             clk,   // Clock
    input  logic             rst,   // Async reset, active-high
    input  logic             en,    // Shift enable (holds when low)
    output logic [WIDTH-1:0] q      // LFSR register state
);

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            q <= INIT[WIDTH-1:0];
        end else begin
            if (en) begin
                q <= {(((q[23] ^ q[22]) ^ q[21]) ^ q[16]), q[WIDTH-1:1]};
            end
        end
    end

endmodule
