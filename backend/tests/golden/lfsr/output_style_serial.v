// SemiCraft v0.1.0
// Snippet: lfsr (config hash: 18a744e704dc)
// 8-bit Fibonacci LFSR, serial output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter WIDTH = 8,
    parameter INIT = 1
) (
    input  wire clk,     // Clock
    input  wire rst_n,   // Sync reset, active-low
    input  wire en,      // Shift enable (holds when low)
    output wire out      // Combinational feedback bit (XOR of the tap bits of the current state)
);

    reg [WIDTH-1:0] q;  // Internal LFSR register state (no parallel output port)

    always @(posedge clk) begin
        if (!rst_n) begin
            q <= INIT[WIDTH-1:0];
        end else begin
            if (en) begin
                q <= {(((q[7] ^ q[5]) ^ q[4]) ^ q[3]), q[WIDTH-1:1]};
            end
        end
    end

    assign out = q[0];

endmodule
