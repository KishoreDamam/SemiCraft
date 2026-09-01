// SemiCraft v0.4.0
// Snippet: clock_divider (config hash: f93ac723f3c3)
// Clock divider by 2 (toggle output)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module clock_divider #(
    parameter int unsigned CNT_WIDTH = 1
) (
    input  logic p_clk,     // Input clock
    input  logic p_rst_n,   // Sync reset, active-low
    output logic p_clkOut   // Divided clock signal, toggling every DIV/2=1 input cycles
);

    logic [CNT_WIDTH-1:0] p_cnt;  // Free-running divide counter

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_cnt <= {CNT_WIDTH{1'b0}};
            p_clkOut <= 1'b0;
        end else begin
            if (p_cnt == {CNT_WIDTH{1'b0}}) begin
                p_cnt <= {CNT_WIDTH{1'b0}};
                p_clkOut <= ~p_clkOut;
            end else begin
                p_cnt <= p_cnt + 1'b1;
            end
        end
    end

endmodule
