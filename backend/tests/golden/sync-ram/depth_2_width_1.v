// SemiCraft v0.3.0
// Snippet: sync_ram (config hash: 4ce06443ea46)
// 2 x 1-bit single-port synchronous RAM
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram (
    input  wire       clk,    // Clock; the only timing input
    input  wire [0:0] addr,   // Shared read/write address
    input  wire       we,     // Write enable
    input  wire [0:0] din,    // Write data
    input  wire       re,     // Read enable; dout holds when low
    output reg  [0:0] dout    // Registered read data, valid the next cycle
);

    reg [0:0] mem [0:1];  // Storage array; never reset

    always @(posedge clk) begin
        if (we) begin
            mem[addr] <= din;
        end
        if (re) begin
            dout <= mem[addr];
        end
    end

endmodule
