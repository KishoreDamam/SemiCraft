// SemiCraft v0.4.0
// Example instantiation: sync_ram (config hash: 9e0ede76a0d6)
// A 256-word by 8-bit synchronous RAM in single-port configuration.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram_example (
    input  logic       p_clk,
    input  logic [7:0] p_addr,
    input  logic       p_we,
    input  logic [7:0] p_din,
    input  logic       p_re,
    output logic [7:0] p_dout
);

    sync_ram u_sync_ram (
        // Clocking
        .p_clk  (p_clk),
        // Write port (bundle `mem`, sram-single target)
        .p_addr (p_addr),
        .p_we   (p_we),
        .p_din  (p_din),
        // Read port (bundle `mem`, sram-single target)
        .p_re   (p_re),
        .p_dout (p_dout)
    );

endmodule
