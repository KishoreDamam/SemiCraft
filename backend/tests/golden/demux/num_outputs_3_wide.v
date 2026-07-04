// SemiCraft v0.1.0
// Snippet: demux (config hash: 5a12b6c3ee37)
// 3-way demultiplexer, 32-bit data
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module demux #(
    parameter WIDTH = 32
) (
    input  wire [WIDTH-1:0]     din,    // Data input routed to the selected output
    input  wire [SEL_WIDTH-1:0] sel,    // Output select (2-bit; chooses out0..out2)
    output reg  [WIDTH-1:0]     out0,   // Demultiplexed output 0; driven by din when sel == 0, else zero
    output reg  [WIDTH-1:0]     out1,   // Demultiplexed output 1; driven by din when sel == 1, else zero
    output reg  [WIDTH-1:0]     out2    // Demultiplexed output 2; driven by din when sel == 2, else zero
);

    localparam SEL_WIDTH = 2;

    always @(*) begin
        out0 = {WIDTH{1'b0}};
        out1 = {WIDTH{1'b0}};
        out2 = {WIDTH{1'b0}};
        case (sel)
            {SEL_WIDTH{1'b0}}: out0 = din;
            {{(SEL_WIDTH-1){1'b0}}, 1'b1}: out1 = din;
            {{(SEL_WIDTH-2){1'b0}}, 2'b10}: out2 = din;
            default: ;
        endcase
    end

endmodule
