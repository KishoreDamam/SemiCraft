// SemiCraft v0.1.0
// Snippet: rr_arbiter (config hash: ab00db50bcb5)
// 2-way round-robin arbiter, combinational grant
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module rr_arbiter (
    input  wire       clk,          // Clock
    input  wire       rst_n,        // Sync reset, active-low
    input  wire [1:0] req,          // Request lines, one per requester
    output wire [1:0] grant,        // One-hot grant (zero when idle), combinational
    output wire       grant_valid   // High when a grant is asserted (|grant)
);

    reg [0:0] ptr;  // Highest-priority requester index (rotates)
    wire [1:0] masked_req;  // Requests at or above the priority pointer
    wire [1:0] masked_gnt;  // Lowest-index grant within the masked window
    wire [1:0] unmasked_gnt;  // Lowest-index grant over all requests (wrap-around)
    wire [1:0] grant_nxt;  // Combinational rotate-priority grant decision

    assign masked_req = req & ({2{1'b1}} << ptr);

    assign masked_gnt = {(masked_req[1] & (~|masked_req[0:0])), masked_req[0]};

    assign unmasked_gnt = {(req[1] & (~|req[0:0])), req[0]};

    assign grant_nxt = (|masked_req) ? masked_gnt : unmasked_gnt;

    assign grant = grant_nxt;

    assign grant_valid = |grant;

    always @(posedge clk) begin
        if (!rst_n) begin
            ptr <= 1'd0;
        end else begin
            if (grant_nxt[0]) begin
                ptr <= 1'd1;
            end else if (grant_nxt[1]) begin
                ptr <= 1'd0;
            end
        end
    end

endmodule
