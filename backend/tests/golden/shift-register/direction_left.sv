// SemiCraft v0.1.0
// Snippet: shift_register (config hash: bd4cbdf0dd1f)
// Left-shifting shift register, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module shift_register #(
    parameter int unsigned DEPTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    input  logic             en,      // Shift/load enable (holds when low)
    input  logic             si,      // Serial input
    output logic [DEPTH-1:0] q,       // Parallel shift-register contents
    output logic             so       // Serial output, taps the MSB (q[DEPTH-1])
);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            q <= {DEPTH{1'b0}};
        end else begin
            if (en) begin
                q <= {q[DEPTH-2:0], si};
            end
        end
    end

    assign so = q[DEPTH-1:DEPTH-1];

endmodule
