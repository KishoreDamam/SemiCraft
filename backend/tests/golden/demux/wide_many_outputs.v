// SemiCraft v0.1.0
// Snippet: demux (config hash: 81449dcc3e2c)
// 16-way demultiplexer, 32-bit data
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module demux #(
    parameter WIDTH = 32
) (
    input  wire [WIDTH-1:0]     din,     // Data input routed to the selected output
    input  wire [SEL_WIDTH-1:0] sel,     // Output select (4-bit; chooses out0..out15)
    output reg  [WIDTH-1:0]     out0,    // Demultiplexed output 0; driven by din when sel == 0, else zero
    output reg  [WIDTH-1:0]     out1,    // Demultiplexed output 1; driven by din when sel == 1, else zero
    output reg  [WIDTH-1:0]     out2,    // Demultiplexed output 2; driven by din when sel == 2, else zero
    output reg  [WIDTH-1:0]     out3,    // Demultiplexed output 3; driven by din when sel == 3, else zero
    output reg  [WIDTH-1:0]     out4,    // Demultiplexed output 4; driven by din when sel == 4, else zero
    output reg  [WIDTH-1:0]     out5,    // Demultiplexed output 5; driven by din when sel == 5, else zero
    output reg  [WIDTH-1:0]     out6,    // Demultiplexed output 6; driven by din when sel == 6, else zero
    output reg  [WIDTH-1:0]     out7,    // Demultiplexed output 7; driven by din when sel == 7, else zero
    output reg  [WIDTH-1:0]     out8,    // Demultiplexed output 8; driven by din when sel == 8, else zero
    output reg  [WIDTH-1:0]     out9,    // Demultiplexed output 9; driven by din when sel == 9, else zero
    output reg  [WIDTH-1:0]     out10,   // Demultiplexed output 10; driven by din when sel == 10, else zero
    output reg  [WIDTH-1:0]     out11,   // Demultiplexed output 11; driven by din when sel == 11, else zero
    output reg  [WIDTH-1:0]     out12,   // Demultiplexed output 12; driven by din when sel == 12, else zero
    output reg  [WIDTH-1:0]     out13,   // Demultiplexed output 13; driven by din when sel == 13, else zero
    output reg  [WIDTH-1:0]     out14,   // Demultiplexed output 14; driven by din when sel == 14, else zero
    output reg  [WIDTH-1:0]     out15    // Demultiplexed output 15; driven by din when sel == 15, else zero
);

    localparam SEL_WIDTH = 4;

    always @(*) begin
        out0 = {WIDTH{1'b0}};
        out1 = {WIDTH{1'b0}};
        out2 = {WIDTH{1'b0}};
        out3 = {WIDTH{1'b0}};
        out4 = {WIDTH{1'b0}};
        out5 = {WIDTH{1'b0}};
        out6 = {WIDTH{1'b0}};
        out7 = {WIDTH{1'b0}};
        out8 = {WIDTH{1'b0}};
        out9 = {WIDTH{1'b0}};
        out10 = {WIDTH{1'b0}};
        out11 = {WIDTH{1'b0}};
        out12 = {WIDTH{1'b0}};
        out13 = {WIDTH{1'b0}};
        out14 = {WIDTH{1'b0}};
        out15 = {WIDTH{1'b0}};
        case (sel)
            {SEL_WIDTH{1'b0}}: out0 = din;
            {{(SEL_WIDTH-1){1'b0}}, 1'b1}: out1 = din;
            {{(SEL_WIDTH-2){1'b0}}, 2'b10}: out2 = din;
            {{(SEL_WIDTH-2){1'b0}}, 2'b11}: out3 = din;
            {{(SEL_WIDTH-3){1'b0}}, 3'b100}: out4 = din;
            {{(SEL_WIDTH-3){1'b0}}, 3'b101}: out5 = din;
            {{(SEL_WIDTH-3){1'b0}}, 3'b110}: out6 = din;
            {{(SEL_WIDTH-3){1'b0}}, 3'b111}: out7 = din;
            {{(SEL_WIDTH-4){1'b0}}, 4'b1000}: out8 = din;
            {{(SEL_WIDTH-4){1'b0}}, 4'b1001}: out9 = din;
            {{(SEL_WIDTH-4){1'b0}}, 4'b1010}: out10 = din;
            {{(SEL_WIDTH-4){1'b0}}, 4'b1011}: out11 = din;
            {{(SEL_WIDTH-4){1'b0}}, 4'b1100}: out12 = din;
            {{(SEL_WIDTH-4){1'b0}}, 4'b1101}: out13 = din;
            {{(SEL_WIDTH-4){1'b0}}, 4'b1110}: out14 = din;
            {{(SEL_WIDTH-4){1'b0}}, 4'b1111}: out15 = din;
            default: ;
        endcase
    end

endmodule
