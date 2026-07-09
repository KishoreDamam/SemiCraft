// SemiCraft v0.1.0
// Snippet: pwm (config hash: 821433cc8f67)
// PWM generator, 8-bit, runtime duty input
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module pwm #(
    parameter RES = 8
) (
    input  wire           clk,      // Clock
    input  wire           rst,      // Sync reset, active-high
    input  wire [RES-1:0] duty,     // Runtime duty-cycle threshold
    output wire           pwm_out   // PWM output, active-high
);

    reg [RES-1:0] cnt;  // Free-running PWM period counter

    always @(posedge clk) begin
        if (rst) begin
            cnt <= {RES{1'b0}};
        end else begin
            cnt <= cnt + 1'b1;
        end
    end

    assign pwm_out = cnt < duty;

endmodule
