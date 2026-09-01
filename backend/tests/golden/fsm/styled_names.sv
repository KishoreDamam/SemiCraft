// SemiCraft v0.4.0
// Snippet: fsm (config hash: 05e858ab38f9)
// Moore FSM, 3 states, binary encoding
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module fsm (
    input logic p_clk,    // Clock
    input logic p_rst_n   // Sync reset, active-low
);

    typedef enum logic [1:0] {
        p_idle = 2'b00,
        p_run  = 2'b01,
        p_done = 2'b10
    } p_stateT;

    logic [1:0] p_state;  // Current state
    logic [1:0] p_stateNext;  // Next state (comb)

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_state <= p_idle;
        end else begin
            p_state <= p_stateNext;
        end
    end

    // Next-state logic (transitions are user-completed)
    always_comb begin
        // default: hold current state (no-latch guarantee)
        p_stateNext = p_state;
        unique case (p_state)
            p_idle: begin
                // TODO: transition logic for idle
            end
            p_run: begin
                // TODO: transition logic for run
            end
            p_done: begin
                // TODO: transition logic for done
            end
            default: ;
        endcase
    end

endmodule
