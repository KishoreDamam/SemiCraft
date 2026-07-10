// SemiCraft v0.1.0
// Snippet: lfsr (config hash: 99427475f265)
// 32-bit Fibonacci LFSR, serial output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter int unsigned WIDTH = 32,
    parameter int unsigned INIT = 1
) (
    input  logic clk,     // Clock
    input  logic rst_n,   // Sync reset, active-low
    output logic out      // Combinational feedback bit (XOR of the tap bits of the current state)
);

    logic [WIDTH-1:0] q;  // Internal LFSR register state (no parallel output port)

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            q <= INIT[WIDTH-1:0];
        end else begin
            q <= {(((q[31] ^ q[21]) ^ q[1]) ^ q[0]), q[WIDTH-1:1]};
        end
    end

    assign out = q[0];

endmodule
