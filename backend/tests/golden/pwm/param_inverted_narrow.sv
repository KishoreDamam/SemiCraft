// SemiCraft v0.1.0
// Snippet: pwm (config hash: 349000b7556e)
// PWM generator, 6-bit, fixed duty parameter, inverted
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module pwm #(
    parameter int unsigned RES = 6,
    parameter int unsigned DUTY = 32
) (
    input  logic clk,      // Clock
    input  logic rst_n,    // Sync reset, active-low
    output logic pwm_out   // PWM output, inverted (active-low)
);

    logic [RES-1:0] cnt;  // Free-running PWM period counter

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            cnt <= {RES{1'b0}};
        end else begin
            cnt <= cnt + 1'b1;
        end
    end

    assign pwm_out = !(cnt < DUTY[RES-1:0]);

endmodule
