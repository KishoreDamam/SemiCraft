// SemiCraft v0.1.0
// Snippet: clock_divider (config hash: 716c16a4e6be)
// Clock divider by 2 (pulse output)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module clock_divider #(
    parameter CNT_WIDTH = 1
) (
    input  wire clk,      // Input clock
    input  wire rst_n,    // Sync reset, active-low
    output reg  clk_out   // Single-cycle enable pulse, asserted once every DIV=2 input cycles
);

    reg [CNT_WIDTH-1:0] cnt;  // Free-running divide counter

    always @(posedge clk) begin
        if (!rst_n) begin
            cnt <= {CNT_WIDTH{1'b0}};
            clk_out <= 1'b0;
        end else begin
            if (cnt == {{(CNT_WIDTH-1){1'b0}}, 1'b1}) begin
                cnt <= {CNT_WIDTH{1'b0}};
                clk_out <= 1'b1;
            end else begin
                cnt <= cnt + 1'b1;
                clk_out <= 1'b0;
            end
        end
    end

endmodule
