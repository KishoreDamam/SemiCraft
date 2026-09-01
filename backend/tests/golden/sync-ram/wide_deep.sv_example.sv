// SemiCraft v0.4.0
// Example instantiation: sync_ram (config hash: 579a52f3bde7)
// A 1024-word by 64-bit synchronous RAM in single-port configuration.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram_example (
    input  logic        clk,
    input  logic [9:0]  addr,
    input  logic        we,
    input  logic [63:0] din,
    input  logic        re,
    output logic [63:0] dout
);

    sync_ram u_sync_ram (
        // Clocking
        .clk  (clk),
        // Write port (bundle `mem`, sram-single target)
        .addr (addr),
        .we   (we),
        .din  (din),
        // Read port (bundle `mem`, sram-single target)
        .re   (re),
        .dout (dout)
    );

endmodule
