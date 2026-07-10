"""Render a :class:`~.nodes.TbModule` to SystemVerilog testbench text.

SystemVerilog **only** (Verilator-compatible), even when the DUT was rendered as
Verilog-2001: a ``.sv`` testbench instantiating a ``.v`` module compiles fine
under Verilator (mixed-language elaboration). See docs/TB_SPEC.md.

Deterministic: no timestamps, no randomness — identical ``TbModule`` in, identical
text out (release criterion §1). The output shape is fixed:

    <banner>                       // mirrors the RTL header (config hash + disclaimer)

    `timescale 1ns/1ps

    module <dut>_tb;
        <net declarations>

        <clock generator>

        <DUT instance>

        initial begin
            <stimulus + self-checking assertions>
        end
    endmodule
"""

from __future__ import annotations

from .nodes import (
    ClockGen,
    Decl,
    Delay,
    Display,
    DriveSignal,
    DutInstance,
    ExpectSignal,
    Finish,
    Initial,
    Stmt,
    TbComment,
    TbModule,
    WaitCycles,
)

_INDENT = "    "
_CLOCK_NAME = "clk"  # the styled clock net; drives WaitCycles edge expressions


def _lit(value: int, width: int) -> str:
    """Size a literal to ``width`` bits as a decimal-based SV constant."""
    return f"{width}'d{value}"


def _decl_line(d: Decl) -> str:
    if d.width <= 1:
        return f"logic {d.name};"
    return f"logic [{d.width - 1}:0] {d.name};"


class _Writer:
    """Tiny indent-aware line accumulator (mirrors the RTL renderer's style)."""

    def __init__(self) -> None:
        self._lines: list[str] = []
        self._level = 0

    def line(self, text: str = "") -> None:
        self._lines.append(_INDENT * self._level + text if text else "")

    def blank(self) -> None:
        if self._lines and self._lines[-1] != "":
            self._lines.append("")

    def indent(self) -> None:
        self._level += 1

    def dedent(self) -> None:
        self._level -= 1

    def text(self) -> str:
        return "\n".join(self._lines) + "\n"


def _emit_clock(w: _Writer, clock: ClockGen) -> None:
    w.line("// Free-running clock")
    w.line(f"initial {clock.signal} = 1'b0;")
    w.line(f"always #{clock.half_period_ns} {clock.signal} = ~{clock.signal};")


def _emit_dut(w: _Writer, dut: DutInstance) -> None:
    w.line("// Device under test")
    if not dut.connections:
        w.line(f"{dut.module} {dut.instance} ();")
        return
    pad = max(len(port) for port, _ in dut.connections)
    w.line(f"{dut.module} {dut.instance} (")
    w.indent()
    for i, (port, net) in enumerate(dut.connections):
        comma = "," if i < len(dut.connections) - 1 else ""
        w.line(f".{port.ljust(pad)} ({net}){comma}")
    w.dedent()
    w.line(");")


def _emit_stmt(w: _Writer, s: Stmt) -> None:
    if isinstance(s, TbComment):
        w.line(f"// {s.text}")
    elif isinstance(s, DriveSignal):
        w.line(f"{s.signal} = {_lit(s.value, s.width)};")
    elif isinstance(s, Delay):
        w.line(f"#{s.ns};")
    elif isinstance(s, WaitCycles):
        if s.n == 1:
            w.line(f"@({s.edge} {_CLOCK_NAME});")
        else:
            w.line(f"repeat ({s.n}) @({s.edge} {_CLOCK_NAME});")
    elif isinstance(s, ExpectSignal):
        w.line(f"if ({s.signal} !== {_lit(s.expected, s.width)}) begin")
        w.indent()
        w.line(
            f'$fatal(1, "SMOKE FAIL: {s.signal} at {s.cycle_label} '
            f'expected {s.expected}, got %0d", {s.signal});'
        )
        w.dedent()
        w.line("end")
    elif isinstance(s, Display):
        w.line(f'$display("{s.message}");')
    elif isinstance(s, Finish):
        w.line("$finish;")
    else:  # pragma: no cover - exhaustive over the Stmt union
        raise TypeError(f"unrenderable TB statement: {s!r}")


def _emit_initial(w: _Writer, initial: Initial) -> None:
    w.line("// Stimulus and self-checking assertions")
    w.line("initial begin")
    w.indent()
    for s in initial.stmts:
        _emit_stmt(w, s)
    w.dedent()
    w.line("end")


def render_tb(tb: TbModule) -> str:
    """Render ``tb`` to SystemVerilog testbench source text."""
    w = _Writer()
    for banner_line in tb.banner:
        w.line(banner_line)
    w.blank()
    w.line("`timescale 1ns/1ps")
    w.blank()
    w.line(f"module {tb.name};")
    w.indent()
    for d in tb.decls:
        w.line(_decl_line(d))
    w.blank()
    _emit_clock(w, tb.clock)
    w.blank()
    _emit_dut(w, tb.dut)
    w.blank()
    _emit_initial(w, tb.initial)
    w.dedent()
    w.blank()
    w.line("endmodule")
    return w.text()


__all__ = ["render_tb"]
