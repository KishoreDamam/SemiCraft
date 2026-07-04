// SemiCraft v0.1.0
// Snippet: fsm (config hash: a64657569ff2)
// Moore FSM, 5 states, binary encoding
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module fsm (
    input wire clk,    // Clock
    input wire rst_n   // Sync reset, active-low
);

    // state_t: binary encoding
    localparam [2:0] idle  = 3'b000;
    localparam [2:0] load  = 3'b001;
    localparam [2:0] run   = 3'b010;
    localparam [2:0] flush = 3'b011;
    localparam [2:0] done  = 3'b100;

    reg [2:0] state;  // Current state
    reg [2:0] state_next;  // Next state (comb)

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
