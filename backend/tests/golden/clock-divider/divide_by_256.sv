// SemiCraft v0.1.0
// Snippet: clock_divider (config hash: 6e3a1f6810fa)
// Clock divider by 256 (toggle output)
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module clock_divider #(
    parameter int unsigned CNT_WIDTH = 8
) (
    input  logic clk,      // Input clock
    input  logic rst_n,    // Sync reset, active-low
    output logic clk_out   // Divided clock signal, toggling every DIV/2=128 input cycles
);

    logic [CNT_WIDTH-1:0] cnt;  // Free-running divide counter

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            cnt <= {CNT_WIDTH{1'b0}};
            clk_out <= 1'b0;
        end else begin
            if (cnt == {{(CNT_WIDTH-7){1'b0}}, 7'b1111111}) begin
                cnt <= {CNT_WIDTH{1'b0}};
                clk_out <= ~clk_out;
            end else begin
                cnt <= cnt + 1'b1;
            end
        end
    end

endmodule
