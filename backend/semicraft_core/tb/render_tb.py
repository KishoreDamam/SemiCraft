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

        <reset sequence process>        // only when TbModule.reset_seq is set

        <task declarations>             // only when TbModule.tasks is non-empty

        initial begin
            <stimulus + self-checking assertions>
        end

        <concurrent SVA assertions>     // only when TbModule.asserts is non-empty
    endmodule

The P3-01 optional sections (reset_seq / tasks / asserts) are omitted entirely
when absent, so P2 smoke constructions render byte-identically to before.
"""

from __future__ import annotations

from .nodes import (
    AssertProperty,
    CallTask,
    ClockGen,
    Decl,
    Delay,
    Display,
    DriveSignal,
    Dump,
    DutInstance,
    ExpectSignal,
    Finish,
    ForkJoin,
    IfTb,
    Initial,
    RepeatBlock,
    ResetSeq,
    Stmt,
    Task,
    TbComment,
    TbModule,
    TimeoutGuard,
    WaitCycles,
    WaitUntil,
)

_INDENT = "    "
_CLOCK_NAME = "clk"  # the styled clock net; drives WaitCycles edge expressions

# ForkJoin.join discipline -> SystemVerilog join keyword (TB_SPEC §3.1).
_JOIN_KEYWORD = {"all": "join", "any": "join_any", "none": "join_none"}


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


def _emit_block(w: _Writer, stmts: tuple[Stmt, ...], scope: str) -> None:
    """Emit ``stmts`` one indent level deeper (the body of a begin/end block)."""
    w.indent()
    for s in stmts:
        _emit_stmt(w, s, scope)
    w.dedent()


def _emit_stmt(w: _Writer, s: Stmt, scope: str) -> None:
    """Emit one statement. ``scope`` is the enclosing TB module name (the
    ``$dumpvars`` scope for :class:`Dump`)."""
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
    elif isinstance(s, WaitUntil):
        w.line(f"wait ({s.condition_text});")
    elif isinstance(s, ForkJoin):
        w.line("fork")
        w.indent()
        for branch in s.branches:
            w.line("begin")
            _emit_block(w, branch, scope)
            w.line("end")
        w.dedent()
        w.line(_JOIN_KEYWORD[s.join])
    elif isinstance(s, RepeatBlock):
        w.line(f"repeat ({s.count}) begin")
        _emit_block(w, s.stmts, scope)
        w.line("end")
    elif isinstance(s, IfTb):
        w.line(f"if ({s.condition_text}) begin")
        _emit_block(w, s.then, scope)
        if s.else_ is None:
            w.line("end")
        else:
            w.line("end else begin")
            _emit_block(w, s.else_, scope)
            w.line("end")
    elif isinstance(s, TimeoutGuard):
        # Forked watchdog: a hung DUT fails loudly instead of stalling the sim.
        w.line("fork")
        w.indent()
        w.line("begin")
        w.indent()
        w.line(f"repeat ({s.cycles}) @(posedge {_CLOCK_NAME});")
        w.line(f'$fatal(1, "{s.message}");')
        w.dedent()
        w.line("end")
        w.dedent()
        w.line("join_none")
    elif isinstance(s, Dump):
        w.line(f'$dumpfile("{s.file}");')
        w.line(f"$dumpvars({s.levels}, {scope});")
    elif isinstance(s, CallTask):
        w.line(f"{s.name}();")
    else:  # pragma: no cover - exhaustive over the Stmt union
        raise TypeError(f"unrenderable TB statement: {s!r}")


def _emit_reset_seq(w: _Writer, rs: ResetSeq, clock: str) -> None:
    """Declarative reset process: assert at time 0, hold, deassert."""
    assert_level = 0 if rs.active_low else 1
    deassert_level = 1 - assert_level
    w.line("// Reset sequence")
    w.line("initial begin")
    w.indent()
    w.line(f"{rs.signal} = {_lit(assert_level, 1)};")
    if rs.cycles == 1:
        w.line(f"@(posedge {clock});")
    else:
        w.line(f"repeat ({rs.cycles}) @(posedge {clock});")
    w.line(f"{rs.signal} = {_lit(deassert_level, 1)};")
    w.dedent()
    w.line("end")


def _emit_task(w: _Writer, task: Task, scope: str) -> None:
    w.line(f"task {task.name};")
    _emit_block(w, task.stmts, scope)
    w.line("endtask")


def _emit_assert(w: _Writer, a: AssertProperty) -> None:
    guard = f"disable iff ({a.disable_iff}) " if a.disable_iff is not None else ""
    w.line(f"{a.name}: assert property (@(posedge {a.clock}) {guard}{a.property_text})")
    w.indent()
    w.line(f'else $fatal(1, "SVA FAIL: {a.name}");')
    w.dedent()


def _emit_initial(w: _Writer, initial: Initial, scope: str) -> None:
    w.line("// Stimulus and self-checking assertions")
    w.line("initial begin")
    _emit_block(w, initial.stmts, scope)
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
    if tb.reset_seq is not None:
        w.blank()
        _emit_reset_seq(w, tb.reset_seq, tb.clock.signal)
    for task in tb.tasks:
        w.blank()
        _emit_task(w, task, tb.name)
    w.blank()
    _emit_initial(w, tb.initial, tb.name)
    if tb.asserts:
        w.blank()
        w.line("// Concurrent assertions (SVA)")
        for a in tb.asserts:
            _emit_assert(w, a)
    w.dedent()
    w.blank()
    w.line("endmodule")
    return w.text()


__all__ = ["render_tb"]
