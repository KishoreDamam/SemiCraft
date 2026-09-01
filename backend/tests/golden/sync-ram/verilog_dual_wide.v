// SemiCraft v0.4.0
// Snippet: sync_ram (config hash: a20114503dbf)
// 4096 x 32-bit simple dual-port synchronous RAM
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram (
    input  wire        clk,     // Clock; the only timing input
    input  wire [11:0] waddr,   // Write address
    input  wire        we,      // Write enable
    input  wire [31:0] din,     // Write data
    input  wire [11:0] raddr,   // Read address
    input  wire        re,      // Read enable; dout holds when low
    output reg  [31:0] dout     // Registered read data, valid the next cycle
);

    reg [31:0] mem [0:4095];  // Storage array; never reset

    always @(posedge clk) begin
        if (we) begin
            mem[waddr] <= din;
        end
        if (re) begin
            dout <= mem[raddr];
        end
    end

endmodule
