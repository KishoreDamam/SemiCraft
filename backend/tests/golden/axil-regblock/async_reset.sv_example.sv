// SemiCraft v0.4.0
// Example instantiation: axil_regblock (config hash: 7a463a042753)
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
    output logic        ctrl0_enable,
    output logic [1:0]  ctrl0_mode,
    output logic [3:0]  ctrl0_level,
    input  logic        status0_busy,
    input  logic [3:0]  status0_code,
    output logic [3:0]  irq0_flags,
    input  logic [3:0]  irq0_flags_set,
    output logic        cmd0_go,
    output logic [2:0]  cmd0_code,
    output logic [31:0] scratch_value
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
        .ctrl0_enable   (ctrl0_enable),
        .ctrl0_mode     (ctrl0_mode),
        .ctrl0_level    (ctrl0_level),
        .status0_busy   (status0_busy),
        .status0_code   (status0_code),
        .irq0_flags     (irq0_flags),
        .irq0_flags_set (irq0_flags_set),
        .cmd0_go        (cmd0_go),
        .cmd0_code      (cmd0_code),
        .scratch_value  (scratch_value)
    );

endmodule
