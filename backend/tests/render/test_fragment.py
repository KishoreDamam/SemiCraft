"""Fragment mode (include_wrapper=False): declarations-as-comment block +
processes + continuous assigns, no module/endmodule (WP-02 task 1)."""

from __future__ import annotations

from semicraft_core.ir import ResetKind
from semicraft_core.render import render

from tests.render.test_golden_counter import build_counter


def test_sv_fragment_shape() -> None:
    m = build_counter(ResetKind.ASYNC, active_low=True)
    out = render(m, language="sv", include_wrapper=False)
    # No wrapper at all.
    assert "module counter" not in out
    assert "endmodule" not in out
    # Declarations appear as a comment block.
    assert "// Fragment mode" in out
    assert "//     parameter int unsigned WIDTH = 8;" in out
    assert "//     input  logic clk;" in out
    assert "//     input  logic rst_n;" in out
    assert "//     output logic [WIDTH-1:0] count;" in out
    # The process is emitted at zero indentation.
    assert "\nalways_ff @(posedge clk or negedge rst_n) begin\n" in out
    assert "    if (!rst_n) begin" in out
    # Header banner still present (license stamp is per generated file).
    assert out.startswith("// SemiCraft v0.1.0\n")


def test_verilog_fragment_shape() -> None:
    m = build_counter(ResetKind.SYNC, active_low=False)
    out = render(m, language="verilog", include_wrapper=False)
    assert "module counter" not in out
    assert "endmodule" not in out
    assert "//     parameter WIDTH = 8;" in out
    assert "//     output reg [WIDTH-1:0] count;" in out
    assert "\nalways @(posedge clk) begin\n" in out
