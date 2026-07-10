// SemiCraft v0.1.0
// Snippet: lfsr (config hash: 37d97d337f4e)
// 8-bit Fibonacci LFSR, parallel output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter int unsigned WIDTH = 8,
    parameter int unsigned INIT = 1
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    input  logic             en,      // Shift enable (holds when low)
    output logic [WIDTH-1:0] q        // LFSR register state
);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            q <= INIT[WIDTH-1:0];
        end else begin
            if (en) begin
                q <= {(((q[7] ^ q[5]) ^ q[4]) ^ q[3]), q[WIDTH-1:1]};
            end
        end
    end

endmodule
