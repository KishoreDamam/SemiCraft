// SemiCraft v0.1.0
// Snippet: edge_detector (config hash: c50e77408e48)
// Rising-edge detector, 8-bit one-cycle pulse
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module edge_detector #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Sync reset, active-low
    input  logic [WIDTH-1:0] d,       // Input signal to detect edges on
    output logic [WIDTH-1:0] pulse    // One-cycle rising-edge pulse (registered output)
);

    logic [WIDTH-1:0] d_q;  // Previous-cycle value of d (delay register)

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            d_q <= {WIDTH{1'b0}};
            pulse <= {WIDTH{1'b0}};
        end else begin
            d_q <= d;
            pulse <= d & (~d_q);
        end
    end

endmodule
