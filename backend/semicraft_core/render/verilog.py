"""Verilog-2001 renderer (WP-02, IR_SPEC §7 table, right column).

Language-specific hooks only: ``reg``/``wire`` inference (design rule 6 —
procedural driver -> ``reg``, everything else -> ``wire``, procedurally driven
output ports -> ``output reg`` in the ANSI port list), ``always @(posedge
...)`` / ``always @(*)``, plain ``case`` (with a verbose-level intent comment
when the IR asked for ``unique``, handled in base), plain ``parameter``, and
one ``localparam`` per enum member with the encoding values applied.
"""

from __future__ import annotations

from ..ir.nodes import EnumDecl, Port, PortDir, Signal
from .base import BaseRenderer, enum_layout


class VerilogRenderer(BaseRenderer):
    language = "verilog"
    supports_unique_case = False

    def always_ff_open(self, sensitivity: str) -> str:
        return f"always @({sensitivity}) begin"

    def always_comb_open(self) -> str:
        return "always @(*) begin"

    def case_keyword(self, unique: bool) -> str:
        return "case"

    def param_keyword(self, *, local: bool) -> str:
        return "localparam" if local else "parameter"

    def port_kind(self, port: Port) -> str:
        if port.dir is PortDir.OUTPUT and port.name in self.procedural:
            return "reg"
        return "wire"

    def signal_kind(self, sig: Signal) -> str:
        return "reg" if sig.name in self.procedural else "wire"

    def _emit_enum_decl(self, decl: EnumDecl) -> None:
        width, values = enum_layout(decl)
        members = [self.name(m) for m in decl.members]
        pad = max(len(m) for m in members)
        if self._docs_visible():
            self._emit(f"// {self.name(decl.name)}: {decl.encoding} encoding")
        for member, value in zip(members, values, strict=True):
            self._emit(
                f"localparam [{width - 1}:0] {member.ljust(pad)}"
                f" = {width}'b{value:0{width}b};"
            )
