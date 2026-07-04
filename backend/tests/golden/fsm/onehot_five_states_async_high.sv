// SemiCraft v0.1.0
// Snippet: fsm (config hash: f6dbe721f797)
// Moore FSM, 5 states, onehot encoding
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module fsm (
    input logic clk,   // Clock
    input logic rst    // Async reset, active-high
);

    typedef enum logic [4:0] {
        s0 = 5'b00001,
        s1 = 5'b00010,
        s2 = 5'b00100,
        s3 = 5'b01000,
        s4 = 5'b10000
    } state_t;

    logic [4:0] state;  // Current state
    logic [4:0] state_next;  // Next state (comb)

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= s0;
        end else begin
            state <= state_next;
        end
    end

    // Next-state logic (transitions are user-completed)
    always_comb begin
        // default: hold current state (no-latch guarantee)
        state_next = state;
        unique case (state)
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
        endcase
    end

endmodule
