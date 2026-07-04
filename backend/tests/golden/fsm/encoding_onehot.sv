// SemiCraft v0.1.0
// Snippet: fsm (config hash: 33c4ec723e9e)
// Moore FSM, 3 states, onehot encoding
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module fsm (
    input logic clk,    // Clock
    input logic rst_n   // Sync reset, active-low
);

    typedef enum logic [2:0] {
        idle = 3'b001,
        run  = 3'b010,
        done = 3'b100
    } state_t;

    logic [2:0] state;  // Current state
    logic [2:0] state_next;  // Next state (comb)

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= idle;
        end else begin
            state <= state_next;
        end
    end

    // Next-state logic (transitions are user-completed)
    always_comb begin
        // default: hold current state (no-latch guarantee)
        state_next = state;
        unique case (state)
            idle: begin
                // TODO: transition logic for idle
            end
            run: begin
                // TODO: transition logic for run
            end
            done: begin
                // TODO: transition logic for done
            end
        endcase
    end

endmodule
