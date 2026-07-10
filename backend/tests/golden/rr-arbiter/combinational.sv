// SemiCraft v0.1.0
// Snippet: rr_arbiter (config hash: f1ab6597e25b)
// 4-way round-robin arbiter, combinational grant
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module rr_arbiter (
    input  logic       clk,          // Clock
    input  logic       rst_n,        // Sync reset, active-low
    input  logic [3:0] req,          // Request lines, one per requester
    output logic [3:0] grant,        // One-hot grant (zero when idle), combinational
    output logic       grant_valid   // High when a grant is asserted (|grant)
);

    logic [1:0] ptr;  // Highest-priority requester index (rotates)
    logic [3:0] masked_req;  // Requests at or above the priority pointer
    logic [3:0] masked_gnt;  // Lowest-index grant within the masked window
    logic [3:0] unmasked_gnt;  // Lowest-index grant over all requests (wrap-around)
    logic [3:0] grant_nxt;  // Combinational rotate-priority grant decision

    assign masked_req = req & ({4{1'b1}} << ptr);

    assign masked_gnt = {(masked_req[3] & (~|masked_req[2:0])), (masked_req[2] & (~|masked_req[1:0])), (masked_req[1] & (~|masked_req[0:0])), masked_req[0]};

    assign unmasked_gnt = {(req[3] & (~|req[2:0])), (req[2] & (~|req[1:0])), (req[1] & (~|req[0:0])), req[0]};

    assign grant_nxt = (|masked_req) ? masked_gnt : unmasked_gnt;

    assign grant = grant_nxt;

    assign grant_valid = |grant;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            ptr <= 2'd0;
        end else begin
            if (grant_nxt[0]) begin
                ptr <= 2'd1;
            end else if (grant_nxt[1]) begin
                ptr <= 2'd2;
            end else if (grant_nxt[2]) begin
                ptr <= 2'd3;
            end else if (grant_nxt[3]) begin
                ptr <= 2'd0;
            end
        end
    end

endmodule
