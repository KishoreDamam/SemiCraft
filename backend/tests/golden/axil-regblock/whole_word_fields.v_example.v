// SemiCraft v0.4.0
// Example instantiation: axil_regblock (config hash: 763ad261e462)
// An AXI4-Lite target that serves a register map: address decode, byte-strobe writes, per-access-type field behaviour, and a registered read path.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_regblock_example (
    input  wire        aclk,
    input  wire        areset_n,
    input  wire [4:0]  awaddr,
    input  wire        awvalid,
    output wire        awready,
    input  wire [31:0] wdata,
    input  wire [3:0]  wstrb,
    input  wire        wvalid,
    output wire        wready,
    output wire [1:0]  bresp,
    output wire        bvalid,
    input  wire        bready,
    input  wire [4:0]  araddr,
    input  wire        arvalid,
    output wire        arready,
    output wire [31:0] rdata,
    output wire [1:0]  rresp,
    output wire        rvalid,
    input  wire        rready,
    output wire [31:0] ctrl0_value,
    input  wire [31:0] status0_value,
    output wire [31:0] irq0_value,
    input  wire [31:0] irq0_value_set,
    output wire [31:0] cmd0_value,
    output wire [31:0] scratch_value
);

    axil_regblock u_axil_regblock (
        // Clocking
        .aclk           (aclk),
        .areset_n       (areset_n),
        // AXI4-Lite slave (bundle `s_axil`, axi4-lite target)
        .awaddr         (awaddr),
        .awvalid        (awvalid),
        .awready        (awready),
        .wdata          (wdata),
        .wstrb          (wstrb),
        .wvalid         (wvalid),
        .wready         (wready),
        .bresp          (bresp),
        .bvalid         (bvalid),
        .bready         (bready),
        .araddr         (araddr),
        .arvalid        (arvalid),
        .arready        (arready),
        .rdata          (rdata),
        .rresp          (rresp),
        .rvalid         (rvalid),
        .rready         (rready),
        // Hardware face
        .ctrl0_value    (ctrl0_value),
        .status0_value  (status0_value),
        .irq0_value     (irq0_value),
        .irq0_value_set (irq0_value_set),
        .cmd0_value     (cmd0_value),
        .scratch_value  (scratch_value)
    );

endmodule
