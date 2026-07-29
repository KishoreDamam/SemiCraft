# SemiCraft Checker/Monitor/Scoreboard Scaffold Generator (P3-06)

**Owner:** verification core (`semicraft_core/checkers/`). Companion to
[TB_SPEC.md](TB_SPEC.md) (the TB IR family), [ASSERTIONS.md](ASSERTIONS.md)
(the P3-05 concurrent-SVA generator), and
[PLAN-semicraft-phases-2-8.md](PLAN-semicraft-phases-2-8.md) (Phase 3, P3-06).

A small, deterministic generator that turns declarative specs
(`semicraft_core.checkers.spec`) directly into SystemVerilog **scaffold
text** for three directed (not UVM, per PRD non-goal — no `uvm_*` base
classes, no factory, no `config_db`, no phasing) verification components:

- a passive bundle **monitor** module,
- a **checker** module of procedural protocol checks,
- an expected-value **scoreboard** class with an optional wrapper module.

It is a standalone package, same shape as P3-05: it is **not** yet wired into
`generate_files` — integration is a later WP. Unlike P3-05 (which emits
`AssertProperty` nodes for `render_tb` to render later), this package owns
its own tiny renderer and returns SV text directly — it does not add nodes to
`semicraft_core/tb/nodes.py` and does not touch `render_tb.py`,
`validate_tb`, or `generate_tb.py`.

## Design rules

Mirrors [TB_SPEC §2](TB_SPEC.md) / [IR_SPEC §2](IR_SPEC.md) /
[ASSERTIONS.md](ASSERTIONS.md): every spec type is a **frozen + slotted**
dataclass with full type annotations; sequence-valued fields accept any
`Sequence` and are stored as `tuple`. Generation is pure and deterministic —
the same spec yields byte-identical text, with no timestamps, randomness, or
dict-iteration-order dependence. Signal names are taken verbatim (already
styled by the caller) — the generator never rewrites identifiers.

**Documented approximation (consistent with TB_SPEC §5 / ASSERTIONS.md).**
Qualifiers, expressions, and item types (`qualifier`, `push_expr`,
`item_type`, ...) are opaque SystemVerilog text. The generator does not parse
them, so it cannot verify that identifiers used *inside* such text are
actually declared — the caller must list every referenced signal on the
relevant `fields`/`ports` sequence, or the emitted scaffold will not compile.

## Procedural checks vs. concurrent SVA (read before wiring both into one TB)

P3-05 (`semicraft_core.assertions`) emits **concurrent assertions**:

```systemverilog
name: assert property (@(posedge clk) disable iff (!rst_n) valid && !ready |=> valid)
    else $fatal(1, "SVA FAIL: name");
```

