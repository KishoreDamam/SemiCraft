"""SystemVerilog renderer (WP-02, IR_SPEC §7 table, left column).

Only language-specific hooks live here: ``logic`` everywhere,
``always_ff``/``always_comb``, ``unique case``, ``parameter int unsigned``,
and ``typedef enum logic [N-1:0]`` with encoding values applied. Everything
structural is inherited from :class:`~semicraft_core.render.base.BaseRenderer`.
"""

from __future__ import annotations

from ..ir.nodes import EnumDecl, Port, Signal
from .base import BaseRenderer, enum_layout


class SVRenderer(BaseRenderer):
    language = "sv"
    supports_unique_case = True

    def always_ff_open(self, sensitivity: str) -> str:
        return f"always_ff @({sensitivity}) begin"

    def always_comb_open(self) -> str:
        return "always_comb begin"

    def case_keyword(self, unique: bool) -> str:
        return "unique case" if unique else "case"

    def param_keyword(self, *, local: bool) -> str:
        return "localparam int unsigned" if local else "parameter int unsigned"

    def port_kind(self, port: Port) -> str:
        return "logic"

    def signal_kind(self, sig: Signal) -> str:
        return "logic"

    def _emit_enum_decl(self, decl: EnumDecl) -> None:
        width, values = enum_layout(decl)
        members = [self.name(m) for m in decl.members]
        pad = max(len(m) for m in members)
        self._emit(f"typedef enum logic [{width - 1}:0] {{")
        with self._indented():
            for i, (member, value) in enumerate(zip(members, values, strict=True)):
                comma = "," if i < len(members) - 1 else ""
                self._emit(f"{member.ljust(pad)} = {width}'b{value:0{width}b}{comma}")
        self._emit(f"}} {self.name(decl.name)};")
