// SemiCraft v0.1.0
// Snippet: cdc_synchronizer (config hash: 1d8668e13734)
// 2-stage single-bit CDC synchronizer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module cdc_synchronizer (
    input  wire clk,       // Destination-domain clock
    input  wire rst_n,     // Sync reset, active-low (clears the synchronizer chain)
    input  wire d_async,   // Asynchronous input, not synchronous to clk (source of the CDC)
    output reg  q          // Synchronized output, 2 clk cycles behind d_async
);

    localparam STAGES = 2;
    reg sync_ff1;  // Synchronizer stage 1

    always @(posedge clk) begin
        if (!rst_n) begin
            sync_ff1 <= 1'b0;
            q <= 1'b0;
        end else begin
            sync_ff1 <= d_async;
            q <= sync_ff1;
        end
    end

endmodule
