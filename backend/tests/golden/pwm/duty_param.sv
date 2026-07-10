// SemiCraft v0.1.0
// Snippet: pwm (config hash: b04486fb66e3)
// PWM generator, 8-bit, fixed duty parameter
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module pwm #(
    parameter int unsigned RES = 8,
    parameter int unsigned DUTY = 128
) (
    input  logic clk,      // Clock
    input  logic rst_n,    // Sync reset, active-low
    output logic pwm_out   // PWM output, active-high
);

    logic [RES-1:0] cnt;  // Free-running PWM period counter

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            cnt <= {RES{1'b0}};
        end else begin
            cnt <= cnt + 1'b1;
        end
    end

    assign pwm_out = cnt < DUTY[RES-1:0];

endmodule
