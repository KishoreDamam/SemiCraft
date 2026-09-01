// SemiCraft v0.4.0
// Example instantiation: sync_ram (config hash: 3744a15536c5)
// A 256-word by 8-bit synchronous RAM in simple dual-port configuration.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_ram_example (
    input  logic       clk,
    input  logic [7:0] waddr,
    input  logic       we,
    input  logic [7:0] din,
    input  logic [7:0] raddr,
    output logic [7:0] dout
);

    sync_ram u_sync_ram (
        // Clocking
        .clk   (clk),
        // Write port (bundle `wr`, sram-write target)
        .waddr (waddr),
        .we    (we),
        .din   (din),
        // Read port (bundle `rd`, sram-read target)
        .raddr (raddr),
        .dout  (dout)
    );

endmodule
