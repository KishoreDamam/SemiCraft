// SemiCraft v0.1.0
// Snippet: cdc_synchronizer (config hash: 5e9ce4732aee)
// 2-stage 2-bit CDC synchronizer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module cdc_synchronizer #(
    parameter int unsigned WIDTH = 2
) (
    input  logic             clk,       // Destination-domain clock
    input  logic [WIDTH-1:0] d_async,   // Asynchronous input, not synchronous to clk (source of the CDC)
    output logic [WIDTH-1:0] q          // Synchronized output, 2 clk cycles behind d_async
);

    logic [WIDTH-1:0] sync_ff1;  // Synchronizer stage 1

    always_ff @(posedge clk) begin
        // WIDTH > 1: each bit is synchronized independently by its own flip-flop chain. This is only safe for gray-coded or quasi-static signals -- individual bits may resolve on different clock cycles, so arbitrary multi-bit data is NOT guaranteed to arrive coherently.
        sync_ff1 <= d_async;
        q <= sync_ff1;
    end

endmodule
