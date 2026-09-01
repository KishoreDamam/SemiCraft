// SemiCraft v0.4.0
// Snippet: sync_ram (config hash: 579a52f3bde7)
// 1024 x 64-bit single-port synchronous RAM
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram (
    input  logic        clk,    // Clock; the only timing input
    input  logic [9:0]  addr,   // Shared read/write address
    input  logic        we,     // Write enable
    input  logic [63:0] din,    // Write data
    input  logic        re,     // Read enable; dout holds when low
    output logic [63:0] dout    // Registered read data, valid the next cycle
);

    logic [63:0] mem [1024];  // Storage array; never reset

    always_ff @(posedge clk) begin
        if (we) begin
            mem[addr] <= din;
        end
        if (re) begin
            dout <= mem[addr];
        end
    end

endmodule
