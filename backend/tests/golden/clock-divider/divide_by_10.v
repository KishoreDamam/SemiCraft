// SemiCraft v0.1.0
// Snippet: clock_divider (config hash: 5e6fb15227f9)
// Clock divider by 10 (toggle output)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module clock_divider #(
    parameter DIV = 10,
    parameter CNT_WIDTH = 4
) (
    input  wire clk,      // Input clock
    input  wire rst_n,    // Sync reset, active-low
    output reg  clk_out   // Divided clock signal, toggling every DIV/2=5 input cycles
);

    reg [CNT_WIDTH-1:0] cnt;  // Free-running divide counter

    always @(posedge clk) begin
        if (!rst_n) begin
            cnt <= {CNT_WIDTH{1'b0}};
            clk_out <= 1'b0;
        end else begin
            if (cnt == {{(CNT_WIDTH-3){1'b0}}, 3'b100}) begin
                cnt <= {CNT_WIDTH{1'b0}};
                clk_out <= ~clk_out;
            end else begin
                cnt <= cnt + 1'b1;
            end
        end
    end

endmodule
