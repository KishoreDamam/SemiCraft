// SemiCraft v0.4.0
// Example instantiation: sync_ram (config hash: f3c56bc88039)
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
    input  wire       clk,
    input  wire [7:0] waddr,
    input  wire       we,
    input  wire [7:0] din,
    input  wire [7:0] raddr,
    output wire [7:0] dout
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
