// SemiCraft v0.1.0
// Snippet: encoder (config hash: 5f16885ada76)
// Priority encoder, 4 inputs
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module encoder #(
    parameter int unsigned NUM_INPUTS = 4
) (
    input  logic [NUM_INPUTS-1:0] din,    // 4-bit input vector
    output logic [OUT_WIDTH-1:0]  dout,   // Encoded index output
    output logic                  valid   // High when dout reflects a valid encoded input
);

    localparam int unsigned OUT_WIDTH = 2;

    always_comb begin
        // Priority encoder: highest-indexed set bit wins (din[3] is highest priority, din[0] is lowest priority).
        dout = {OUT_WIDTH{1'b0}};
        valid = 1'b0;
        if (din[3]) begin
            dout = {{(OUT_WIDTH-2){1'b0}}, 2'b11};
            valid = 1'b1;
        end else if (din[2]) begin
            dout = {{(OUT_WIDTH-2){1'b0}}, 2'b10};
            valid = 1'b1;
        end else if (din[1]) begin
            dout = {{(OUT_WIDTH-1){1'b0}}, 1'b1};
            valid = 1'b1;
        end else if (din[0]) begin
            dout = {OUT_WIDTH{1'b0}};
            valid = 1'b1;
        end
    end

endmodule
