// SemiCraft v0.4.0
// Snippet: cdc_synchronizer (config hash: a4ff1e37506d)
// 2-stage single-bit CDC synchronizer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module cdc_synchronizer (
    input  logic p_clk,      // Destination-domain clock
    input  logic p_dAsync,   // Asynchronous input, not synchronous to clk (source of the CDC)
    output logic p_q         // Synchronized output, 2 clk cycles behind d_async
);

    logic p_syncFf1;  // Synchronizer stage 1

    always_ff @(posedge p_clk) begin
        p_syncFf1 <= p_dAsync;
        p_q <= p_syncFf1;
    end

endmodule
