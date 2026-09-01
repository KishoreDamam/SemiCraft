// SemiCraft v0.4.0
// Snippet: pwm (config hash: 30a28f1388c6)
// PWM generator, 8-bit, runtime duty input
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module pwm #(
    parameter int unsigned RES = 8
) (
    input  logic           p_clk,     // Clock
    input  logic           p_rst_n,   // Sync reset, active-low
    input  logic [RES-1:0] p_duty,    // Runtime duty-cycle threshold
    output logic           p_pwmOut   // PWM output, active-high
);

    logic [RES-1:0] p_cnt;  // Free-running PWM period counter

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_cnt <= {RES{1'b0}};
        end else begin
            p_cnt <= p_cnt + 1'b1;
        end
    end

    assign p_pwmOut = p_cnt < p_duty;

endmodule
