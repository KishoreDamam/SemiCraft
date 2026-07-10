// SemiCraft v0.1.0
// Snippet: lfsr (config hash: 898dfab59083)
// 32-bit Fibonacci LFSR, serial output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter WIDTH = 32,
    parameter INIT = 1
) (
    input  wire clk,     // Clock
    input  wire rst_n,   // Sync reset, active-low
    output wire out      // Combinational feedback bit (XOR of the tap bits of the current state)
);

    reg [WIDTH-1:0] q;  // Internal LFSR register state (no parallel output port)

    always @(posedge clk) begin
        if (!rst_n) begin
            q <= INIT[WIDTH-1:0];
        end else begin
            q <= {(((q[31] ^ q[21]) ^ q[1]) ^ q[0]), q[WIDTH-1:1]};
        end
    end

    assign out = q[0];

endmodule
