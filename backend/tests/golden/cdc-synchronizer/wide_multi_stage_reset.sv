// SemiCraft v0.1.0
// Snippet: cdc_synchronizer (config hash: 793181160da2)
// 4-stage 2-bit CDC synchronizer
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module cdc_synchronizer #(
    parameter int unsigned WIDTH = 2
) (
    input  logic             clk,       // Destination-domain clock
    input  logic             rst_n,     // Sync reset, active-low (clears the synchronizer chain)
    input  logic [WIDTH-1:0] d_async,   // Asynchronous input, not synchronous to clk (source of the CDC)
    output logic [WIDTH-1:0] q          // Synchronized output, 4 clk cycles behind d_async
);

    localparam int unsigned STAGES = 4;
    logic [WIDTH-1:0] sync_ff1;  // Synchronizer stage 1
    logic [WIDTH-1:0] sync_ff2;  // Synchronizer stage 2
    logic [WIDTH-1:0] sync_ff3;  // Synchronizer stage 3

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            sync_ff1 <= {WIDTH{1'b0}};
            sync_ff2 <= {WIDTH{1'b0}};
            sync_ff3 <= {WIDTH{1'b0}};
            q <= {WIDTH{1'b0}};
        end else begin
            // WIDTH > 1: each bit is synchronized independently by its own flip-flop chain. This is only safe for gray-coded or quasi-static signals -- individual bits may resolve on different clock cycles, so arbitrary multi-bit data is NOT guaranteed to arrive coherently.
            sync_ff1 <= d_async;
            sync_ff2 <= sync_ff1;
            sync_ff3 <= sync_ff2;
            q <= sync_ff3;
        end
    end

endmodule
