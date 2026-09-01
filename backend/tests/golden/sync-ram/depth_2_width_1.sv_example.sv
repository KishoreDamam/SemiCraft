// SemiCraft v0.4.0
// Example instantiation: sync_ram (config hash: cba02084b546)
// A 2-word by 1-bit synchronous RAM in single-port configuration.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram_example (
    input  logic  clk,
    input  logic  addr,
    input  logic  we,
    input  logic  din,
    input  logic  re,
    output logic  dout
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
