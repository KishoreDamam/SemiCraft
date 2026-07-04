"""Comment-verbosity filtering: none / normal / verbose (design rule 7)."""

from __future__ import annotations

from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysComb,
    Assign,
    Comment,
    CommentLevel,
    Header,
    Module,
    Port,
    Ref,
    bit,
)
from semicraft_core.render import StyleOptions, render

HEADER = Header(
    license="as-is",
    config_hash="0" * 12,
    tool_version="0.1.0",
    description="test",
)


def _commented_module() -> Module:
    return Module(
        name="m",
        header=HEADER,
        ports=[
            Port("a", IN, bit(), doc="input operand"),
            Port("y", OUT, bit()),
        ],
        items=[
            Comment("top level note", CommentLevel.NORMAL),
            AlwaysComb(
                [
                    Comment("normal note", CommentLevel.NORMAL),
                    Comment("verbose note", CommentLevel.VERBOSE),
                    Assign(Ref("y"), Ref("a")),
                ]
            ),
        ],
    )


def test_verbosity_normal_default() -> None:
    out = render(_commented_module(), language="sv")
    assert "// top level note" in out
    assert "// normal note" in out
    assert "// verbose note" not in out
    assert "// input operand" in out  # port doc rendered at normal


def test_verbosity_verbose() -> None:
    out = render(
        _commented_module(),
        language="sv",
        style=StyleOptions(comment_verbosity="verbose"),
    )
    assert "// top level note" in out
    assert "// normal note" in out
    assert "// verbose note" in out
    assert "// input operand" in out


def test_verbosity_none_strips_comments_and_port_docs() -> None:
    out = render(
        _commented_module(),
        language="sv",
        style=StyleOptions(comment_verbosity="none"),
    )
    assert "top level note" not in out
    assert "normal note" not in out
    assert "verbose note" not in out
    assert "input operand" not in out
    # The file header banner is not a Comment node and always renders.
    assert out.startswith("// SemiCraft v0.1.0\n")
