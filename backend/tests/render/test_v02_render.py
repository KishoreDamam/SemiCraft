"""Golden renderings of the IR v0.2 nodes (P2-03): ``GenFor``, ``Memory``, and
``DataType.enum_type``, per IR_SPEC §10.

Inline-golden style like ``test_golden_counter.py``: full-file byte-exact
assertions for the structural cases, plus focused assertions for naming,
fragment mode, and determinism. The generate-keyword decision (P2-03) is
explicit ``generate``/``endgenerate`` in BOTH languages (IR_SPEC §10.1 text):
SV declares the genvar inline in the loop header, Verilog declares ``genvar i;``
before the block and increments with ``i = i + 1``.
"""

from __future__ import annotations

import pytest
from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysComb,
    AlwaysFF,
    Assign,
    Bit,
    ClockSpec,
    Const,
    ContAssign,
    EnumDecl,
    EnumEncoding,
    EnumRef,
    Header,
    If,
    Module,
    Param,
    Port,
    Ref,
    ResetKind,
    ResetSpec,
    Signal,
    UnaryOp,
    UnaryOpKind,
    bit,
    enum_t,
    genfor,
    mem,
    vec,
)
from semicraft_core.ir.validate import IRValidationError
from semicraft_core.render import StyleError, StyleOptions, render

HEADER = Header(
    license="as-is",
    config_hash="0" * 12,
    tool_version="0.1.0",
    description="test",
)

# Five-line banner + trailing blank line (STYLE_GUIDE §8), for the given name.
def _banner(name: str) -> str:
    return (
        "// SemiCraft v0.1.0\n"
        f"// Snippet: {name} (config hash: 000000000000)\n"
        "// test\n"
        "//\n"
        "// as-is\n"
        "\n"
    )


# --------------------------------------------------------------------------- #
# 1. GenFor with a ContAssign replication
# --------------------------------------------------------------------------- #


def _inv_array() -> Module:
    """Bitwise-invert each bit of a parameterized-width bus via a generate loop."""
    return Module(
        name="inv_array",
        header=HEADER,
        params=[Param("N", Const(4))],
        ports=[Port("din", IN, vec("N")), Port("dout", OUT, vec("N"))],
        items=[
            genfor(
                "bits",
                "i",
                Ref("N"),
                [
                    ContAssign(
                        Bit(Ref("dout"), Ref("i")),
                        UnaryOp(UnaryOpKind.NOT_BITWISE, Bit(Ref("din"), Ref("i"))),
                    )
                ],
            )
        ],
    )


INV_ARRAY_SV = _banner("inv_array") + """module inv_array #(
    parameter int unsigned N = 4
) (
    input  logic [N-1:0] din,
    output logic [N-1:0] dout
);

    generate
        for (genvar i = 0; i < N; i++) begin : gen_bits
            assign dout[i] = ~din[i];
        end
    endgenerate

endmodule
"""

INV_ARRAY_VERILOG = _banner("inv_array") + """module inv_array #(
    parameter N = 4
) (
    input  wire [N-1:0] din,
    output wire [N-1:0] dout
);

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : gen_bits
            assign dout[i] = ~din[i];
        end
    endgenerate

endmodule
"""


def test_genfor_contassign_sv() -> None:
    assert render(_inv_array(), language="sv") == INV_ARRAY_SV


def test_genfor_contassign_verilog() -> None:
    assert render(_inv_array(), language="verilog") == INV_ARRAY_VERILOG


# --------------------------------------------------------------------------- #
# 2. GenFor containing an AlwaysFF (reset composition unchanged inside generate)
# --------------------------------------------------------------------------- #


