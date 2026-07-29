"""Deterministic checker/monitor/scoreboard SV generator (P3-06).

Turns the declarative specs in :mod:`semicraft_core.checkers.spec` into
SystemVerilog **text** directly — a small, self-contained emitter, the same
shape P3-05's assertion generator used to stay standalone. Unlike P3-05
(which emits :class:`~semicraft_core.tb.nodes.AssertProperty` nodes for
``render_tb`` to render later), this package owns its own tiny renderer: it
does not add nodes to ``semicraft_core.tb.nodes`` and does not touch
``render_tb``/``validate_tb``/``generate_tb``.

Three independent entry points, one per component family:

- :func:`generate_monitor` — a passive bundle-sampling module.
- :func:`generate_checker` — a module of procedural (``always``-block)
  protocol checks. **Not** SVA — see the module-vs-property distinction
  below.
- :func:`generate_scoreboard` — an expected-value-queue class, optionally
  paired with a thin wrapper module.

Procedural checks vs. concurrent SVA (read before wiring both generators into
the same TB): P3-05 (`semicraft_core.assertions`) emits *concurrent
assertions* (``name: assert property (@(posedge clk) ...) else $fatal(...);``)
which the SystemVerilog scheduler evaluates automatically against every
transition of every underlying signal, independent of procedural code order.
`generate_checker` here emits *procedural* checks — plain
``always @(posedge clk) if (...) $error(...);`` blocks — which only run at
the modeled clock edge and only see the values procedural code assigned by
then. They are not interchangeable: procedural checks are directed and
easier to read/step through in a waveform viewer; concurrent SVA composes
better and can catch violations between the checker's own clock edges. Use
whichever a directed TB's other components already lean on, or both.

Determinism: every ``generate_*`` function is pure — the same spec renders to
byte-identical text, with no timestamps, randomness, or dict-iteration-order
dependence. Signal names are taken verbatim; this module never rewrites an
identifier.

Verilator-friendly by construction: no ``uvm_*`` base classes, no ``program``
blocks, no ``randomize()``/constrained random, no ``fork``/loop constructs (so
the ``%Error-LIFETIME`` trap TB_SPEC §3.1 documents for ``TimeoutGuard``'s
forked counting loop does not apply here — nothing in this generator forks).
Verilator is not available on this host; the emitted SV has been reviewed but
is **not compile-verified locally** (see ``docs/CHECKERS.md``). Not wired
into ``generate_files`` — like P3-05, this lands standalone.
"""

from __future__ import annotations

from .spec import (
    CheckerItem,
    CheckerSpec,
    LatencyCheck,
    MonitorSpec,
    ResetPolarity,
    ResetValueCheck,
    ScoreboardSpec,
    ScoreboardWrapper,
    StabilityCheck,
)

__all__ = ["generate_monitor", "generate_checker", "generate_scoreboard"]

_INDENT = "    "


# ---------------------------------------------------------------------------
# Tiny indent-aware line accumulator (self-contained; mirrors tb/render_tb.py's
# _Writer without importing it, per the "own small emitter" design constraint)
# ---------------------------------------------------------------------------


class _Writer:
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


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _lit(value: int, width: int) -> str:
    """Sized decimal literal ``<width>'d<value>`` (mirrors DriveSignal/assertions)."""
    return f"{width}'d{value}"


def _sized(name: str, width: int) -> str:
    """``[width-1:0] name`` (or bare ``name`` when ``width <= 1``)."""
    if width <= 1:
        return name
    return f"[{width - 1}:0] {name}"


def _port_decl(name: str, width: int) -> str:
    """``input logic [width-1:0] name`` (or bare ``input logic name``)."""
    return f"input logic {_sized(name, width)}"


def _reg_decl(name: str, width: int) -> str:
    """``logic [width-1:0] name;`` (or bare ``logic name;``)."""
    return f"logic {_sized(name, width)};"


def _emit_port_list(w: _Writer, module: str, ports: list[str]) -> None:
    """Emit ``module <module> (\\n    <port>,\\n    ...\\n);`` for pre-formatted
    port declaration strings (already including the ``input``/``output``
    keyword)."""
    w.line(f"module {module} (")
    w.indent()
    for i, port in enumerate(ports):
        comma = "," if i < len(ports) - 1 else ""
        w.line(f"{port}{comma}")
    w.dedent()
    w.line(");")


def _assert_unique(names: list[str], what: str) -> None:
    """Raise ``ValueError`` on the first repeated name in ``names`` (order-stable)."""
    seen: set[str] = set()
    for name in names:
        if name in seen:
            raise ValueError(f"duplicate {what}: {name!r}")
        seen.add(name)


