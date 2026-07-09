// SemiCraft v0.1.0
// Snippet: pwm (config hash: be3c5ccd374e)
// PWM generator, 8-bit, runtime duty input, inverted
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module pwm #(
    parameter RES = 8
) (
    input  wire           clk,      // Clock
    input  wire           rst_n,    // Sync reset, active-low
    input  wire [RES-1:0] duty,     // Runtime duty-cycle threshold
    output wire           pwm_out   // PWM output, inverted (active-low)
);

    reg [RES-1:0] cnt;  // Free-running PWM period counter

    always @(posedge clk) begin
        if (!rst_n) begin
            cnt <= {RES{1'b0}};
        end else begin
            cnt <= cnt + 1'b1;
        end
    end

    assign pwm_out = !(cnt < duty);

endmodule