def _pipe() -> Module:
    """Per-bit register with a sync active-low reset, inside a generate loop."""
    return Module(
        name="pipe",
        header=HEADER,
        params=[Param("N", Const(4))],
        ports=[
            Port("clk", IN, bit()),
            Port("rst", IN, bit()),
            Port("d", IN, vec("N")),
            Port("q", OUT, vec("N")),
        ],
        items=[
            genfor(
                "stage",
                "i",
                Ref("N"),
                [
                    AlwaysFF(
                        clock=ClockSpec("clk"),
                        reset=ResetSpec("rst", kind=ResetKind.SYNC, active_low=True),
                        reset_body=[Assign(Bit(Ref("q"), Ref("i")), Const(0))],
                        body=[Assign(Bit(Ref("q"), Ref("i")), Bit(Ref("d"), Ref("i")))],
                    )
                ],
            )
        ],
    )


PIPE_SV = _banner("pipe") + """module pipe #(
    parameter int unsigned N = 4
) (
    input  logic         clk,
    input  logic         rst_n,
    input  logic [N-1:0] d,
    output logic [N-1:0] q
);

    generate
        for (genvar i = 0; i < N; i++) begin : gen_stage
            always_ff @(posedge clk) begin
                if (!rst_n) begin
                    q[i] <= 1'b0;
                end else begin
                    q[i] <= d[i];
                end
            end
        end
    endgenerate

endmodule
"""

PIPE_VERILOG = _banner("pipe") + """module pipe #(
    parameter N = 4
) (
    input  wire         clk,
    input  wire         rst_n,
    input  wire [N-1:0] d,
    output reg  [N-1:0] q
);

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : gen_stage
            always @(posedge clk) begin
                if (!rst_n) begin
                    q[i] <= 1'b0;
                end else begin
                    q[i] <= d[i];
                end
            end
        end
    endgenerate

endmodule
"""


def test_genfor_alwaysff_sv() -> None:
    assert render(_pipe(), language="sv") == PIPE_SV


def test_genfor_alwaysff_verilog() -> None:
    # ``q`` infers ``output reg`` even though its only driver is inside the
    # generate loop (procedural_targets descends into GenFor items).
    assert render(_pipe(), language="verilog") == PIPE_VERILOG


# --------------------------------------------------------------------------- #
# 3. Memory module: synchronous write + asynchronous read, parameterized W/DEPTH
# --------------------------------------------------------------------------- #


def _ram() -> Module:
    return Module(
        name="ram",
        header=HEADER,
        params=[Param("W", Const(8)), Param("DEPTH", Const(16))],
        ports=[
            Port("clk", IN, bit()),
            Port("we", IN, bit()),
            Port("waddr", IN, vec("DEPTH")),
            Port("wdata", IN, vec("W")),
            Port("raddr", IN, vec("DEPTH")),
            Port("rdata", OUT, vec("W")),
        ],
        items=[
            mem("storage", "W", "DEPTH", doc="RAM storage"),
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=None,
                reset_body=[],
                body=[
                    If(
                        Ref("we"),
                        then=[Assign(Bit(Ref("storage"), Ref("waddr")), Ref("wdata"))],
                    )
                ],
            ),
            ContAssign(Ref("rdata"), Bit(Ref("storage"), Ref("raddr"))),
        ],
    )


RAM_SV = _banner("ram") + """module ram #(
    parameter int unsigned W = 8,
    parameter int unsigned DEPTH = 16
) (
    input  logic             clk,
    input  logic             we,
    input  logic [DEPTH-1:0] waddr,
    input  logic [W-1:0]     wdata,
    input  logic [DEPTH-1:0] raddr,
    output logic [W-1:0]     rdata
);

    logic [W-1:0] storage [DEPTH];  // RAM storage

    always_ff @(posedge clk) begin
        if (we) begin
            storage[waddr] <= wdata;
        end
    end

    assign rdata = storage[raddr];

endmodule
"""

