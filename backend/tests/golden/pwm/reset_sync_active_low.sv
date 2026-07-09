// SemiCraft v0.1.0
// Snippet: pwm (config hash: 6adac905f45d)
// PWM generator, 8-bit, runtime duty input
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module pwm #(
    parameter int unsigned RES = 8
) (
    input  logic           clk,      // Clock
    input  logic           rst_n,    // Sync reset, active-low
    input  logic [RES-1:0] duty,     // Runtime duty-cycle threshold
    output logic           pwm_out   // PWM output, active-high
);

    logic [RES-1:0] cnt;  // Free-running PWM period counter

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            cnt <= {RES{1'b0}};
        end else begin
            cnt <= cnt + 1'b1;
        end
    end

    assign pwm_out = cnt < duty;

endmodule
