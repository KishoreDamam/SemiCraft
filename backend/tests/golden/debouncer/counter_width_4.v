// SemiCraft v0.1.0
// Snippet: debouncer (config hash: 58bd1cbc01a0)
// Debouncer, 16-cycle period, active-high idle
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module debouncer #(
    parameter CNT_WIDTH = 4
) (
    input  wire clk,     // Clock
    input  wire rst_n,   // Sync reset, active-low
    input  wire d_in,    // Raw, potentially bouncy input
    output reg  q        // Debounced output (idles high)
);

    reg [CNT_WIDTH-1:0] cnt;  // Disagreement counter: counts consecutive cycles d_in != q

    always @(posedge clk) begin
        if (!rst_n) begin
            cnt <= {CNT_WIDTH{1'b0}};
            q <= 1'b1;
        end else begin
            if (d_in != q) begin
                if (cnt == {{(CNT_WIDTH-4){1'b0}}, 4'b1111}) begin
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
