"""Assignment operator selection by context (design rule 3) and
reg/wire inference incl. `output reg` (design rule 6)."""

from __future__ import annotations

from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysComb,
    AlwaysFF,
    Assign,
    ClockSpec,
    ContAssign,
    Header,
    Module,
    Port,
    Ref,
    Signal,
    bit,
)
from semicraft_core.render import render

HEADER = Header(
    license="as-is",
    config_hash="0" * 12,
    tool_version="0.1.0",
    description="test",
)

# The single shared Assign node: operator is chosen purely by context.
_ASSIGN = Assign(Ref("q"), Ref("d"))


def test_assign_in_always_ff_is_nonblocking() -> None:
    m = Module(
        name="m",
        header=HEADER,
        ports=[Port("clk", IN, bit()), Port("d", IN, bit()), Port("q", OUT, bit())],
        items=[AlwaysFF(clock=ClockSpec("clk"), reset=None, reset_body=[], body=[_ASSIGN])],
    )
    for language in ("sv", "verilog"):
        out = render(m, language=language)
        assert "q <= d;" in out
        assert "q = d;" not in out


def test_same_assign_in_always_comb_is_blocking() -> None:
    m = Module(
        name="m",
        header=HEADER,
        ports=[Port("d", IN, bit()), Port("q", OUT, bit())],
        items=[AlwaysComb([_ASSIGN])],
    )
    for language in ("sv", "verilog"):
        out = render(m, language=language)
        assert "q = d;" in out
        assert "q <= d;" not in out


def test_cont_assign_uses_assign_keyword() -> None:
    m = Module(
        name="m",
        header=HEADER,
        ports=[Port("d", IN, bit()), Port("q", OUT, bit())],
        items=[ContAssign(Ref("q"), Ref("d"))],
    )
    out = render(m, language="sv")
    assert "assign q = d;" in out


def _inference_module() -> Module:
    """q: FF-driven output; y: assign-driven output; t: comb-driven signal;
    u: assign-driven signal."""
    return Module(
        name="m",
        header=HEADER,
        ports=[
            Port("clk", IN, bit()),
            Port("d", IN, bit()),
            Port("q", OUT, bit()),
            Port("y", OUT, bit()),
        ],
        items=[
            Signal("t", bit()),
            Signal("u", bit()),
            AlwaysFF(
                clock=ClockSpec("clk"),
                reset=None,
                reset_body=[],
                body=[Assign(Ref("q"), Ref("d"))],
            ),
            AlwaysComb([Assign(Ref("t"), Ref("d"))]),
            ContAssign(Ref("u"), Ref("d")),
            ContAssign(Ref("y"), Ref("t")),
        ],
    )


def test_verilog_reg_wire_inference() -> None:
    out = render(_inference_module(), language="verilog")
    # Procedurally driven output port -> output reg in the ANSI port list.
    assert "output reg  q," in out
    # Continuous-assign driven output -> wire.
    assert "output wire y" in out
    # Inputs are wires.
    assert "input  wire clk," in out
    # Internal signals: procedural -> reg, continuous -> wire.
    assert "    reg t;" in out
    assert "    wire u;" in out


def test_sv_uses_logic_everywhere() -> None:
    out = render(_inference_module(), language="sv")
    assert "reg" not in out.replace("// SemiCraft", "")
    assert "wire" not in out
    assert "output logic q," in out
    assert "output logic y" in out
    assert "    logic t;" in out
    assert "    logic u;" in out
