// SemiCraft v0.4.0
// Example instantiation: sync_fifo (config hash: e02e49bfb231)
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
    input  wire       clk,
    input  wire       rst_n,
    input  wire       wr_en,
    input  wire [7:0] wr_data,
    output wire       full,
    input  wire       rd_en,
    output wire [7:0] rd_data,
    output wire       empty,
    output wire [3:0] count
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