RAM_VERILOG = _banner("ram") + """module ram #(
    parameter W = 8,
    parameter DEPTH = 16
) (
    input  wire             clk,
    input  wire             we,
    input  wire [DEPTH-1:0] waddr,
    input  wire [W-1:0]     wdata,
    input  wire [DEPTH-1:0] raddr,
    output wire [W-1:0]     rdata
);

    reg [W-1:0] storage [0:DEPTH-1];  // RAM storage

    always @(posedge clk) begin
        if (we) begin
            storage[waddr] <= wdata;
        end
    end

    assign rdata = storage[raddr];

endmodule
"""


def test_memory_sync_write_async_read_sv() -> None:
    assert render(_ram(), language="sv") == RAM_SV


def test_memory_sync_write_async_read_verilog() -> None:
    # SV element storage is always ``logic``; Verilog is always ``reg`` (memories
    # are procedurally written, rule 9) — never ``wire``. Array dim differs:
    # SV ``[DEPTH]``, Verilog ``[0:DEPTH-1]``.
    assert render(_ram(), language="verilog") == RAM_VERILOG


def test_memory_literal_depth_folds_verilog_high_index() -> None:
    m = Module(
        name="rom",
        header=HEADER,
        ports=[Port("clk", IN, bit()), Port("we", IN, bit())],
        items=[
            mem("data", 8, 16),
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=None,
                reset_body=[],
                body=[
                    If(Ref("we"), then=[Assign(Bit(Ref("data"), Const(0)), Const(0))])
                ],
            ),
        ],
    )
    # SV keeps element count ``[16]``; Verilog folds to a concrete high index.
    assert "logic [7:0] data [16];" in render(m, language="sv")
    assert "reg [7:0] data [0:15];" in render(m, language="verilog")


# --------------------------------------------------------------------------- #
# 4. DataType.enum_type — typed enum signals
# --------------------------------------------------------------------------- #


def _fsm_typed(encoding: EnumEncoding) -> Module:
    """Enum-typed state signal AND an enum-typed output port."""
    members = ["st_idle", "st_run", "st_done"]
    return Module(
        name="fsm",
        header=HEADER,
        ports=[Port("clk", IN, bit()), Port("cur", OUT, enum_t("state_t"))],
        items=[
            EnumDecl("state_t", members, encoding),
            Signal("state", enum_t("state_t")),
            AlwaysComb([Assign(Ref("state"), EnumRef("state_t", "st_idle"))]),
            ContAssign(Ref("cur"), Ref("state")),
        ],
    )


def test_enum_type_sv_uses_typedef_name() -> None:
    out = render(_fsm_typed(EnumEncoding.BINARY), language="sv")
    # SV declares both the signal and the port with the typedef name, no range.
    assert "    output state_t cur\n" in out
    assert "    state_t state;\n" in out


def test_enum_type_verilog_plain_vector_binary() -> None:
    out = render(_fsm_typed(EnumEncoding.BINARY), language="verilog")
    # Verilog ignores enum_type: plain vector of the layout width. Kind is
    # inferred per driver — ``state`` (always_comb) is ``reg``; ``cur``
    # (ContAssign) is ``wire``.
    assert "    output wire [1:0] cur\n" in out
    assert "    reg [1:0] state;\n" in out
    # No SV typedef leaks into Verilog: no ``typedef`` and no typed declaration
    # (the ``state_t`` name still legitimately appears in the localparam-group
    # header comment, so we can't assert its total absence).
    assert "typedef" not in out
    assert "state_t state" not in out
    assert "state_t cur" not in out


def test_enum_type_verilog_onehot_layout_width() -> None:
    out = render(_fsm_typed(EnumEncoding.ONEHOT), language="verilog")
    # 3 members, onehot -> 3-bit layout (reuses enum_layout; not duplicated).
    assert "    output wire [2:0] cur\n" in out
    assert "    reg [2:0] state;\n" in out


# --------------------------------------------------------------------------- #
# 5. Naming: gen_ prefix rule, genvar through camel, reserved-word collision
# --------------------------------------------------------------------------- #


