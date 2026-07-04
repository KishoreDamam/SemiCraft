"""EnumDecl rendering in both languages with computed encoding values,
plus `unique case` handling (SV keyword vs Verilog intent comment)."""

from __future__ import annotations

from semicraft_core.ir import (
    IN,
    AlwaysComb,
    AlwaysFF,
    Assign,
    Case,
    CaseItem,
    ClockSpec,
    EnumDecl,
    EnumEncoding,
    EnumRef,
    Header,
    Module,
    Port,
    Ref,
    Signal,
    bit,
    vec,
)
from semicraft_core.render import StyleOptions, render

HEADER = Header(
    license="as-is",
    config_hash="0" * 12,
    tool_version="0.1.0",
    description="test",
)


def _enum_module(members: list[str], encoding: EnumEncoding, state_width: int) -> Module:
    return Module(
        name="m",
        header=HEADER,
        ports=[Port("clk", IN, bit())],
        items=[
            EnumDecl("state_t", members, encoding),
            Signal("state", vec(state_width)),
            AlwaysComb([Assign(Ref("state"), EnumRef("state_t", members[0]))]),
        ],
    )


MEMBERS3 = ["st_idle", "st_run", "st_done"]


def test_sv_enum_binary() -> None:
    out = render(_enum_module(MEMBERS3, EnumEncoding.BINARY, 2), language="sv")
    assert "    typedef enum logic [1:0] {\n" in out
    assert "        st_idle = 2'b00,\n" in out
    assert "        st_run  = 2'b01,\n" in out
    assert "        st_done = 2'b10\n" in out
    assert "    } state_t;\n" in out


def test_sv_enum_onehot() -> None:
    out = render(_enum_module(MEMBERS3, EnumEncoding.ONEHOT, 3), language="sv")
    assert "    typedef enum logic [2:0] {\n" in out
    assert "        st_idle = 3'b001,\n" in out
    assert "        st_run  = 3'b010,\n" in out
    assert "        st_done = 3'b100\n" in out


def test_sv_enum_gray() -> None:
    members = ["st_a", "st_b", "st_c", "st_d"]
    out = render(_enum_module(members, EnumEncoding.GRAY, 2), language="sv")
    assert "        st_a = 2'b00,\n" in out
    assert "        st_b = 2'b01,\n" in out
    assert "        st_c = 2'b11,\n" in out
    assert "        st_d = 2'b10\n" in out


def test_verilog_enum_binary_localparams() -> None:
    out = render(_enum_module(MEMBERS3, EnumEncoding.BINARY, 2), language="verilog")
    assert "    // state_t: binary encoding\n" in out
    assert "    localparam [1:0] st_idle = 2'b00;\n" in out
    assert "    localparam [1:0] st_run  = 2'b01;\n" in out
    assert "    localparam [1:0] st_done = 2'b10;\n" in out
    assert "typedef" not in out


def test_verilog_enum_onehot_and_gray_values() -> None:
    out = render(_enum_module(MEMBERS3, EnumEncoding.ONEHOT, 3), language="verilog")
    assert "    localparam [2:0] st_idle = 3'b001;\n" in out
    assert "    localparam [2:0] st_done = 3'b100;\n" in out
    members = ["st_a", "st_b", "st_c", "st_d"]
    out = render(_enum_module(members, EnumEncoding.GRAY, 2), language="verilog")
    assert "    localparam [1:0] st_c = 2'b11;\n" in out
    assert "    localparam [1:0] st_d = 2'b10;\n" in out


def _fsm_module() -> Module:
    """Two-state FSM exercising a full-coverage unique enum case."""
    return Module(
        name="m",
        header=HEADER,
        ports=[Port("clk", IN, bit())],
        items=[
            EnumDecl("state_t", ["s_a", "s_b"], EnumEncoding.BINARY),
            Signal("state", vec(1)),
            Signal("state_next", vec(1)),
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=None,
                reset_body=[],
                body=[Assign(Ref("state"), Ref("state_next"))],
            ),
            AlwaysComb(
                [
                    Case(
                        sel=Ref("state"),
                        items=[
                            CaseItem(
                                [EnumRef("state_t", "s_a")],
                                [Assign(Ref("state_next"), EnumRef("state_t", "s_b"))],
                            ),
                            CaseItem([EnumRef("state_t", "s_b")], []),
                        ],
                        unique=True,
                    )
                ]
            ),
        ],
    )


def test_sv_unique_case() -> None:
    out = render(_fsm_module(), language="sv")
    assert "        unique case (state)\n" in out
    assert "            s_a: state_next = s_b;\n" in out  # single-assign arm inline
    assert "            s_b: ;\n" in out  # empty arm
    assert "        endcase\n" in out


def test_verilog_plain_case_with_intent_comment_at_verbose() -> None:
    normal = render(_fsm_module(), language="verilog")
    assert "        case (state)\n" in normal
    assert "unique" not in normal
    verbose = render(
        _fsm_module(),
        language="verilog",
        style=StyleOptions(comment_verbosity="verbose"),
    )
    assert "// unique case intent: labels are mutually exclusive" in verbose
