"""Renderers and style engine that turn IR into SystemVerilog/Verilog text.

Public API (WP-02)::

    render(module, language="sv" | "verilog",
           style=StyleOptions(), include_wrapper=True) -> str

``render`` validates the IR first (IR_SPEC §6 runs before any rendering),
builds the style name map (raising :class:`StyleError` on post-transform
reserved-word collisions), and walks the tree with the language renderer.
``include_wrapper=False`` selects fragment mode (no ``module``/``endmodule``;
declarations are emitted as a comment block).
"""

from __future__ import annotations

from ..ir.nodes import Module
from ..ir.validate import validate
from .base import BaseRenderer
from .style import StyleError, StyleOptions
from .sv import SVRenderer
from .verilog import VerilogRenderer

_RENDERERS: dict[str, type[BaseRenderer]] = {
    "sv": SVRenderer,
    "verilog": VerilogRenderer,
}


def render(
    module: Module,
    language: str = "sv",
    style: StyleOptions | None = None,
    include_wrapper: bool = True,
) -> str:
    """Render ``module`` to source text in the requested language."""
    if language not in _RENDERERS:
        raise ValueError(f"unknown language {language!r}; expected 'sv' or 'verilog'")
    validate(module)
    renderer = _RENDERERS[language](module, style if style is not None else StyleOptions())
    return renderer.render(include_wrapper=include_wrapper)


__all__ = [
    "render",
    "StyleOptions",
    "StyleError",
    "BaseRenderer",
    "SVRenderer",
    "VerilogRenderer",
]
