// SemiCraft v0.4.0
// Example instantiation: axil_regblock (config hash: 9e0a82cbd583)
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
    input  logic        p_aclk,
    input  logic        p_areset_n,
    input  logic [4:0]  p_awaddr,
    input  logic        p_awvalid,
    output logic        p_awready,
    input  logic [31:0] p_wdata,
    input  logic [3:0]  p_wstrb,
    input  logic        p_wvalid,
    output logic        p_wready,
    output logic [1:0]  p_bresp,
    output logic        p_bvalid,
    input  logic        p_bready,
    input  logic [4:0]  p_araddr,
    input  logic        p_arvalid,
    output logic        p_arready,
    output logic [31:0] p_rdata,
    output logic [1:0]  p_rresp,
    output logic        p_rvalid,
    input  logic        p_rready,
    output logic        p_ctrl0Enable,
    output logic [1:0]  p_ctrl0Mode,
    output logic [3:0]  p_ctrl0Level,
    input  logic        p_status0Busy,
    input  logic [3:0]  p_status0Code,
    output logic [3:0]  p_irq0Flags,
    input  logic [3:0]  p_irq0FlagsSet,
    output logic        p_cmd0Go,
    output logic [2:0]  p_cmd0Code,
    output logic [31:0] p_scratchValue
);

    axil_regblock u_axil_regblock (
        // Clocking
        .p_aclk         (p_aclk),
        .p_areset_n     (p_areset_n),
        // AXI4-Lite slave (bundle `s_axil`, axi4-lite target)
        .p_awaddr       (p_awaddr),
        .p_awvalid      (p_awvalid),
        .p_awready      (p_awready),
        .p_wdata        (p_wdata),
        .p_wstrb        (p_wstrb),
        .p_wvalid       (p_wvalid),
        .p_wready       (p_wready),
        .p_bresp        (p_bresp),
        .p_bvalid       (p_bvalid),
        .p_bready       (p_bready),
        .p_araddr       (p_araddr),
        .p_arvalid      (p_arvalid),
        .p_arready      (p_arready),
        .p_rdata        (p_rdata),
        .p_rresp        (p_rresp),
        .p_rvalid       (p_rvalid),
        .p_rready       (p_rready),
        // Hardware face
        .p_ctrl0Enable  (p_ctrl0Enable),
        .p_ctrl0Mode    (p_ctrl0Mode),
        .p_ctrl0Level   (p_ctrl0Level),
        .p_status0Busy  (p_status0Busy),
        .p_status0Code  (p_status0Code),
        .p_irq0Flags    (p_irq0Flags),
        .p_irq0FlagsSet (p_irq0FlagsSet),
        .p_cmd0Go       (p_cmd0Go),
        .p_cmd0Code     (p_cmd0Code),
        .p_scratchValue (p_scratchValue)
    );

endmodule
