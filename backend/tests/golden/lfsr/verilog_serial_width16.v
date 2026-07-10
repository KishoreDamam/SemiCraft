// SemiCraft v0.1.0
// Snippet: lfsr (config hash: d5b18ee6212c)
// 16-bit Fibonacci LFSR, serial output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter WIDTH = 16,
    parameter INIT = {{(WIDTH-1){1'b0}}, 1'b1}
) (
    input  wire clk,     // Clock
    input  wire rst_n,   // Sync reset, active-low
    input  wire en,      // Shift enable (holds when low)
    output wire out      // Combinational feedback bit (XOR of the tap bits of the current state)
);

    reg [WIDTH-1:0] q;  // Internal LFSR register state (no parallel output port)

    always @(posedge clk) begin
        if (!rst_n) begin
            q <= INIT;
        end else begin
            if (en) begin
                q <= {(((q[15] ^ q[14]) ^ q[12]) ^ q[3]), q[WIDTH-1:1]};
            end
        end
    end

    assign out = ((q[15] ^ q[14]) ^ q[12]) ^ q[3];

endmodule
