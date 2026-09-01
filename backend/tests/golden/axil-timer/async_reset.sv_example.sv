// SemiCraft v0.4.0
// Example instantiation: axil_timer (config hash: a8fc26c779ca)
// An AXI4-Lite timer with a 32-bit down-counter and a 16-bit prescaler, running one-shot or periodically and raising a maskable interrupt on expiry.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_timer_example (
    input  logic        aclk,
    input  logic        areset_n,
    input  logic [4:0]  awaddr,
    input  logic        awvalid,
    output logic        awready,
    input  logic [31:0] wdata,
    input  logic [3:0]  wstrb,
    input  logic        wvalid,
    output logic        wready,
    output logic [1:0]  bresp,
    output logic        bvalid,
    input  logic        bready,
    input  logic [4:0]  araddr,
    input  logic        arvalid,
    output logic        arready,
    output logic [31:0] rdata,
    output logic [1:0]  rresp,
    output logic        rvalid,
    input  logic        rready,
    output logic        irq
);

    axil_timer u_axil_timer (
        // Clocking
        .aclk     (aclk),
        .areset_n (areset_n),
        // AXI4-Lite slave (bundle `s_axil`, axi4-lite target)
        .awaddr   (awaddr),
        .awvalid  (awvalid),
        .awready  (awready),
        .wdata    (wdata),
        .wstrb    (wstrb),
        .wvalid   (wvalid),
        .wready   (wready),
        .bresp    (bresp),
        .bvalid   (bvalid),
        .bready   (bready),
        .araddr   (araddr),
        .arvalid  (arvalid),
        .arready  (arready),
        .rdata    (rdata),
        .rresp    (rresp),
        .rvalid   (rvalid),
        .rready   (rready),
        // Interrupt
        .irq      (irq)
    );

endmodule
