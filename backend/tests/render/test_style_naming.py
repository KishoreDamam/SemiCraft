"""Naming-transform tests: camel conversion, prefix/suffix, collisions (WP-02)."""

from __future__ import annotations

import pytest
from semicraft_core.ir import (
    IN,
    OUT,
    AlwaysComb,
    Assign,
    ContAssign,
    Header,
    Module,
    Port,
    Ref,
    Signal,
    bit,
)
from semicraft_core.render import StyleOptions, render
from semicraft_core.render.style import StyleError

HEADER = Header(
    license="as-is",
    config_hash="0" * 12,
    tool_version="0.1.0",
    description="test",
)


def _naming_module() -> Module:
    return Module(
        name="m",
        header=HEADER,
        ports=[
            Port("data_in", IN, bit()),
            Port("data_out", OUT, bit()),
        ],
        items=[
            Signal("count_next", bit()),
            AlwaysComb([Assign(Ref("count_next"), Ref("data_in"))]),
            ContAssign(Ref("data_out"), Ref("count_next")),
        ],
    )


def test_camel_convention() -> None:
    out = render(_naming_module(), language="sv", style=StyleOptions(naming="camel"))
    assert "logic countNext;" in out
    assert "countNext = dataIn;" in out
    assert "assign dataOut = countNext;" in out
    assert "count_next" not in out
    assert "data_in" not in out


def test_prefix_and_suffix() -> None:
    out = render(
        _naming_module(),
        language="sv",
        style=StyleOptions(prefix="io_", suffix="_x"),
    )
    assert "input  logic io_data_in_x," in out
    assert "logic io_count_next_x;" in out
    assert "assign io_data_out_x = io_count_next_x;" in out


def test_snake_default_is_identity() -> None:
    out = render(_naming_module(), language="sv")
    assert "logic count_next;" in out
    assert "count_next = data_in;" in out


def test_reserved_word_collision_raises() -> None:
    # Canonical name "ire" + prefix "w" renders "wire" -> reserved in both
    # languages; the style engine must refuse (IR_SPEC §6 rule 7 post-style).
    m = Module(
        name="m",
        header=HEADER,
        ports=[Port("a", IN, bit()), Port("y", OUT, bit())],
        items=[
            Signal("ire", bit()),
            AlwaysComb([Assign(Ref("ire"), Ref("a"))]),
            ContAssign(Ref("y"), Ref("ire")),
        ],
    )
    with pytest.raises(StyleError, match="wire"):
        render(m, language="sv", style=StyleOptions(prefix="w"))


def test_camel_rendered_name_collision_raises() -> None:
    # "x_y" and "x__y" both camel-convert to "xY" -> ambiguous output.
    m = Module(
        name="m",
        header=HEADER,
        ports=[Port("a", IN, bit())],
        items=[
            Signal("x_y", bit()),
            Signal("x__y", bit()),
            AlwaysComb(
                [Assign(Ref("x_y"), Ref("a")), Assign(Ref("x__y"), Ref("a"))]
            ),
        ],
    )
    with pytest.raises(StyleError, match="xY"):
        render(m, language="sv", style=StyleOptions(naming="camel"))
