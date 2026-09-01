// SemiCraft v0.4.0
// Example instantiation: axil_i2c (config hash: 932323353f5c)
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
    input  wire        scl_in,
    input  wire        sda_in,
    output wire        scl_oe,
    output wire        sda_oe
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
