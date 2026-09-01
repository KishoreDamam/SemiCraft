// SemiCraft v0.4.0
// Snippet: demux (config hash: effa6035a4e5)
// 4-way demultiplexer, 8-bit data
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module demux #(
    parameter int unsigned WIDTH = 8
) (
    input  logic [WIDTH-1:0]     p_din,    // Data input routed to the selected output
    input  logic [SEL_WIDTH-1:0] p_sel,    // Output select (2-bit; chooses out0..out3)
    output logic [WIDTH-1:0]     p_out0,   // Demultiplexed output 0; driven by din when sel == 0, else zero
    output logic [WIDTH-1:0]     p_out1,   // Demultiplexed output 1; driven by din when sel == 1, else zero
    output logic [WIDTH-1:0]     p_out2,   // Demultiplexed output 2; driven by din when sel == 2, else zero
    output logic [WIDTH-1:0]     p_out3    // Demultiplexed output 3; driven by din when sel == 3, else zero
);

    localparam int unsigned SEL_WIDTH = 2;

    always_comb begin
        p_out0 = {WIDTH{1'b0}};
        p_out1 = {WIDTH{1'b0}};
        p_out2 = {WIDTH{1'b0}};
        p_out3 = {WIDTH{1'b0}};
        case (p_sel)
            {SEL_WIDTH{1'b0}}: p_out0 = p_din;
            {{(SEL_WIDTH-1){1'b0}}, 1'b1}: p_out1 = p_din;
            {{(SEL_WIDTH-2){1'b0}}, 2'b10}: p_out2 = p_din;
            {{(SEL_WIDTH-2){1'b0}}, 2'b11}: p_out3 = p_din;
            default: ;
        endcase
    end

endmodule
