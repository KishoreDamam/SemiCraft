// SemiCraft v0.4.0
// Snippet: lfsr (config hash: 5a438ef873db)
// 8-bit Fibonacci LFSR, parallel output
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module lfsr #(
    parameter int unsigned WIDTH = 8,
    parameter int unsigned INIT = 1
) (
    input  logic             p_clk,     // Clock
    input  logic             p_rst_n,   // Sync reset, active-low
    input  logic             p_en,      // Shift enable (holds when low)
    output logic [WIDTH-1:0] p_q        // LFSR register state
);

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_q <= INIT[WIDTH-1:0];
        end else begin
            if (p_en) begin
                p_q <= {(((p_q[7] ^ p_q[5]) ^ p_q[4]) ^ p_q[3]), p_q[WIDTH-1:1]};
            end
        end
    end

endmodule
