// SemiCraft v0.1.0
// Snippet: cdc_synchronizer (config hash: 5eaa0109d9f7)
// 3-stage single-bit CDC synchronizer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module cdc_synchronizer (
    input  wire clk,       // Destination-domain clock
    input  wire rst_n,     // Sync reset, active-low (clears the synchronizer chain)
    input  wire d_async,   // Asynchronous input, not synchronous to clk (source of the CDC)
    output reg  q          // Synchronized output, 3 clk cycles behind d_async
);

    localparam STAGES = 3;
    reg sync_ff1;  // Synchronizer stage 1
    reg sync_ff2;  // Synchronizer stage 2

    always @(posedge clk) begin
        if (!rst_n) begin
            sync_ff1 <= 1'b0;
            sync_ff2 <= 1'b0;
            q <= 1'b0;
        end else begin
            sync_ff1 <= d_async;
            sync_ff2 <= sync_ff1;
            q <= sync_ff2;
        end
    end

endmodule
