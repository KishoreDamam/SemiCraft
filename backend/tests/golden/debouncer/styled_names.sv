// SemiCraft v0.4.0
// Snippet: debouncer (config hash: 25b930679f39)
// Debouncer, 65536-cycle period, active-high idle
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module debouncer #(
    parameter int unsigned CNT_WIDTH = 16
) (
    input  logic p_clk,     // Clock
    input  logic p_rst_n,   // Sync reset, active-low
    input  logic p_dIn,     // Raw, potentially bouncy input
    output logic p_q        // Debounced output (idles high)
);

    logic [CNT_WIDTH-1:0] p_cnt;  // Disagreement counter: counts consecutive cycles d_in != q

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_cnt <= {CNT_WIDTH{1'b0}};
            p_q <= 1'b1;
        end else begin
            if (p_dIn != p_q) begin
                if (p_cnt == {{(CNT_WIDTH-16){1'b0}}, 16'b1111111111111111}) begin
                    p_q <= p_dIn;
                    p_cnt <= {CNT_WIDTH{1'b0}};
                end else begin
                    p_cnt <= p_cnt + 1'b1;
                end
            end else begin
                p_cnt <= {CNT_WIDTH{1'b0}};
            end
        end
    end

endmodule
