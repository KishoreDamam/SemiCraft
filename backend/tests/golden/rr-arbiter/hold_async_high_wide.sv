// SemiCraft v0.1.0
// Snippet: rr_arbiter (config hash: 44a0e0329fe0)
// 16-way round-robin arbiter, registered grant, hold-grant
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module rr_arbiter (
    input  logic        clk,          // Clock
    input  logic        rst,          // Async reset, active-high
    input  logic [15:0] req,          // Request lines, one per requester
    output logic [15:0] grant,        // One-hot grant (zero when idle), registered
    output logic        grant_valid   // High when a grant is asserted (|grant)
);

    logic [3:0] ptr;  // Highest-priority requester index (rotates)
    logic [15:0] masked_req;  // Requests at or above the priority pointer
    logic [15:0] masked_gnt;  // Lowest-index grant within the masked window
    logic [15:0] unmasked_gnt;  // Lowest-index grant over all requests (wrap-around)
    logic [15:0] grant_nxt;  // Combinational rotate-priority grant decision

    assign masked_req = req & ({16{1'b1}} << ptr);

    assign masked_gnt = {(masked_req[15] & (~|masked_req[14:0])), (masked_req[14] & (~|masked_req[13:0])), (masked_req[13] & (~|masked_req[12:0])), (masked_req[12] & (~|masked_req[11:0])), (masked_req[11] & (~|masked_req[10:0])), (masked_req[10] & (~|masked_req[9:0])), (masked_req[9] & (~|masked_req[8:0])), (masked_req[8] & (~|masked_req[7:0])), (masked_req[7] & (~|masked_req[6:0])), (masked_req[6] & (~|masked_req[5:0])), (masked_req[5] & (~|masked_req[4:0])), (masked_req[4] & (~|masked_req[3:0])), (masked_req[3] & (~|masked_req[2:0])), (masked_req[2] & (~|masked_req[1:0])), (masked_req[1] & (~|masked_req[0:0])), masked_req[0]};

    assign unmasked_gnt = {(req[15] & (~|req[14:0])), (req[14] & (~|req[13:0])), (req[13] & (~|req[12:0])), (req[12] & (~|req[11:0])), (req[11] & (~|req[10:0])), (req[10] & (~|req[9:0])), (req[9] & (~|req[8:0])), (req[8] & (~|req[7:0])), (req[7] & (~|req[6:0])), (req[6] & (~|req[5:0])), (req[5] & (~|req[4:0])), (req[4] & (~|req[3:0])), (req[3] & (~|req[2:0])), (req[2] & (~|req[1:0])), (req[1] & (~|req[0:0])), req[0]};

    assign grant_nxt = (|masked_req) ? masked_gnt : unmasked_gnt;

    assign grant_valid = |grant;

    always_ff @(posedge clk or posedge rst) begin
        if (rst) begin
            ptr <= 4'd0;
            grant <= 16'd0;
        end else begin
            if (grant_nxt[0]) begin
                ptr <= 4'd0;
            end else if (grant_nxt[1]) begin
                ptr <= 4'd1;
            end else if (grant_nxt[2]) begin
                ptr <= 4'd2;
            end else if (grant_nxt[3]) begin
                ptr <= 4'd3;
            end else if (grant_nxt[4]) begin
                ptr <= 4'd4;
            end else if (grant_nxt[5]) begin
                ptr <= 4'd5;
            end else if (grant_nxt[6]) begin
                ptr <= 4'd6;
            end else if (grant_nxt[7]) begin
                ptr <= 4'd7;
            end else if (grant_nxt[8]) begin
                ptr <= 4'd8;
            end else if (grant_nxt[9]) begin
                ptr <= 4'd9;
            end else if (grant_nxt[10]) begin
                ptr <= 4'd10;
            end else if (grant_nxt[11]) begin
                ptr <= 4'd11;
            end else if (grant_nxt[12]) begin
                ptr <= 4'd12;
            end else if (grant_nxt[13]) begin
                ptr <= 4'd13;
            end else if (grant_nxt[14]) begin
                ptr <= 4'd14;
            end else if (grant_nxt[15]) begin
                ptr <= 4'd15;
            end
            grant <= grant_nxt;
        end
    end

endmodule
