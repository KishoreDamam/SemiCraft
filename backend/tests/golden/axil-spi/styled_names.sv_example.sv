// SemiCraft v0.4.0
// Example instantiation: axil_spi (config hash: bea2ab0054b1)
// An AXI4-Lite SPI master in mode 00.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_spi_example (
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
    input  logic        p_miso,
    output logic        p_sclk,
    output logic        p_mosi,
    output logic        p_csN
);

    axil_spi u_axil_spi (
        // Clocking
        .p_aclk     (p_aclk),
        .p_areset_n (p_areset_n),
        // AXI4-Lite slave (bundle `s_axil`, axi4-lite target)
        .p_awaddr   (p_awaddr),
        .p_awvalid  (p_awvalid),
        .p_awready  (p_awready),
        .p_wdata    (p_wdata),
        .p_wstrb    (p_wstrb),
        .p_wvalid   (p_wvalid),
        .p_wready   (p_wready),
        .p_bresp    (p_bresp),
        .p_bvalid   (p_bvalid),
        .p_bready   (p_bready),
        .p_araddr   (p_araddr),
        .p_arvalid  (p_arvalid),
        .p_arready  (p_arready),
        .p_rdata    (p_rdata),
        .p_rresp    (p_rresp),
        .p_rvalid   (p_rvalid),
        .p_rready   (p_rready),
        // SPI link (bundle `spi`, spi initiator)
        .p_sclk     (p_sclk),
        .p_mosi     (p_mosi),
        .p_miso     (p_miso),
        .p_csN      (p_csN)
    );

endmodule
