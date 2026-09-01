// SemiCraft v0.4.0
// Snippet: rr_arbiter (config hash: b56dc4a4ccc9)
// 4-way round-robin arbiter, registered grant
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module rr_arbiter (
    input  logic       p_clk,         // Clock
    input  logic       p_rst_n,       // Sync reset, active-low
    input  logic [3:0] p_req,         // Request lines, one per requester
    output logic [3:0] p_grant,       // One-hot grant (zero when idle), registered
    output logic       p_grantValid   // High when a grant is asserted (|grant)
);

    logic [1:0] p_ptr;  // Highest-priority requester index (rotates)
    logic [3:0] p_maskedReq;  // Requests at or above the priority pointer
    logic [3:0] p_maskedGnt;  // Lowest-index grant within the masked window
    logic [3:0] p_unmaskedGnt;  // Lowest-index grant over all requests (wrap-around)
    logic [3:0] p_grantNxt;  // Combinational rotate-priority grant decision

    assign p_maskedReq = p_req & ({4{1'b1}} << p_ptr);

    assign p_maskedGnt = {(p_maskedReq[3] & (~|p_maskedReq[2:0])), (p_maskedReq[2] & (~|p_maskedReq[1:0])), (p_maskedReq[1] & (~|p_maskedReq[0:0])), p_maskedReq[0]};

    assign p_unmaskedGnt = {(p_req[3] & (~|p_req[2:0])), (p_req[2] & (~|p_req[1:0])), (p_req[1] & (~|p_req[0:0])), p_req[0]};

    assign p_grantNxt = (|p_maskedReq) ? p_maskedGnt : p_unmaskedGnt;

    assign p_grantValid = |p_grant;

    always_ff @(posedge p_clk) begin
        if (!p_rst_n) begin
            p_ptr <= 2'd0;
            p_grant <= 4'd0;
        end else begin
            if (p_grantNxt[0]) begin
                p_ptr <= 2'd1;
            end else if (p_grantNxt[1]) begin
                p_ptr <= 2'd2;
            end else if (p_grantNxt[2]) begin
                p_ptr <= 2'd3;
            end else if (p_grantNxt[3]) begin
                p_ptr <= 2'd0;
            end
            p_grant <= p_grantNxt;
        end
    end

endmodule
