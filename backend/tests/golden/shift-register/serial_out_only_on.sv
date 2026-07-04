// SemiCraft v0.1.0
// Snippet: shift_register (config hash: b43abf711509)
// Right-shifting shift register, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module shift_register #(
    parameter int unsigned DEPTH = 8
) (
    input  logic clk,     // Clock
    input  logic rst_n,   // Sync reset, active-low
    input  logic en,      // Shift/load enable (holds when low)
    input  logic si,      // Serial input
    output logic so       // Serial output, taps the LSB (q[0])
);

    logic [DEPTH-1:0] q;  // Internal shift-register state (no parallel output port)

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            q <= {DEPTH{1'b0}};
        end else begin
            if (en) begin
                q <= {si, q[DEPTH-1:1]};
            end
        end
    end

    assign so = q[0:0];

endmodule
