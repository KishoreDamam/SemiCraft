// SemiCraft v0.3.0
// Snippet: sync_ram (config hash: a97e5ce17e8a)
// 256 x 8-bit single-port synchronous RAM
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram (
    input  logic       clk,    // Clock; the only timing input
    input  logic [7:0] addr,   // Shared read/write address
    input  logic       we,     // Write enable
    input  logic [7:0] din,    // Write data
    output logic [7:0] dout    // Registered read data, valid the next cycle
);

    logic [7:0] mem [256];  // Storage array; never reset

    always_ff @(posedge clk) begin
        if (we) begin
            mem[addr] <= din;
        end
        dout <= mem[addr];
    end

endmodule
