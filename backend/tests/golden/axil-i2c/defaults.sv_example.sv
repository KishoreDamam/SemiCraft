// SemiCraft v0.4.0
// Example instantiation: axil_i2c (config hash: 240d428184ad)
// An open-drain AXI4-Lite I2C master.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module axil_i2c_example (
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
    input  logic        scl_in,
    input  logic        sda_in,
    output logic        scl_oe,
    output logic        sda_oe
);

    axil_i2c u_axil_i2c (
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
        // I2C bus (bundle `i2c`, i2c initiator)
        .scl_in   (scl_in),
        .sda_in   (sda_in),
        .scl_oe   (scl_oe),
        .sda_oe   (sda_oe)
    );

endmodule