def _reset_asserted_expr(reset: ResetPolarity) -> str:
    """Boolean expression true while reset is currently asserted."""
    return f"!{reset.signal}" if reset.active_low else reset.signal


def _reset_deasserted_expr(reset: ResetPolarity) -> str:
    """Boolean expression true while reset is currently deasserted."""
    return reset.signal if reset.active_low else f"!{reset.signal}"


def _reset_deassert_edge_expr(reset: ResetPolarity) -> str:
    """Procedural reset-deassertion edge, off a one-cycle-delayed shadow reg.

    ``!<reset>_prev && <reset>`` (active-low: net rises 0->1 on release), or
    ``<reset>_prev && !<reset>`` (active-high: net falls 1->0 on release).
    Procedural analogue of the SVA generator's ``$rose``/``$fell`` edges.
    """
    prev = f"{reset.signal}_prev"
    if reset.active_low:
        return f"!{prev} && {reset.signal}"
    return f"{prev} && !{reset.signal}"


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------


def generate_monitor(spec: MonitorSpec) -> str:
    """Emit a passive bundle-sampling monitor module (pure; see module docstring).

    Renders an SV ``module`` with one ``input logic`` port per
    ``spec.clock``/``spec.fields`` entry and a single
    ``always @(posedge clock)`` block that ``$display``s a
    ``[%0t] <name>: field=%0d ...`` transaction line — under an
    ``if (qualifier)`` guard when ``spec.qualifier`` is given, unconditionally
    otherwise. Drives nothing: every port is an input.

    Raises :class:`ValueError` if two fields (or a field and the clock) share
    a name — the emitted module would otherwise declare the same port twice.
    """
    _assert_unique([spec.clock, *(f.name for f in spec.fields)], "monitor port name")

    w = _Writer()
    ports = [_port_decl(spec.clock, 1)]
    ports += [_port_decl(f.name, f.width) for f in spec.fields]
    _emit_port_list(w, spec.name, ports)
    w.blank()
    w.indent()

    if spec.fields:
        header = f"[%0t] {spec.name}: " + " ".join(f"{f.name}=%0d" for f in spec.fields)
    else:
        header = f"[%0t] {spec.name}"
    args = ", ".join(["$time", *(f.name for f in spec.fields)])

    qual_note = f" when {spec.qualifier}" if spec.qualifier is not None else ""
    w.line(
        f"// Passive monitor: samples the bundle on posedge {spec.clock}{qual_note}"
    )
    w.line(f"always @(posedge {spec.clock}) begin")
    w.indent()
    if spec.qualifier is not None:
        w.line(f"if ({spec.qualifier}) begin")
        w.indent()
        w.line(f'$display("{header}", {args});')
        w.dedent()
        w.line("end")
    else:
        w.line(f'$display("{header}", {args});')
    w.dedent()
    w.line("end")

    w.dedent()
    w.blank()
    w.line("endmodule")
    return w.text()


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


def _guard_prefix(reset: ResetPolarity | None, guarded: bool) -> str:
    """``"<not-in-reset> && "`` prefix for a guarded check, or ``""``."""
    if reset is None or not guarded:
        return ""
    return f"{_reset_deasserted_expr(reset)} && "


