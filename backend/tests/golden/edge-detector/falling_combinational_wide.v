// SemiCraft v0.1.0
// Snippet: edge_detector (config hash: 68bc694ab7d1)
// Falling-edge detector, 16-bit one-cycle pulse
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module edge_detector #(
    parameter WIDTH = 16
) (
    input  wire             clk,     // Clock
    input  wire             rst_n,   // Sync reset, active-low
    input  wire [WIDTH-1:0] d,       // Input signal to detect edges on
    output wire [WIDTH-1:0] pulse    // One-cycle falling-edge pulse (combinational output)
);

    reg [WIDTH-1:0] d_q;  // Previous-cycle value of d (delay register)

    always @(posedge clk) begin
        if (!rst_n) begin
            d_q <= {WIDTH{1'b0}};
        end else begin
            d_q <= d;
        end
    end

    assign pulse = (~d) & d_q;

endmodule
