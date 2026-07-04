// SemiCraft v0.1.0
// Snippet: encoder (config hash: 372338a0e179)
// Priority encoder, 16 inputs
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module encoder #(
    parameter int unsigned NUM_INPUTS = 16
) (
    input  logic [NUM_INPUTS-1:0] din,    // 16-bit input vector
    output logic [OUT_WIDTH-1:0]  dout,   // Encoded index output
    output logic                  valid   // High when dout reflects a valid encoded input
);

    localparam int unsigned OUT_WIDTH = 4;

    always_comb begin
        // Priority encoder: highest-indexed set bit wins (din[15] is highest priority, din[0] is lowest priority).
        dout = {OUT_WIDTH{1'b0}};
        valid = 1'b0;
        if (din[15]) begin
            dout = {{(OUT_WIDTH-4){1'b0}}, 4'b1111};
            valid = 1'b1;
        end else if (din[14]) begin
            dout = {{(OUT_WIDTH-4){1'b0}}, 4'b1110};
            valid = 1'b1;
        end else if (din[13]) begin
            dout = {{(OUT_WIDTH-4){1'b0}}, 4'b1101};
            valid = 1'b1;
        end else if (din[12]) begin
            dout = {{(OUT_WIDTH-4){1'b0}}, 4'b1100};
            valid = 1'b1;
        end else if (din[11]) begin
            dout = {{(OUT_WIDTH-4){1'b0}}, 4'b1011};
            valid = 1'b1;
        end else if (din[10]) begin
            dout = {{(OUT_WIDTH-4){1'b0}}, 4'b1010};
            valid = 1'b1;
        end else if (din[9]) begin
            dout = {{(OUT_WIDTH-4){1'b0}}, 4'b1001};
            valid = 1'b1;
        end else if (din[8]) begin
            dout = {{(OUT_WIDTH-4){1'b0}}, 4'b1000};
            valid = 1'b1;
        end else if (din[7]) begin
            dout = {{(OUT_WIDTH-3){1'b0}}, 3'b111};
            valid = 1'b1;
        end else if (din[6]) begin
            dout = {{(OUT_WIDTH-3){1'b0}}, 3'b110};
            valid = 1'b1;
        end else if (din[5]) begin
            dout = {{(OUT_WIDTH-3){1'b0}}, 3'b101};
            valid = 1'b1;
        end else if (din[4]) begin
            dout = {{(OUT_WIDTH-3){1'b0}}, 3'b100};
            valid = 1'b1;
        end else if (din[3]) begin
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
