// SemiCraft v0.1.0
// Snippet: cdc_synchronizer (config hash: dc4a8f5579db)
// 2-stage single-bit CDC synchronizer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module cdc_synchronizer (
    input  logic clk,       // Destination-domain clock
    input  logic d_async,   // Asynchronous input, not synchronous to clk (source of the CDC)
    output logic q          // Synchronized output, 2 clk cycles behind d_async
);

    localparam int unsigned STAGES = 2;
    logic sync_ff1;  // Synchronizer stage 1

    always_ff @(posedge clk) begin
        sync_ff1 <= d_async;
        q <= sync_ff1;
    end

endmodule
