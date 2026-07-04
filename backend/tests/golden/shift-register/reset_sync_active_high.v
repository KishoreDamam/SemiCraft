// SemiCraft v0.1.0
// Snippet: shift_register (config hash: cd8e2db10526)
// Right-shifting shift register, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module shift_register #(
    parameter DEPTH = 8
) (
    input  wire             clk,   // Clock
    input  wire             rst,   // Sync reset, active-high
    input  wire             en,    // Shift/load enable (holds when low)
    input  wire             si,    // Serial input
    output reg  [DEPTH-1:0] q,     // Parallel shift-register contents
    output wire             so     // Serial output, taps the LSB (q[0])
);

    always @(posedge clk) begin
        if (rst) begin
            q <= {DEPTH{1'b0}};
        end else begin
            if (en) begin
                q <= {si, q[DEPTH-1:1]};
            end
        end
    end

    assign so = q[0:0];

endmodule
