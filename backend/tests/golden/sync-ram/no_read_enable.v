// SemiCraft v0.3.0
// Snippet: sync_ram (config hash: d7838913fc69)
// 256 x 8-bit single-port synchronous RAM
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram (
    input  wire       clk,    // Clock; the only timing input
    input  wire [7:0] addr,   // Shared read/write address
    input  wire       we,     // Write enable
    input  wire [7:0] din,    // Write data
    output reg  [7:0] dout    // Registered read data, valid the next cycle
);

    reg [7:0] mem [0:255];  // Storage array; never reset

    always @(posedge clk) begin
        if (we) begin
            mem[addr] <= din;
        end
        dout <= mem[addr];
    end

endmodule
