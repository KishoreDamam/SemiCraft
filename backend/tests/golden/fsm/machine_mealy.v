// SemiCraft v0.1.0
// Snippet: fsm (config hash: 4c9591ac45c5)
// Mealy FSM, 3 states, binary encoding
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module fsm (
    input wire clk,    // Clock
    input wire rst_n   // Sync reset, active-low
);

    // state_t: binary encoding
    localparam [1:0] idle = 2'b00;
    localparam [1:0] run  = 2'b01;
    localparam [1:0] done = 2'b10;

    reg [1:0] state;  // Current state
    reg [1:0] state_next;  // Next state (comb)

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= idle;
        end else begin
            state <= state_next;
        end
    end

    // Next-state logic (transitions are user-completed)
    always @(*) begin
        // default: hold current state (no-latch guarantee)
        state_next = state;
        case (state)
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
