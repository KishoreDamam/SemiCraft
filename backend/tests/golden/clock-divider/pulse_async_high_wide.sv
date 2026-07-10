// SemiCraft v0.1.0
// Snippet: clock_divider (config hash: a1a9207f5113)
// Clock divider by 1024 (pulse output)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module clock_divider #(
    parameter int unsigned CNT_WIDTH = 10
) (
    input  logic clk,      // Input clock
    input  logic rst,      // Async reset, active-high
    output logic clk_out   // Single-cycle enable pulse, asserted once every DIV=1024 input cycles
);

    logic [CNT_WIDTH-1:0] cnt;  // Free-running divide counter

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            cnt <= {CNT_WIDTH{1'b0}};
            clk_out <= 1'b0;
        end else begin
            if (cnt == {{(CNT_WIDTH-10){1'b0}}, 10'b1111111111}) begin
                cnt <= {CNT_WIDTH{1'b0}};
                clk_out <= 1'b1;
            end else begin
                cnt <= cnt + 1'b1;
                clk_out <= 1'b0;
            end
        end
    end

endmodule