The SystemVerilog scheduler evaluates a concurrent assertion automatically
against every relevant signal transition, independent of procedural code
order, and `disable iff` disables its *entire* evaluation window (including
whatever sample feeds an operator like `$stable`'s "previous value").

`generate_checker` here (P3-06) emits **procedural** checks — plain
`always @(posedge clk) if (...) $error(...);` blocks — which only run at the
modeled clock edge and only see values procedural code has already assigned
by then. A `guarded` item's reset gate here only skips *that* evaluation; any
shadow/shift registers backing it (see `StabilityCheck`/`LatencyCheck` below)
keep updating every cycle regardless, which is a weaker approximation than
SVA `disable iff` — documented per item below.

The two generators are **not interchangeable**: procedural checks are
directed and easier to single-step through in a waveform viewer; concurrent
SVA composes better and can catch violations between a checker's own clock
edges. Pick whichever a directed TB's other components already lean on, or
use both side by side (they never collide — they emit different constructs
into different modules).

## Spec model (`semicraft_core.checkers.spec`)

Shared building blocks:

```python
Signal(name: str, width: int = 1)          # one input port: verbatim name + bit width
ResetPolarity(signal: str, active_low: bool)  # reset net + asserted polarity, no `sync`
```

`ResetPolarity` is deliberately narrower than `assertions.spec.ResetContext`:
procedural checks evaluate once per clock edge regardless of whether the
reset driving them is synchronous or asynchronous, so there is no `sync`
field to carry.

### Monitor

```python
MonitorSpec(name: str, clock: str, fields: Sequence[Signal], qualifier: str | None = None)
```

`generate_monitor(spec) -> str` emits one `module`: an `input logic` port per
`clock`/`fields` entry, and a single `always @(posedge clock)` block that
`$display`s a `[%0t] <name>: field=%0d ...` transaction line — under
`if (qualifier)` when given, unconditionally otherwise. Every port is an
input; the module drives nothing.

### Checker

```python
ResetValueCheck(name: str, signal: str, value: int, width: int)
StabilityCheck(name: str, signal: str, enable: str, width: int, guarded: bool = True)
LatencyCheck(name: str, request: str, response: str, max_cycles: int, guarded: bool = True)

CheckerSpec(
    name: str, clock: str, ports: Sequence[Signal],
    checks: Sequence[CheckerItem], reset: ResetPolarity | None = None,
)
```

`generate_checker(spec) -> str` emits one `module`: ports are `clock`, then
`reset` (if present), then every `ports` entry, in that order; each
`checks` item renders as an independent `always @(posedge clock)` block (plus
whatever shadow/state registers it needs), in item order.

| Item | Emits |
|---|---|
| `ResetValueCheck` | One `always` block. Edge-detects reset deassertion off a one-cycle-delayed shadow register of the reset net (`<reset>_prev`, declared **once** and shared across every `ResetValueCheck` in the spec), then `$error`s if `signal !== width'dvalue` at that edge. **Never guarded** — like its SVA counterpart, it is the check *about* reset, so gating it on reset would defeat its purpose. Requires `CheckerSpec.reset`; raises `ValueError` otherwise. |
| `StabilityCheck` | One register-update `always` block maintaining `<name>_enable_prev`/`<name>_signal_prev` (one-cycle-delayed shadows of `enable`/`signal`), plus a second `always` block: if `!<name>_enable_prev && (signal !== <name>_signal_prev)`, `$error`. When `guarded` and the spec has a reset, the check block is additionally prefixed with "reset currently deasserted" (`rst_n && ...` / `!rst && ...`) — the shadow registers themselves are **not** gated, only the comparison is (see the procedural-vs-SVA note above). |
| `LatencyCheck` | A `<name>_pending` flag + `<name>_wait` (32-bit) counter and one `always` block: `request` (while nothing pending) arms the countdown; `response` clears it; the counter reaching `max_cycles` before `response` arrives fires `$error` and clears the pending flag. Only one outstanding request is tracked — a second `request` while one is already pending is not separately queued. When `guarded` and the spec has a reset, an `if (<reset asserted>)` branch resets `pending`/`wait` to 0; `max_cycles` must be positive (`ValueError` otherwise). |

`generate_checker` raises `ValueError` on: a duplicate port name (including a
port colliding with `clock`/`reset.signal`); a duplicate check `name` (check
names seed generated register names, so a collision would double-declare a
register); a `ResetValueCheck` with no `CheckerSpec.reset`; or a
non-positive `LatencyCheck.max_cycles`.

### Scoreboard

```python
ScoreboardWrapper(
    module_name: str, clock: str,
    push_signal: str, push_expr: str,
    compare_signal: str, compare_expr: str,
    ports: Sequence[Signal] = (),
)
ScoreboardSpec(name: str, item_type: str, wrapper: ScoreboardWrapper | None = None)
```

`generate_scoreboard(spec) -> str` always emits an SV **class** —
`<item_type> expected_q[$]`, a `match_count`/`mismatch_count` pair,
`push_expected(item)` (push to the tail), `compare(actual)` (pop the head,
`!==` compare, bump the matching counter, `$error` on mismatch or on an empty
queue), and `report()` (`$display`s the pass/fail totals). `$error`/`$display`
format items with `%0d`, so `item_type` should be numeric or
numeric-compatible — a struct/class `item_type` will not format sensibly
(documented approximation).

**Why a class plus an optional thin wrapper module, not just one or the
other:** the comparison logic lives in the `class` because that is the
reusable, hand-instantiable seam — a directed TB with custom multi-field
sampling or multi-cycle capture windows can `new()` the class straight from
its own hand-written `initial`/`always` blocks with full control over when
`push_expected`/`compare` fire. `spec.wrapper` adds a thin *module* only for
the common case (one push qualifier, one compare qualifier, one value
expression each, both sampled every clock edge) so a simple directed TB does
not have to hand-write that wiring: it declares `<class> sb;`, `new()`s it in
an `initial`, drives `push_expected`/`compare` from an
`always @(posedge clock)` block, and calls `sb.report()` from a `final`
block. Complex sampling should skip the wrapper and drive the class
directly from hand-written procedural code.

`generate_scoreboard` raises `ValueError` if `spec.wrapper` is given and two
of its ports (including the implicit `clock`/`push_signal`/`compare_signal`
ports) share a name.

## Entry points

```python
from semicraft_core.checkers import generate_monitor, generate_checker, generate_scoreboard

monitor_text: str = generate_monitor(monitor_spec)
checker_text: str = generate_checker(checker_spec)
scoreboard_text: str = generate_scoreboard(scoreboard_spec)   # class [+ wrapper module]
```

All three are pure: the same spec renders to byte-identical text every call.

## Worked example

```python
from semicraft_core.checkers import (
    CheckerSpec, LatencyCheck, MonitorSpec, ResetPolarity, ResetValueCheck,
    ScoreboardSpec, ScoreboardWrapper, Signal, StabilityCheck,
    generate_checker, generate_monitor, generate_scoreboard,
)

RST_N = ResetPolarity(signal="rst_n", active_low=True)

mon = MonitorSpec(
    name="req_ack_mon", clock="clk",
    fields=[Signal("req", 1), Signal("ack", 1), Signal("data", 8)],
    qualifier="req && ack",
)
print(generate_monitor(mon))
```

emits:

```systemverilog
module req_ack_mon (
    input logic clk,
    input logic req,
    input logic ack,
    input logic [7:0] data
);

    // Passive monitor: samples the bundle on posedge clk when req && ack
    always @(posedge clk) begin
        if (req && ack) begin
            $display("[%0t] req_ack_mon: req=%0d ack=%0d data=%0d", $time, req, ack, data);
        end
    end

endmodule
```

```python
chk = CheckerSpec(
    name="req_ack_checker", clock="clk", reset=RST_N,
    ports=[Signal("busy", 1), Signal("data", 8), Signal("en", 1),
           Signal("req", 1), Signal("ack", 1)],
    checks=[
        ResetValueCheck("busy_reset", "busy", 0, 1),
        StabilityCheck("data_hold", "data", "en", 8),
        LatencyCheck("req_ack_latency", "req", "ack", 4),
    ],
)
print(generate_checker(chk))
```

emits (abridged — the `LatencyCheck` block is the pending/wait state machine
described above):

```systemverilog
module req_ack_checker (
    input logic clk,
    input logic rst_n,
    input logic busy,
    input logic [7:0] data,
    input logic en,
    input logic req,
    input logic ack
);

    logic rst_n_prev;
    always @(posedge clk) rst_n_prev <= rst_n;

    // busy_reset: busy known value on reset deassertion
    always @(posedge clk) begin
        if (!rst_n_prev && rst_n) begin
            if (busy !== 1'd0) begin
                $error("CHECK FAIL: busy_reset: busy expected 1'd0 on reset deassertion, got %0d", busy);
            end
        end
    end

    // data_hold: data stable one cycle after en deasserts
    logic data_hold_enable_prev;
    logic [7:0] data_hold_signal_prev;
    always @(posedge clk) begin
        data_hold_enable_prev <= en;
        data_hold_signal_prev <= data;
    end
    always @(posedge clk) begin
        if (rst_n && !data_hold_enable_prev && (data !== data_hold_signal_prev)) begin
            $error("CHECK FAIL: data_hold: data changed while en was deasserted last cycle (was %0d, now %0d)", data_hold_signal_prev, data);
        end
    end

    // req_ack_latency: ack must arrive within 4 cycles of req
    logic req_ack_latency_pending;
    logic [31:0] req_ack_latency_wait;
    always @(posedge clk) begin
        if (!rst_n) begin
            req_ack_latency_pending <= 1'b0;
            req_ack_latency_wait <= 32'd0;
        end else if (req_ack_latency_pending) begin
            if (ack) begin
                req_ack_latency_pending <= 1'b0;
            end else if (req_ack_latency_wait >= 32'd4) begin
                $error("CHECK FAIL: req_ack_latency: ack did not arrive within 4 cycles of req");
                req_ack_latency_pending <= 1'b0;
            end else begin
                req_ack_latency_wait <= req_ack_latency_wait + 32'd1;
            end
        end else if (req) begin
            req_ack_latency_pending <= 1'b1;
            req_ack_latency_wait <= 32'd0;
        end
    end

endmodule
```

```python
sb = ScoreboardSpec(
    name="req_ack_scoreboard", item_type="logic [7:0]",
    wrapper=ScoreboardWrapper(
        module_name="req_ack_scoreboard_wrap", clock="clk",
        push_signal="req", push_expr="data",
        compare_signal="ack", compare_expr="data",
    ),
)
print(generate_scoreboard(sb))
```

emits:

```systemverilog
class req_ack_scoreboard;

    logic [7:0] expected_q[$];
    int unsigned match_count;
    int unsigned mismatch_count;

    function new();
        match_count = 0;
        mismatch_count = 0;
    endfunction

    function void push_expected(logic [7:0] item);
        expected_q.push_back(item);
    endfunction

    function void compare(logic [7:0] actual);
        logic [7:0] expected;
        if (expected_q.size() == 0) begin
            mismatch_count++;
            $error("req_ack_scoreboard: compare() called with an empty expected queue");
            return;
        end
        expected = expected_q.pop_front();
        if (actual !== expected) begin
            mismatch_count++;
            $error("req_ack_scoreboard: mismatch: expected %0d, got %0d", expected, actual);
        end else begin
            match_count++;
        end
    endfunction

    function void report();
        $display("req_ack_scoreboard: %0d match, %0d mismatch, %0d total", match_count, mismatch_count, match_count + mismatch_count);
    endfunction

endclass

module req_ack_scoreboard_wrap (
    input logic clk,
    input logic req,
    input logic ack
);

    req_ack_scoreboard sb;

    initial sb = new();

    always @(posedge clk) begin
        if (req) begin
            sb.push_expected(data);
        end
        if (ack) begin
            sb.compare(data);
        end
    end

    final begin
        sb.report();
    end

endmodule
```

These three exact texts are asserted byte-for-byte by
`backend/tests/checkers/test_golden.py`.

## Documented approximations and limitations

- **Opaque text fields, not parsed.** `qualifier` (monitor), the
  `push_expr`/`compare_expr`/`push_signal`/`compare_signal` on
  `ScoreboardWrapper`, and every check's signal-name fields are raw
  SystemVerilog text/identifiers taken verbatim. This generator never parses
  them, so it cannot verify identifiers used *inside* opaque text (e.g. a
  monitor `qualifier` referencing a signal not listed in `fields`) resolve —
  the caller is responsible for listing every referenced signal on the
  relevant `fields`/`ports` sequence, exactly the same discipline TB_SPEC §5
  and ASSERTIONS.md document for their own opaque-text fields.
- **`StabilityCheck`'s guard is check-only, not window-wide.** SVA
  `disable iff` suppresses an assertion's entire evaluation, including the
  sample that feeds `$stable`'s notion of "previous value." The procedural
  `StabilityCheck` here keeps its shadow registers (`<name>_enable_prev`,
  `<name>_signal_prev`) updating every cycle regardless of reset/guard state;
  only the final comparison is skipped while in reset. In practice this
  rarely matters (the shadow values during reset are typically overwritten
  again once the design is out of reset before any check fires), but it is
  not bit-for-bit equivalent to the SVA `disable iff` semantics.
- **`LatencyCheck` tracks only one outstanding request.** There is no request
  queue — if `request` fires again while one is already pending, the second
  occurrence is not separately tracked (it neither restarts nor extends the
  existing countdown). A protocol that can have multiple requests in flight
  needs either a hand-written checker or several `LatencyCheck` instances
  wired to per-slot request/response signals.
- **Scoreboard `%0d` formatting assumes a numeric `item_type`.** A
  struct/class `item_type` will compile the class's method signatures fine,
  but the `$error`/`$display` calls' `%0d` format specifier will not print it
  meaningfully. A caller wanting to scoreboard structured transactions should
  give the class a numeric summary field to compare, or accept the cosmetic
  formatting gap.
- **`ScoreboardWrapper` uses `final begin ... end` to call `report()`.** This
  is a standard SystemVerilog construct Verilator has supported for several
  releases, but see below — it has not been exercised by an actual
  Verilator run in this environment.
- **Not compile-verified locally.** Verilator is not available on this
  development host (see `CLAUDE.md`), so none of the SV this generator
  produces — including the worked examples above — has been run through
  `verilator --timing --binary` or any other SV compiler. The output has
  been hand-reviewed for syntactic correctness and cross-checked against the
  idioms `tb/render_tb.py` and `semicraft_core/assertions/generate.py`
  already use, but "not compile-verified locally" should be read literally:
  compile-checking this family end-to-end is deferred to the P3-09 CI gate
  (or an earlier WP that wires a sandboxed Verilator run).
- **Not wired into `generate_files`.** Like P3-05, this package is standalone
  by design for this WP: no `ModuleDef`/`TbSpec` carries a
  `MonitorSpec`/`CheckerSpec`/`ScoreboardSpec` yet, and `generate_files` does
  not call into `semicraft_core.checkers`. Wiring these into the module
  metadata surface and the generated-file pipeline is a later WP's decision,
  not made here.
