// SemiCraft v0.1.0
// Snippet: rr_arbiter (config hash: 711f1b633732)
// 8-way round-robin arbiter, registered grant
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module rr_arbiter (
    input  wire       clk,          // Clock
    input  wire       rst_n,        // Sync reset, active-low
    input  wire [7:0] req,          // Request lines, one per requester
    output reg  [7:0] grant,        // One-hot grant (zero when idle), registered
    output wire       grant_valid   // High when a grant is asserted (|grant)
);

    reg [2:0] ptr;  // Highest-priority requester index (rotates)
    wire [7:0] masked_req;  // Requests at or above the priority pointer
    wire [7:0] masked_gnt;  // Lowest-index grant within the masked window
    wire [7:0] unmasked_gnt;  // Lowest-index grant over all requests (wrap-around)
    wire [7:0] grant_nxt;  // Combinational rotate-priority grant decision

    assign masked_req = req & ({8{1'b1}} << ptr);

    assign masked_gnt = {(masked_req[7] & (~|masked_req[6:0])), (masked_req[6] & (~|masked_req[5:0])), (masked_req[5] & (~|masked_req[4:0])), (masked_req[4] & (~|masked_req[3:0])), (masked_req[3] & (~|masked_req[2:0])), (masked_req[2] & (~|masked_req[1:0])), (masked_req[1] & (~|masked_req[0:0])), masked_req[0]};

    assign unmasked_gnt = {(req[7] & (~|req[6:0])), (req[6] & (~|req[5:0])), (req[5] & (~|req[4:0])), (req[4] & (~|req[3:0])), (req[3] & (~|req[2:0])), (req[2] & (~|req[1:0])), (req[1] & (~|req[0:0])), req[0]};

    assign grant_nxt = (|masked_req) ? masked_gnt : unmasked_gnt;

    assign grant_valid = |grant;

    always @(posedge clk) begin
        if (!rst_n) begin
            ptr <= 3'd0;
            grant <= 8'd0;
        end else begin
            if (grant_nxt[0]) begin
                ptr <= 3'd1;
            end else if (grant_nxt[1]) begin
                ptr <= 3'd2;
            end else if (grant_nxt[2]) begin
                ptr <= 3'd3;
            end else if (grant_nxt[3]) begin
                ptr <= 3'd4;
            end else if (grant_nxt[4]) begin
                ptr <= 3'd5;
            end else if (grant_nxt[5]) begin
                ptr <= 3'd6;
            end else if (grant_nxt[6]) begin
                ptr <= 3'd7;
            end else if (grant_nxt[7]) begin
                ptr <= 3'd0;
            end
            grant <= grant_nxt;
        end
    end

endmodule
