// SemiCraft v0.4.0
// Snippet: sync_ram (config hash: 9e0ede76a0d6)
// 256 x 8-bit single-port synchronous RAM
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram (
    input  logic       p_clk,    // Clock; the only timing input
    input  logic [7:0] p_addr,   // Shared read/write address
    input  logic       p_we,     // Write enable
    input  logic [7:0] p_din,    // Write data
    input  logic       p_re,     // Read enable; dout holds when low
    output logic [7:0] p_dout    // Registered read data, valid the next cycle
);

    logic [7:0] p_mem [256];  // Storage array; never reset

    always_ff @(posedge p_clk) begin
        if (p_we) begin
            p_mem[p_addr] <= p_din;
        end
        if (p_re) begin
            p_dout <= p_mem[p_addr];
        end
    end

endmodule
