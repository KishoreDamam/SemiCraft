// SemiCraft v0.1.0
// Snippet: lfsr (config hash: 6e7aa99607fa)
// 32-bit Fibonacci LFSR, parallel output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter int unsigned WIDTH = 32,
    parameter int unsigned INIT = {{(WIDTH-1){1'b0}}, 1'b1}
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    input  logic             en,      // Shift enable (holds when low)
    output logic [WIDTH-1:0] q        // LFSR register state
);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            q <= INIT;
        end else begin
            if (en) begin
                q <= {(((q[31] ^ q[21]) ^ q[1]) ^ q[0]), q[WIDTH-1:1]};
            end
        end
    end

endmodule