def _emit_checker_body(w: _Writer, spec: CheckerSpec) -> None:
    clock = spec.clock
    needs_reset_prev = spec.reset is not None and any(
        isinstance(item, ResetValueCheck) for item in spec.checks
    )
    if needs_reset_prev:
        assert spec.reset is not None
        prev = f"{spec.reset.signal}_prev"
        w.line(f"logic {prev};")
        w.line(f"always @(posedge {clock}) {prev} <= {spec.reset.signal};")
        w.blank()

    item: CheckerItem
    for i, item in enumerate(spec.checks):
        if i:
            w.blank()
        if isinstance(item, ResetValueCheck):
            if spec.reset is None:
                raise ValueError(
                    f"ResetValueCheck {item.name!r} requires CheckerSpec.reset"
                )
            edge = _reset_deassert_edge_expr(spec.reset)
            w.line(f"// {item.name}: {item.signal} known value on reset deassertion")
            w.line(f"always @(posedge {clock}) begin")
            w.indent()
            w.line(f"if ({edge}) begin")
            w.indent()
            w.line(f"if ({item.signal} !== {_lit(item.value, item.width)}) begin")
            w.indent()
            w.line(
                f'$error("CHECK FAIL: {item.name}: {item.signal} expected '
                f'{_lit(item.value, item.width)} on reset deassertion, got %0d", '
                f"{item.signal});"
            )
            w.dedent()
            w.line("end")
            w.dedent()
            w.line("end")
            w.dedent()
            w.line("end")
        elif isinstance(item, StabilityCheck):
            enable_prev = f"{item.name}_enable_prev"
            signal_prev = f"{item.name}_signal_prev"
            w.line(f"// {item.name}: {item.signal} stable one cycle after {item.enable} deasserts")
            w.line(f"logic {enable_prev};")
            w.line(_reg_decl(signal_prev, item.width))
            w.line(f"always @(posedge {clock}) begin")
            w.indent()
            w.line(f"{enable_prev} <= {item.enable};")
            w.line(f"{signal_prev} <= {item.signal};")
            w.dedent()
            w.line("end")
            w.line(f"always @(posedge {clock}) begin")
            w.indent()
            guard = _guard_prefix(spec.reset, item.guarded)
            w.line(
                f"if ({guard}!{enable_prev} && ({item.signal} !== {signal_prev})) begin"
            )
            w.indent()
            w.line(
                f'$error("CHECK FAIL: {item.name}: {item.signal} changed while '
                f'{item.enable} was deasserted last cycle (was %0d, now %0d)", '
                f"{signal_prev}, {item.signal});"
            )
            w.dedent()
            w.line("end")
            w.dedent()
            w.line("end")
        elif isinstance(item, LatencyCheck):
            if item.max_cycles <= 0:
                raise ValueError(
                    f"LatencyCheck {item.name!r} requires max_cycles > 0, "
                    f"got {item.max_cycles}"
                )
            pending = f"{item.name}_pending"
            wait = f"{item.name}_wait"
            w.line(
                f"// {item.name}: {item.response} must arrive within "
                f"{item.max_cycles} cycles of {item.request}"
            )
            w.line(f"logic {pending};")
            w.line(f"logic [31:0] {wait};")
            w.line(f"always @(posedge {clock}) begin")
            w.indent()
            reset_branch = spec.reset is not None and item.guarded
            if reset_branch:
                assert spec.reset is not None
                w.line(f"if ({_reset_asserted_expr(spec.reset)}) begin")
                w.indent()
                w.line(f"{pending} <= 1'b0;")
                w.line(f"{wait} <= 32'd0;")
                w.dedent()
                w.line(f"end else if ({pending}) begin")
            else:
                w.line(f"if ({pending}) begin")
            w.indent()
            w.line(f"if ({item.response}) begin")
            w.indent()
            w.line(f"{pending} <= 1'b0;")
            w.dedent()
            w.line(f"end else if ({wait} >= {_lit(item.max_cycles, 32)}) begin")
            w.indent()
            w.line(
                f'$error("CHECK FAIL: {item.name}: {item.response} did not '
                f'arrive within {item.max_cycles} cycles of {item.request}");'
            )
            w.line(f"{pending} <= 1'b0;")
            w.dedent()
            w.line("end else begin")
            w.indent()
            w.line(f"{wait} <= {wait} + 32'd1;")
            w.dedent()
            w.line("end")
            w.dedent()
            w.line(f"end else if ({item.request}) begin")
            w.indent()
            w.line(f"{pending} <= 1'b1;")
            w.line(f"{wait} <= 32'd0;")
            w.dedent()
            w.line("end")
            w.dedent()
            w.line("end")
        else:  # pragma: no cover - exhaustive over CheckerItem
            raise TypeError(f"unrenderable checker item: {item!r}")


def generate_checker(spec: CheckerSpec) -> str:
    """Emit a module of procedural protocol checks (pure; see module docstring).

    Ports: ``clock``, then ``reset`` (if the spec has one), then every
    ``spec.ports`` entry, in that order. Each ``spec.checks`` item renders as
    an independent ``always @(posedge clock)`` block (plus any shadow/state
    registers it needs), in item order.

    Raises :class:`ValueError` if: two ports (including clock/reset) share a
    name; two checks share a name (they seed generated register names, so a
    collision would double-declare a register); a :class:`~.spec.ResetValueCheck`
    is present but ``spec.reset`` is ``None``; or a
    :class:`~.spec.LatencyCheck.max_cycles` is not positive.
    """
    port_names = [spec.clock]
    if spec.reset is not None:
        port_names.append(spec.reset.signal)
    port_names += [p.name for p in spec.ports]
    _assert_unique(port_names, "checker port name")
    _assert_unique([c.name for c in spec.checks], "checker name")

    w = _Writer()
    ports = [_port_decl(spec.clock, 1)]
    if spec.reset is not None:
        ports.append(_port_decl(spec.reset.signal, 1))
    ports += [_port_decl(p.name, p.width) for p in spec.ports]
    _emit_port_list(w, spec.name, ports)
    w.blank()
    w.indent()
    _emit_checker_body(w, spec)
    w.dedent()
    w.blank()
    w.line("endmodule")
    return w.text()


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------


