// SemiCraft v0.4.0
// Example instantiation: sync_fifo (config hash: 9c7becf10bc8)
// A 16-entry, 64-bit synchronous FIFO.
//
// A compiling starting point, not an integration example: this wrapper
// passes every port straight through. Replace its ports with your own
// logic; what is guaranteed here is that the instantiation below is
// correct for this configuration and lints clean against the IP.
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module sync_fifo_example (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        wr_en,
    input  logic [63:0] wr_data,
    output logic        full,
    input  logic        rd_en,
    output logic [63:0] rd_data,
    output logic        empty,
    output logic [4:0]  count
);

    sync_fifo u_sync_fifo (
        // Clocking
        .clk     (clk),
        .rst_n   (rst_n),
        // Write port (bundle `wr`, fifo-write target)
        .wr_en   (wr_en),
        .wr_data (wr_data),
        .full    (full),
        // Read port
        .rd_en   (rd_en),
        .rd_data (rd_data),
        .empty   (empty),
        .count   (count)
    );

endmodule
