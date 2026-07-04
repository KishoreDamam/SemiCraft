// SemiCraft v0.1.0
// Snippet: fsm (config hash: e1f5c80ba9ca)
// Moore FSM, 5 states, binary encoding
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module fsm (
    input logic clk,    // Clock
    input logic rst_n   // Sync reset, active-low
);

    typedef enum logic [2:0] {
        idle  = 3'b000,
        load  = 3'b001,
        run   = 3'b010,
        flush = 3'b011,
        done  = 3'b100
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
            load: begin
                // TODO: transition logic for load
            end
            run: begin
                // TODO: transition logic for run
            end
            flush: begin
                // TODO: transition logic for flush
            end
            done: begin
                // TODO: transition logic for done
            end
        endcase
    end

endmodule
