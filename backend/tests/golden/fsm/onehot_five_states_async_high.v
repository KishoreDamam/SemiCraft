// SemiCraft v0.1.0
// Snippet: fsm (config hash: dbc45212fe2f)
// Moore FSM, 5 states, onehot encoding
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module fsm (
    input wire clk,   // Clock
    input wire rst    // Async reset, active-high
);

    // state_t: onehot encoding
    localparam [4:0] s0 = 5'b00001;
    localparam [4:0] s1 = 5'b00010;
    localparam [4:0] s2 = 5'b00100;
    localparam [4:0] s3 = 5'b01000;
    localparam [4:0] s4 = 5'b10000;

    reg [4:0] state;  // Current state
    reg [4:0] state_next;  // Next state (comb)

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= s0;
        end else begin
            state <= state_next;
        end
    end

    // Next-state logic (transitions are user-completed)
    always @(*) begin
        // default: hold current state (no-latch guarantee)
        state_next = state;
        case (state)
            s0: begin
                // TODO: transition logic for s0
            end
            s1: begin
                // TODO: transition logic for s1
            end
            s2: begin
                // TODO: transition logic for s2
            end
            s3: begin
                // TODO: transition logic for s3
            end
            s4: begin
                // TODO: transition logic for s4
            end
            default: ;
        endcase
    end

endmodule
