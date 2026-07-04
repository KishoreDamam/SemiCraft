// SemiCraft v0.1.0
// Snippet: shift_register (config hash: 312c53a89925)
// Left-shifting shift register, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module shift_register #(
    parameter DEPTH = 8
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    input  wire             en,      // Shift/load enable (holds when low)
    input  wire             load,    // Parallel load (beats shift)
    input  wire [DEPTH-1:0] d,       // Parallel load data, DEPTH bits wide
    input  wire             si,      // Serial input
    output reg  [DEPTH-1:0] q,       // Parallel shift-register contents
    output wire             so       // Serial output, taps the MSB (q[DEPTH-1])
);

    always @(posedge clk) begin
        if (!rst_n) begin
            q <= {DEPTH{1'b0}};
        end else begin
            if (en) begin
                if (load) begin
                    q <= d;
                end else begin
                    q <= {q[DEPTH-2:0], si};
                end
            end
        end
    end

    assign so = q[DEPTH-1:DEPTH-1];

endmodule
