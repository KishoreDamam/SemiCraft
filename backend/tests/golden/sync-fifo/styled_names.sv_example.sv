// SemiCraft v0.4.0
// Example instantiation: sync_fifo (config hash: aa4576c29109)
// A 8-entry, 8-bit synchronous FIFO.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_fifo_example (
    input  logic       p_clk,
    input  logic       p_rst_n,
    input  logic       p_wrEn,
    input  logic [7:0] p_wrData,
    output logic       p_full,
    input  logic       p_rdEn,
    output logic [7:0] p_rdData,
    output logic       p_empty,
    output logic [3:0] p_count
);

    sync_fifo u_sync_fifo (
        // Clocking
        .p_clk    (p_clk),
        .p_rst_n  (p_rst_n),
        // Write port (bundle `wr`, fifo-write target)
        .p_wrEn   (p_wrEn),
        .p_wrData (p_wrData),
        .p_full   (p_full),
        // Read port
        .p_rdEn   (p_rdEn),
        .p_rdData (p_rdData),
        .p_empty  (p_empty),
        .p_count  (p_count)
    );

endmodule
