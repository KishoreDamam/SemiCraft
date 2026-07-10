// SemiCraft v0.1.0
// Snippet: cdc_synchronizer (config hash: 21ac4282bd13)
// 4-stage single-bit CDC synchronizer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module cdc_synchronizer (
    input  logic clk,       // Destination-domain clock
    input  logic d_async,   // Asynchronous input, not synchronous to clk (source of the CDC)
    output logic q          // Synchronized output, 4 clk cycles behind d_async
);

    logic sync_ff1;  // Synchronizer stage 1
    logic sync_ff2;  // Synchronizer stage 2
    logic sync_ff3;  // Synchronizer stage 3

    always_ff @(posedge clk) begin
        sync_ff1 <= d_async;
        sync_ff2 <= sync_ff1;
        sync_ff3 <= sync_ff2;
        q <= sync_ff3;
    end

endmodule
