"""Golden renderings of the IR_SPEC §9 counter (WP-02 task 5).

Both languages x all four reset variants (sync/async x active-high/low) are
asserted byte-exactly. The async active-low SystemVerilog case is additionally
pinned against a verbatim literal of the IR_SPEC §9 rendering (modulo the
header banner, which §9 elides). WP-08 moves these to golden files.
"""

from __future__ import annotations

import pytest
from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    ClockSpec,
    Const,
    Header,
    If,
    Module,
    Param,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    bit,
    vec,
)
from semicraft_core.license import DISCLAIMER
from semicraft_core.render import render

HEADER = (
    "// SemiCraft v0.1.0\n"
    "// Snippet: counter (config hash: deadbeef1234)\n"
    "// Up counter\n"
    "//\n"
    "// Generated code is provided as-is, without warranty of any kind. Free for\n"
    "// commercial and non-commercial use at the user's own risk.\n"
    "\n"
)


def _rst_doc(kind: ResetKind, active_low: bool) -> str:
    style = "Async" if kind is ResetKind.ASYNC else "Sync"
    pol = "low" if active_low else "high"
    return f"{style} reset, active-{pol}"


def build_counter(kind: ResetKind, active_low: bool) -> Module:
    """The IR_SPEC §9 counter, parameterized over the reset variant."""
    return Module(
        name="counter",
        header=Header(
            license=DISCLAIMER,
            config_hash="deadbeef1234",
            tool_version="0.1.0",
            description="Up counter",
        ),
        params=[Param("WIDTH", Const(8), doc="Counter width in bits")],
        ports=[
            Port("clk", IN, bit()),
            Port("rst", IN, bit(), doc=_rst_doc(kind, active_low)),
            Port("en", IN, bit(), doc="Count enable"),
            Port("count", OUT, vec("WIDTH")),
        ],
        items=[
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=ResetSpec("rst", kind=kind, active_low=active_low),
                reset_body=[Assign(Ref("count"), Const(0, width=Ref("WIDTH")))],
                body=[
                    If(
                        Ref("en"),
                        then=[
                            Assign(
                                Ref("count"),
                                BinOp(BinOpKind.ADD, Ref("count"), Const(1)),
                            )
                        ],
                    )
                ],
            )
        ],
    )


# Module header + ANSI port list, keyed by (language, active_low). The reset
# doc comment is spliced in via <DOC> (its text varies with the reset kind).
_PORT_BLOCKS = {
    ("sv", True): """module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst_n,   // <DOC>
    input  logic             en,      // Count enable
    output logic [WIDTH-1:0] count
);
""",
    ("sv", False): """module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst,    // <DOC>
    input  logic             en,     // Count enable
    output logic [WIDTH-1:0] count
);
""",
    ("verilog", True): """module counter #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,   // <DOC>
    input  wire             en,      // Count enable
    output reg  [WIDTH-1:0] count
);
""",
    ("verilog", False): """module counter #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst,    // <DOC>
    input  wire             en,     // Count enable
    output reg  [WIDTH-1:0] count
);
""",
}


def _always_block(language: str, kind: ResetKind, active_low: bool) -> str:
    kw = "always_ff" if language == "sv" else "always"
    rst = "rst_n" if active_low else "rst"
    sens = "posedge clk"
    if kind is ResetKind.ASYNC:
        sens += f" or {'negedge' if active_low else 'posedge'} {rst}"
    cond = f"!{rst}" if active_low else rst
    return (
        f"    {kw} @({sens}) begin\n"
        f"        if ({cond}) begin\n"
        "            count <= {WIDTH{1'b0}};\n"
        "        end else begin\n"
        "            if (en) begin\n"
        "                count <= count + 1'b1;\n"
        "            end\n"
        "        end\n"
        "    end\n"
    )


def expected_counter(language: str, kind: ResetKind, active_low: bool) -> str:
    ports = _PORT_BLOCKS[(language, active_low)].replace(
        "<DOC>", _rst_doc(kind, active_low)
    )
    return (
        HEADER
        + ports
        + "\n"
        + _always_block(language, kind, active_low)
        + "\nendmodule\n"
    )


# Verbatim IR_SPEC §9 SystemVerilog rendering (modulo header banner).
IR_SPEC_SECTION_9_SV = (
    HEADER
    + """module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst_n,   // Async reset, active-low
    input  logic             en,      // Count enable
    output logic [WIDTH-1:0] count
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
"""
)


def test_sv_async_active_low_matches_ir_spec_section_9() -> None:
    m = build_counter(ResetKind.ASYNC, active_low=True)
    assert render(m, language="sv") == IR_SPEC_SECTION_9_SV


@pytest.mark.parametrize("language", ["sv", "verilog"])
@pytest.mark.parametrize("kind", [ResetKind.SYNC, ResetKind.ASYNC])
@pytest.mark.parametrize("active_low", [True, False])
def test_counter_golden_all_variants(
    language: str, kind: ResetKind, active_low: bool
) -> None:
    m = build_counter(kind, active_low)
    assert render(m, language=language) == expected_counter(language, kind, active_low)
