"""Determinism, instance rendering, header banner, expression
parenthesization, and API error handling (WP-02)."""

from __future__ import annotations

import pytest
from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysComb,
    Assign,
    BinOp,
    BinOpKind,
    Const,
    Header,
    Instance,
    Module,
    Port,
    Ref,
    ResetKind,
    Signal,
    Ternary,
    UnaryOp,
    UnaryOpKind,
    bit,
)
from semicraft_core.render import render

from tests.render.test_golden_counter import build_counter

HEADER = Header(
    license="as-is",
    config_hash="0" * 12,
    tool_version="0.1.0",
    description="test",
)


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_render_is_deterministic(language: str) -> None:
    first = render(build_counter(ResetKind.ASYNC, active_low=True), language=language)
    second = render(build_counter(ResetKind.ASYNC, active_low=True), language=language)
    assert first == second  # byte-identical


def test_unknown_language_rejected() -> None:
    with pytest.raises(ValueError, match="unknown language"):
        render(build_counter(ResetKind.SYNC, active_low=True), language="vhdl")


def test_instance_rendering() -> None:
    m = Module(
        name="top",
        header=HEADER,
        ports=[Port("clk", IN, bit())],
        items=[
            Signal("q", bit()),
            Instance(
                module="sub",
                name="u_sub",
                params={"WIDTH": Const(8)},
                conns={"clk": Ref("clk"), "q": Ref("q")},
            ),
        ],
    )
    out = render(m, language="sv")
    assert (
        "    sub #(\n"
        "        .WIDTH(8)\n"
        "    ) u_sub (\n"
        "        .clk(clk),\n"
        "        .q(q)\n"
        "    );\n"
    ) in out


def test_header_banner_fields_and_no_timestamp() -> None:
    out = render(build_counter(ResetKind.ASYNC, active_low=True), language="sv")
    assert out.startswith("// SemiCraft v0.1.0\n")
    assert "// Snippet: counter (config hash: deadbeef1234)\n" in out
    assert "// Up counter\n" in out
    assert "without warranty of any kind" in out
    # No timestamps anywhere (determinism ground rule).
    assert "20" + "26" not in out


def test_nested_operator_expressions_fully_parenthesized() -> None:
    # y = a + (b * c): nested operator operand parenthesized, statement top
    # level unparenthesized (IR_SPEC §3.1).
    m = Module(
        name="m",
        header=HEADER,
        ports=[
            Port("a", IN, bit()),
            Port("b", IN, bit()),
            Port("c", IN, bit()),
            Port("y", OUT, bit()),
            Port("z", OUT, bit()),
        ],
        items=[
            AlwaysComb(
                [
                    Assign(
                        Ref("y"),
                        BinOp(
                            BinOpKind.ADD,
                            Ref("a"),
                            BinOp(BinOpKind.MUL, Ref("b"), Ref("c")),
                        ),
                    ),
                    Assign(
                        Ref("z"),
                        Ternary(
                            UnaryOp(UnaryOpKind.NOT_LOGICAL, Ref("a")),
                            Ref("b"),
                            Ref("c"),
                        ),
                    ),
                ]
            )
        ],
    )
    out = render(m, language="sv")
    assert "y = a + (b * c);" in out
    assert "z = (!a) ? b : c;" in out