def _tap_module(label: str, genvar: str = "i") -> Module:
    return Module(
        name="taps",
        header=HEADER,
        ports=[Port("a", IN, vec(4)), Port("b", OUT, vec(4))],
        items=[
            genfor(
                label,
                genvar,
                4,
                [ContAssign(Bit(Ref("b"), Ref(genvar)), Bit(Ref("a"), Ref(genvar)))],
            )
        ],
    )


def test_genfor_label_gets_gen_prefix_when_missing() -> None:
    out = render(_tap_module("bits"), language="sv")
    assert "begin : gen_bits" in out


def test_genfor_label_keeps_gen_prefix_when_present() -> None:
    out = render(_tap_module("gen_taps"), language="sv")
    assert "begin : gen_taps" in out
    assert "gen_gen_taps" not in out


def test_genvar_through_camel_naming() -> None:
    out = render(
        _tap_module("bits", genvar="my_idx"),
        language="sv",
        style=StyleOptions(naming="camel"),
    )
    assert "for (genvar myIdx = 0; myIdx < 4; myIdx++) begin : genBits" in out
    assert "assign b[myIdx] = a[myIdx];" in out


def test_reserved_word_genvar_raises() -> None:
    m = Module(
        name="taps",
        header=HEADER,
        ports=[Port("a", IN, vec(4)), Port("b", OUT, vec(4))],
        items=[
            genfor(
                "bits",
                "wire",  # reserved word as a genvar name
                4,
                [ContAssign(Bit(Ref("b"), Ref("wire")), Bit(Ref("a"), Ref("wire")))],
            )
        ],
    )
    with pytest.raises(IRValidationError):
        render(m, language="sv")


def test_genvar_reserved_after_style_transform_raises() -> None:
    # A canonical-legal genvar that a style suffix turns into a reserved word is
    # caught by the post-transform reserved-word check (StyleError).
    m = _tap_module("bits", genvar="ge")
    with pytest.raises(StyleError):
        render(m, language="sv", style=StyleOptions(suffix="nerate"))


# --------------------------------------------------------------------------- #
# 6. Fragment mode with a GenFor and a Memory
# --------------------------------------------------------------------------- #


def _fragment_module() -> Module:
    return Module(
        name="frag",
        header=HEADER,
        params=[Param("N", Const(4))],
        ports=[Port("din", IN, vec("N")), Port("dout", OUT, vec("N"))],
        items=[
            mem("buf_mem", "N", 8, doc="ring buffer"),
            genfor(
                "bits",
                "i",
                Ref("N"),
                [ContAssign(Bit(Ref("dout"), Ref("i")), Bit(Ref("din"), Ref("i")))],
            ),
        ],
    )


def test_fragment_mode_genfor_and_memory_sv() -> None:
    out = render(_fragment_module(), language="sv", include_wrapper=False)
    # No module wrapper.
    assert "module frag" not in out
    assert "endmodule" not in out
    # Memory is a declaration -> commented in the declarations block.
    assert "//     logic [N-1:0] buf_mem [8];  // ring buffer" in out
    # GenFor is logic -> emitted as real generate/endgenerate.
    assert "generate\n" in out
    assert "    for (genvar i = 0; i < N; i++) begin : gen_bits\n" in out
    assert "endgenerate\n" in out


def test_fragment_mode_genfor_and_memory_verilog() -> None:
    out = render(_fragment_module(), language="verilog", include_wrapper=False)
    assert "//     reg [N-1:0] buf_mem [0:7];  // ring buffer" in out
    assert "genvar i;\n" in out
    assert "    for (i = 0; i < N; i = i + 1) begin : gen_bits\n" in out


# --------------------------------------------------------------------------- #
# 7. Determinism — rendering twice is byte-identical
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
@pytest.mark.parametrize(
    "builder",
    [_inv_array, _pipe, _ram, lambda: _fsm_typed(EnumEncoding.BINARY)],
)
def test_v02_render_is_deterministic(language: str, builder) -> None:
    m = builder()
    assert render(m, language=language) == render(m, language=language)
