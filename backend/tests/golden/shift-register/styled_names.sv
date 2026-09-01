// SemiCraft v0.4.0
// Snippet: shift_register (config hash: 28e0fd1f8233)
// Right-shifting shift register, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module shift_register #(
    parameter int unsigned DEPTH = 8
) (
    input  logic             p_clk,     // Clock
    input  logic             p_rst_n,   // Sync reset, active-low
    input  logic             p_en,      // Shift/load enable (holds when low)
    input  logic             p_si,      // Serial input
    output logic [DEPTH-1:0] p_q,       // Parallel shift-register contents
    output logic             p_so       // Serial output, taps the LSB (q[0])
);

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_q <= {DEPTH{1'b0}};
        end else begin
            if (p_en) begin
                p_q <= {p_si, p_q[DEPTH-1:1]};
            end
        end
    end

    assign p_so = p_q[0:0];

endmodule
