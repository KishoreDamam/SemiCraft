// SemiCraft v0.4.0
// Snippet: sync_ram (config hash: f3c56bc88039)
// 256 x 8-bit simple dual-port synchronous RAM
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram (
    input  wire       clk,     // Clock; the only timing input
    input  wire [7:0] waddr,   // Write address
    input  wire       we,      // Write enable
    input  wire [7:0] din,     // Write data
    input  wire [7:0] raddr,   // Read address
    output reg  [7:0] dout     // Registered read data, valid the next cycle
);

    reg [7:0] mem [0:255];  // Storage array; never reset

    always @(posedge clk) begin
        if (we) begin
            mem[waddr] <= din;
        end
        dout <= mem[raddr];
    end

endmodule