def _emit_scoreboard_class(w: _Writer, spec: ScoreboardSpec) -> None:
    t = spec.item_type
    w.line(f"class {spec.name};")
    w.indent()
    w.blank()
    w.line(f"{t} expected_q[$];")
    w.line("int unsigned match_count;")
    w.line("int unsigned mismatch_count;")
    w.blank()
    w.line("function new();")
    w.indent()
    w.line("match_count = 0;")
    w.line("mismatch_count = 0;")
    w.dedent()
    w.line("endfunction")
    w.blank()
    w.line(f"function void push_expected({t} item);")
    w.indent()
    w.line("expected_q.push_back(item);")
    w.dedent()
    w.line("endfunction")
    w.blank()
    w.line(f"function void compare({t} actual);")
    w.indent()
    w.line(f"{t} expected;")
    w.line("if (expected_q.size() == 0) begin")
    w.indent()
    w.line("mismatch_count++;")
    w.line(f'$error("{spec.name}: compare() called with an empty expected queue");')
    w.line("return;")
    w.dedent()
    w.line("end")
    w.line("expected = expected_q.pop_front();")
    w.line("if (actual !== expected) begin")
    w.indent()
    w.line("mismatch_count++;")
    w.line(f'$error("{spec.name}: mismatch: expected %0d, got %0d", expected, actual);')
    w.dedent()
    w.line("end else begin")
    w.indent()
    w.line("match_count++;")
    w.dedent()
    w.line("end")
    w.dedent()
    w.line("endfunction")
    w.blank()
    w.line("function void report();")
    w.indent()
    w.line(
        f'$display("{spec.name}: %0d match, %0d mismatch, %0d total", '
        "match_count, mismatch_count, match_count + mismatch_count);"
    )
    w.dedent()
    w.line("endfunction")
    w.blank()
    w.dedent()
    w.line("endclass")


def _emit_scoreboard_wrapper(w: _Writer, wrapper: ScoreboardWrapper, class_name: str) -> None:
    port_names = [wrapper.clock, wrapper.push_signal, wrapper.compare_signal]
    port_names += [p.name for p in wrapper.ports]
    _assert_unique(port_names, "scoreboard wrapper port name")

    ports = [
        _port_decl(wrapper.clock, 1),
        _port_decl(wrapper.push_signal, 1),
        _port_decl(wrapper.compare_signal, 1),
    ]
    ports += [_port_decl(p.name, p.width) for p in wrapper.ports]
    _emit_port_list(w, wrapper.module_name, ports)
    w.blank()
    w.indent()
    w.line(f"{class_name} sb;")
    w.blank()
    w.line("initial sb = new();")
    w.blank()
    w.line(f"always @(posedge {wrapper.clock}) begin")
    w.indent()
    w.line(f"if ({wrapper.push_signal}) begin")
    w.indent()
    w.line(f"sb.push_expected({wrapper.push_expr});")
    w.dedent()
    w.line("end")
    w.line(f"if ({wrapper.compare_signal}) begin")
    w.indent()
    w.line(f"sb.compare({wrapper.compare_expr});")
    w.dedent()
    w.line("end")
    w.dedent()
    w.line("end")
    w.blank()
    w.line("final begin")
    w.indent()
    w.line("sb.report();")
    w.dedent()
    w.line("end")
    w.dedent()
    w.blank()
    w.line("endmodule")


def generate_scoreboard(spec: ScoreboardSpec) -> str:
    """Emit a scoreboard class, optionally followed by a wrapper module (pure).

    The comparison logic always lives in the ``class`` — `expected_q[$]`` plus
    ``push_expected``/``compare``/``report()`` — because that is the reusable,
    hand-instantiable seam: a directed TB with custom multi-field sampling or
    multi-cycle capture windows can ``new()`` the class straight from its own
    ``initial``/``always`` blocks with full control. ``spec.wrapper`` adds a
    thin *module* on top only for the common case — one push qualifier, one
    compare qualifier, one value expression each, both sampled every clock
    edge — so a simple directed TB does not have to hand-write that wiring;
    it instantiates the class as field ``sb`` and reports totals in a
    ``final`` block. Complex sampling should skip the wrapper and drive the
    class directly.

    Raises :class:`ValueError` if ``spec.wrapper`` is given and two of its
    ports (including the implicit ``clock``/``push_signal``/``compare_signal``
    ports) share a name.
    """
    w = _Writer()
    _emit_scoreboard_class(w, spec)
    if spec.wrapper is not None:
        w.blank()
        _emit_scoreboard_wrapper(w, spec.wrapper, spec.name)
    return w.text()
