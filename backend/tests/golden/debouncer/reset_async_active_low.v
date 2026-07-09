// SemiCraft v0.1.0
// Snippet: debouncer (config hash: c04200c30e94)
// Debouncer, 65536-cycle period, active-high idle
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module debouncer #(
    parameter CNT_WIDTH = 16
) (
    input  wire clk,     // Clock
    input  wire rst_n,   // Async reset, active-low
    input  wire d_in,    // Raw, potentially bouncy input
    output reg  q        // Debounced output (idles high)
);

    reg [CNT_WIDTH-1:0] cnt;  // Disagreement counter: counts consecutive cycles d_in != q

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= {CNT_WIDTH{1'b0}};
            q <= 1'b1;
        end else begin
            if (d_in != q) begin
                if (cnt == {{(CNT_WIDTH-16){1'b0}}, 16'b1111111111111111}) begin
                    q <= d_in;
                    cnt <= {CNT_WIDTH{1'b0}};
                end else begin
                    cnt <= cnt + 1'b1;
                end
            end else begin
                cnt <= {CNT_WIDTH{1'b0}};
            end
        end
    end

endmodule
