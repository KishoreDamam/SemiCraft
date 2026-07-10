// SemiCraft v0.1.0
// Snippet: fsm (config hash: b6d28de14971)
// Mealy FSM, 3 states, gray encoding
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module fsm (
    input  logic clk,     // Clock
    input  logic rst_n,   // Sync reset, active-low
    output logic valid    // Mealy output (TODO: drive)
);

    typedef enum logic [1:0] {
        idle = 2'b00,
        run  = 2'b01,
        done = 2'b11
    } state_t;

    logic [1:0] state;  // Current state
    logic [1:0] state_next;  // Next state (comb)

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= idle;
        end else begin
            state <= state_next;
        end
    end

    // Next-state logic (transitions are user-completed)
    always_comb begin
        // default Mealy outputs (override in transition arms below)
        valid = 1'b0;
        // default: hold current state (no-latch guarantee)
        state_next = state;
        unique case (state)
            idle: begin
                // TODO: transition logic for idle
                // TODO: Mealy outputs for this state belong here
            end
            run: begin
                // TODO: transition logic for run
                // TODO: Mealy outputs for this state belong here
            end
            done: begin
                // TODO: transition logic for done
                // TODO: Mealy outputs for this state belong here
            end
            default: ;
        endcase
    end

endmodule
