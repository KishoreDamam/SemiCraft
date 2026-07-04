// SemiCraft v0.1.0
// Snippet: shift_register (config hash: 97c59c47a644)
// Right-shifting shift register, 16-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module shift_register #(
    parameter DEPTH = 16
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    input  wire             en,      // Shift/load enable (holds when low)
    input  wire             si,      // Serial input
    output reg  [DEPTH-1:0] q,       // Parallel shift-register contents
    output wire             so       // Serial output, taps the LSB (q[0])
);

    always @(posedge clk) begin
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
