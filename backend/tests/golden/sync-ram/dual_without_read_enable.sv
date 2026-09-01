// SemiCraft v0.4.0
// Snippet: sync_ram (config hash: 3744a15536c5)
// 256 x 8-bit simple dual-port synchronous RAM
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram (
    input  logic       clk,     // Clock; the only timing input
    input  logic [7:0] waddr,   // Write address
    input  logic       we,      // Write enable
    input  logic [7:0] din,     // Write data
    input  logic [7:0] raddr,   // Read address
    output logic [7:0] dout     // Registered read data, valid the next cycle
);

    logic [7:0] mem [256];  // Storage array; never reset

    always_ff @(posedge clk) begin
        if (we) begin
            mem[waddr] <= din;
        end
        dout <= mem[raddr];
    end

endmodule
