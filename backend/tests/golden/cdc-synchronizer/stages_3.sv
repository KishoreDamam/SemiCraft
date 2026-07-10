// SemiCraft v0.1.0
// Snippet: cdc_synchronizer (config hash: 131e7aa05a95)
// 3-stage single-bit CDC synchronizer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module cdc_synchronizer (
    input  logic clk,       // Destination-domain clock
    input  logic d_async,   // Asynchronous input, not synchronous to clk (source of the CDC)
    output logic q          // Synchronized output, 3 clk cycles behind d_async
);

    logic sync_ff1;  // Synchronizer stage 1
    logic sync_ff2;  // Synchronizer stage 2

    always_ff @(posedge clk) begin
        sync_ff1 <= d_async;
        sync_ff2 <= sync_ff1;
        q <= sync_ff2;
    end

endmodule
