// SemiCraft v0.4.0
// Snippet: encoder (config hash: c3cd05f89eff)
// Priority encoder, 8 inputs
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module encoder #(
    parameter int unsigned NUM_INPUTS = 8
) (
    input  logic [NUM_INPUTS-1:0] p_din,    // 8-bit input vector
    output logic [OUT_WIDTH-1:0]  p_dout,   // Encoded index output
    output logic                  p_valid   // High when dout reflects a valid encoded input
);

    localparam int unsigned OUT_WIDTH = 3;

    always_comb begin
        // Priority encoder: highest-indexed set bit wins (din[7] is highest priority, din[0] is lowest priority).
        p_dout = {OUT_WIDTH{1'b0}};
        p_valid = 1'b0;
        if (p_din[7]) begin
            p_dout = {{(OUT_WIDTH-3){1'b0}}, 3'b111};
            p_valid = 1'b1;
        end else if (p_din[6]) begin
            p_dout = {{(OUT_WIDTH-3){1'b0}}, 3'b110};
            p_valid = 1'b1;
        end else if (p_din[5]) begin
            p_dout = {{(OUT_WIDTH-3){1'b0}}, 3'b101};
            p_valid = 1'b1;
        end else if (p_din[4]) begin
            p_dout = {{(OUT_WIDTH-3){1'b0}}, 3'b100};
            p_valid = 1'b1;
        end else if (p_din[3]) begin
            p_dout = {{(OUT_WIDTH-2){1'b0}}, 2'b11};
            p_valid = 1'b1;
        end else if (p_din[2]) begin
            p_dout = {{(OUT_WIDTH-2){1'b0}}, 2'b10};
            p_valid = 1'b1;
        end else if (p_din[1]) begin
            p_dout = {{(OUT_WIDTH-1){1'b0}}, 1'b1};
            p_valid = 1'b1;
        end else if (p_din[0]) begin
            p_dout = {OUT_WIDTH{1'b0}};
            p_valid = 1'b1;
        end
    end

endmodule
