# SemiCraft Testbench IR Specification

**Version 2.3 (Phase 4, P4-01).** Owner: verification core (`semicraft_core/tb/`).

The testbench (TB) IR is a small, frozen-dataclass node family for directed
**SystemVerilog** testbenches, entirely separate from the synthesizable IR
(`semicraft_core/ir/`, see [IR_SPEC.md](IR_SPEC.md)). It began (P2-13) as a tiny
"smoke" set — clock, reset, per-cycle drives, self-checking expects — that
`generate_tb` still uses to emit compile-checked smoke testbenches. P3-01 extended
it into the full Phase 3 family (fork/join, loops, conditionals, timeout
watchdog, waveform dump, reusable tasks, an SVA-property stub) and added a
validator (`validate_tb`). P3-02 landed the renderers: `render_tb` now renders
**every** node in the family, and a sim-script emitter (`tb/scripts.py`)
produces a deterministic `run.sh`/`Makefile` pair driving the same Verilator
flow as the sim runner.

The stable public seams are unchanged:
`semicraft_core.tb.generate_tb(module_def, opts, rtl_module) -> str`,
`semicraft_core.tb.render_tb(TbModule) -> str`, and the
`GeneratedFile(kind="tb", path="<module>_tb.sv")` output of `generate_files`.

## Changelog

- **v2.3 (P4-01):** the rendered clock net name is now threaded through the
  statement emitters from `TbModule.clock` instead of a module-level
  `_CLOCK_NAME = "clk"` constant (new §7a, normative). Every emitted testbench
  was uncompilable under any non-default naming style; generator-side only, and
  byte-identical at the default style, so no golden file changed.
- **v2.2 (P3-09a):** reset-deassertion race fixed — the deassert drive is now
  preceded by a `#1` settle so it never shares a timestep with the rising edge
  that ends the reset hold (new §6a, normative). Fixes 17/165 golden TBs that
  failed the full-matrix run gate; generator-side only, no `TbSpec` expected
  value changed.
- **v2.1 (P3-02):** renderers for the full node family — `_emit_stmt` handles
  every `Stmt` (no longer raises on P3 nodes); module-level `Task`,
  `AssertProperty`, and `ResetSeq` render as optional sections (omitted when
  absent, keeping P2 goldens byte-identical). New `tb/scripts.py`
  (`emit_run_script` / `emit_makefile`), exported from `semicraft_core.tb`.
  `generate_tb` did **not** adopt `ResetSeq` (see §3.2 note).
- **v2 (P3-01):** full node family — new statements `WaitUntil`, `ForkJoin`,
  `RepeatBlock`, `IfTb`, `TimeoutGuard`, `Dump`, `CallTask`; new module-level
  `ResetSeq`, `Task`, `AssertProperty`. New validator `validate_tb` (rules
  T1–T8). `TbModule` gains additive `tasks`/`asserts`/`reset_seq` fields
  (defaulted), keeping the P2 smoke pipeline and its golden files byte-identical.
- **v1 (P2-13):** stub smoke-TB node set + `generate_tb`/`render_tb`.

## 1. Separation rule (normative, plan cross-cutting decision 2)

TB constructs live in `semicraft_core/tb/`, entirely outside the synthesizable
IR. The two directions of the invariant:

- **TB may not contain synthesizable IR.** No `semicraft_core.ir.nodes` type may
  appear anywhere inside a `TbModule` (statements, task bodies, fork branches,
  etc.). Enforced at runtime by validator rule **T3**.
- **RTL may not contain TB nodes.** This mirror direction needs no runtime check:
  `semicraft_core.ir.validate.validate` operates on `ir.nodes` types only and
  never imports the TB node family, so a TB node can never appear in an IR
  `Module` it validates. The type sets are disjoint and simply never meet. This
  asymmetry is intentional — do not add a redundant TB-in-IR check.

The TB references the synthesizable world only *by name*: `generate_tb` resolves
every DUT port/net through the **same** style name map (`render.style
.build_name_map`) the RTL renderer used, so TB connections match the rendered RTL
byte-for-byte (an active-low reset rendered `rst_n` is driven as `rst_n`).

## 2. Design rules

Mirrors [IR_SPEC.md §2](IR_SPEC.md): all nodes are **frozen + slotted**
dataclasses; list-valued fields accept any `Sequence` at construction and are
stored as `tuple` (immutability + hashability); full type annotations; no
defaults that hide required semantics. Rendering is deterministic — identical
`TbModule` in, identical text out (no timestamps, no randomness).

## 3. Node catalog

### 3.1 Statements (`Stmt`) — bodies of `Initial`, `Task`, and TB containers

**P2 smoke set (source-compatible, rendered today):**

| Node | Fields | Renders (P2) |
|---|---|---|
| `TbComment` | `text: str` | `// text` |
| `DriveSignal` | `signal, value: int, width: int` | `signal = width'dvalue;` |
| `Delay` | `ns: int` | `#ns;` |
| `WaitCycles` | `n: int, edge="posedge"` | `repeat (n) @(edge clk);` (`n==1` drops `repeat`) |
| `ExpectSignal` | `signal, expected: int, width: int, cycle_label: str` | `if (signal !== width'dexpected) $fatal(...)` |
| `Display` | `message: str` | `$display("message");` |
| `Finish` | — | `$finish;` |

`WaitCycles` carries no signal — it implicitly waits on the testbench clock
(`render_tb` emits the fixed net `clk`).

**P3-01 additions (rendered since P3-02):**

| Node | Fields | Renders |
|---|---|---|
| `WaitUntil` | `condition_text: str` | `wait (condition_text);` (level-sensitive) |
| `ForkJoin` | `branches: tuple[tuple[Stmt,...],...], join: "all"\|"any"\|"none"` | `fork` ... `join[_any\|_none]`; each branch wrapped in `begin ... end` (its own thread regardless of statement count) |
| `RepeatBlock` | `count: int, stmts: tuple[Stmt,...]` | `repeat (count) begin ... end` |
| `IfTb` | `condition_text: str, then, else_: tuple[Stmt,...] \| None` | `if (condition_text) begin ... end [else begin ... end]` |
| `TimeoutGuard` | `cycles: int, message: str` | forked watchdog: `fork begin static int watchdog_i; for (watchdog_i = 0; watchdog_i < cycles; watchdog_i++) @(posedge clk); $fatal(1, "message"); end join_none`. The posedge count uses an explicit **static** loop var, not `repeat` — Verilator flags `repeat`'s implicit automatic counter as possibly outliving the `join_none` process (`%Error-LIFETIME` under `--timing`). |
| `Dump` | `file: str, levels: int = 0` | `$dumpfile("file"); $dumpvars(levels, <tb_name>);` (dump scope = the TB module) |
| `CallTask` | `name: str` | `name();` |

`join` allowed values are `JOIN_KINDS = {"all","any","none"}` mapping to
`join` / `join_any` / `join_none`.

### 3.2 Module-level structural nodes

**P2 smoke set:** `Decl(name, width)`, `ClockGen(signal, half_period_ns=5)`,
`DutInstance(module, instance, connections)`, `Initial(stmts)`.

**P3-01 additions:**

| Node | Fields | Renders (P3-02) |
|---|---|---|
| `ResetSeq` | `signal: str, active_low: bool, cycles: int` | Its own `initial begin ... end` process after the DUT instance: assert level at time 0, `repeat (cycles) @(posedge <clock>);` (`cycles==1` drops `repeat`), `#1;`, deassert. The `#1` settle is normative — see §6a. |
| `Task` | `name: str, stmts: tuple[Stmt,...]` | `task name; ... endtask` between the DUT instance and the stimulus `initial`, in declaration order; invoked via `CallTask`. |
| `AssertProperty` | `name: str, property_text: str, clock: str, disable_iff: str \| None` | `name: assert property (@(posedge clock) [disable iff (expr) ]property_text)` + `else $fatal(1, "SVA FAIL: name");`, after the stimulus `initial`. **SVA stub** — see §5. |

`ResetSeq` adoption decision (P3-02): `generate_tb` keeps its reset **inline**.
Today's reset lives *inside* the main `initial`, after the input-initialisation
drives and under their shared comment line; a module-level `ResetSeq` renders as
a separate `initial` process, so adoption cannot be byte-identical to the P2
goldens. The renderer exists for hand-built/P3-04 TBs; `generate_tb` switching
over would be a golden-visible change requiring an explicit spec decision.

### 3.3 Root node

`TbModule(name, decls, clock, dut, initial, banner=(), tasks=(), asserts=(),
reset_seq=None)`. The P3-01 fields (`tasks`, `asserts`, `reset_seq`) are additive
with defaults, so P2 constructions build unchanged and render byte-identically.

## 4. Validator (`validate_tb`, rules T1–T8)

`validate_tb(tb: TbModule, extra_reserved=frozenset()) -> None` collects **all**
violations and raises a single `TbValidationError` whose message enumerates them,
sorted for determinism (same contract as `ir.validate`). `extra_reserved`
supplements the built-in SV+Verilog keyword sets for the T1 reserved-word check.

`validate_tb` is an **authoring-time** check for hand-built or generator-built
`TbModule`s; it is *not* wired into `generate_tb` (whose styled net names may use
a non-`snake_case` naming convention chosen by the user, outside T1's scope).

| Rule | Check |
|---|---|
| **T1** | `Decl` and `Task` names are canonical `lower_snake_case`, unique within their kind, and not reserved words (+`extra_reserved`); the DUT instance name is a valid identifier and collides with no declared net or task. |
| **T2** | Every `DriveSignal`/`ExpectSignal` `signal` (in the main `Initial` or any `Task`) resolves to a declared `Decl` or the clock signal. `WaitCycles` targets the clock implicitly — nothing to resolve. |
| **T3** | Separation: no `semicraft_core.ir` node appears anywhere in the TB tree (walked via `Initial`, `Task` bodies, and the `ForkJoin`/`RepeatBlock`/`IfTb` containers). Detected by defining module (`type(x).__module__`). |
| **T4** | `ForkJoin` has ≥1 branch and no empty branch; `join ∈ JOIN_KINDS`. `TimeoutGuard.cycles > 0`. |
| **T5** | Every `CallTask.name` resolves to a declared `Task`; the task call graph has no cycles (recursion is rejected — SV tasks here model non-recursive sequences). |
| **T6** | The main `Initial` can terminate: it contains ≥1 `$finish`, its last top-level statement is (or contains) a `Finish`, and at most one `Finish` sits directly at top level. *Approximation* — see §5. |
| **T7** | `Dump.file` is a safe **relative** filename: non-empty, no path separator (`/` or `\`), no `..`, no `:`. |
| **T8** | `AssertProperty` names are unique; `property_text` is non-empty; `clock` resolves to a declared `Decl` or the clock signal. |

## 5. Documented approximations

- **Opaque text fields.** `WaitUntil.condition_text`, `IfTb.condition_text`, and
  `AssertProperty.property_text`/`disable_iff` are raw SystemVerilog expression
  **strings**. A first-class TB expression AST is a later phase, so `validate_tb`
  checks only their structural shell (non-empty, name/clock resolution) — it
  **cannot** resolve identifiers used *inside* the text.
- **`AssertProperty` is an SVA stub.** The property is carried as text, not a
  property AST. Full concurrent-assertion generation (reset/handshake/stability/
  onehot templates) is plan P3-05 and beyond.
- **T6 is structural, not path-exact.** It proves the sim *can* terminate (a
  reachable trailing `$finish`), not that every control path finishes. An `IfTb`
  whose `then`/`else` each `$finish` passes even though only one arm runs.
- **T5 rejects all task recursion**, including indirect cycles. SV does allow
  recursive tasks (`automatic`), but the TB generators model bounded directed
  sequences, so recursion is treated as an authoring error.

## 6. Rendering rules (`render_tb`)

- **SystemVerilog only**, even for Verilog DUTs (a `.sv` TB instantiating a `.v`
  module elaborates fine under Verilator; single simplest path).
- `timescale 1ns/1ps`; free-running clock `always #5 clk = ~clk`.
- Reset asserted from time 0, held `TbSpec.reset_cycles` rising edges, then
  deasserted **after a `#1` settle** (never in the same timestep as that rising
  edge — see §6a); polarity from the DUT's `ResetSpec` (active-low → assert=0/
  deassert=1 on the styled `_n` net).
- Directed cycle `c`: inputs driven on the `negedge` (no drive/sample race with
  the DUT's rising edge); checks sample after a `#1` settle. Runs of idle cycles
  are coalesced into a single `repeat (N) @(negedge clk);`.
- Checks: `if (sig !== expected) $fatal(1, "SMOKE FAIL: ...")`; success path
  prints `SMOKE PASS: <module>` then `$finish`.
- Deterministic: no timestamps; banner mirrors the RTL header (tool version,
  config hash, disclaimer).

### 6a. Reset-deassertion timing (normative decision, P3-09a)

`generate_tb` emits the reset deassertion as `#1;` **then** the deassert drive,
after the `repeat (reset_cycles) @(posedge clk);` hold:

```systemverilog
rst_n = 1'd0;
repeat (2) @(posedge clk);
#1;                          // settle: put the deassert after the edge
rst_n = 1'd1;
```

**Why (the bug this fixes).** Deasserting in the same timestep as the rising edge
the TB just woke on is a drive/sample race against the DUT's own clocked process.
For a *synchronous* reset, `always_ff @(posedge clk) if (!rst_n) ... else ...` may
observe the already-deasserted level and take a real state update on the very edge
the TB still counts as "in reset". The DUT then runs one state ahead of the
`TbSpec` model at directed cycle 0.

This was latent from P2-13 through P3-04 because it is *masked* whenever the DUT's
state update is gated by an enable that is still 0 at that moment (all
initialised-to-0 inputs are). It surfaces only in **free-running** configurations
— which is exactly the set the run gate caught: gray-counter (`enable=False`),
lfsr (`enable=False`/serial), clock-divider (`pulse` style). 17 of 165 golden TBs,
invisible to CI because `test_tb_run.py` defaults to the `defaults` case per
module (`SEMICRAFT_TB_RUN_ALL=1` runs the full matrix).

**Scope of the fix.** Generator-side only: no module's `TbSpec` expected values
changed — the modules' timing models were correct and the TB was wrong. The
change is one added `#1;` line in each of the 165 TB goldens; RTL, doc, and
testplan goldens are byte-identical. Reset is still observed asserted for exactly
`reset_cycles` rising edges, and directed cycle 0 still sees zero post-reset
edges, so §7's name/width anchor and the per-module timing models are unaffected.

Note this rule is the same discipline §6 already applied to *vector* drives
("inputs driven on the `negedge`, no drive/sample race with the DUT's rising
edge") — the reset deassert had simply been exempt from it.

Since P3-02, `_emit_stmt` renders **every** member of the `Stmt` union (it no
longer raises on P3 nodes), per the render columns in §3. Module layout: decls,
clock, DUT instance, then the optional P3 sections — `ResetSeq` process, `Task`
declarations, the stimulus `initial`, `AssertProperty` block (under a
`// Concurrent assertions (SVA)` comment) — each omitted entirely when absent,
so P2 smoke constructions render byte-identically to v1.

### 6b. Sim-script emitters (`tb/scripts.py`, P3-02)

`emit_run_script(tb_filename, rtl_filenames) -> str` and
`emit_makefile(tb_filename, rtl_filenames) -> str` (exported from
`semicraft_core.tb`) emit a POSIX `run.sh` / `Makefile` pair driving the exact
two-stage flow of `semicraft_core.sim.runner.run_smoke`: `verilator --timing
--binary --build-jobs 1 -Mdir obj_dir <tb> <rtl...>` then execute
`obj_dir/V<top>` (`<top>` = the TB filename's stem, which `render_tb` guarantees
is the TB module name). Deterministic, no timestamps; filenames must be bare
relative names free of shell metacharacters (`ValueError` otherwise). Icarus
fallback (plan P3-02 row) is deferred — the sim runner is Verilator-only today,
and the scripts mirror the runner.

## 7. Name/width consistency (the correctness anchor)

`generate_tb` receives the *stamped IR module* the RTL was rendered from and
resolves every net through the same style name map the RTL renderer used. Port
widths are evaluated from the module's default parameter values (`Const`/`Ref`/
`+ - *` expressions only — anything else raises rather than guessing).

### 7a. The clock net name is data, not a constant (normative decision, P4-01)

Every edge-waiting construct the renderer emits — `WaitCycles`, the
`TimeoutGuard` watchdog loop, `ResetSeq` — must name the clock net from
`TbModule.clock.signal`, never a literal `clk`.

`render_tb` originally held it in a module-level `_CLOCK_NAME = "clk"`. That is
correct for every *default* configuration, because the default naming style
renders the clock port as `clk`. Under any style with a prefix, a suffix, or
camelCase conversion the DUT clock renders (say) `p_clk` while the stimulus and
watchdog still said `clk`, and Verilator rejected the testbench outright:
`Can't find definition of variable: 'clk'`. Every module was affected, in both
languages — the emitted testbench simply did not compile.

Why it survived two releases: no golden case sets a naming style, so the whole
matrix (165 cases) exercises only the one spelling for which the constant
happened to be right. It was found by the P4-01 reference IP's Verilator run
gate, which does parametrize over naming.

This is the same failure shape as the assertion restyle of P3-05a: metadata
written in canonical names, rendered without going through the name map. §7 is
the general rule; this section records that the *clock* is subject to it too.

Regression cover: `backend/tests/tb/test_directed_tb.py` asserts, for every
module under a prefix+camelCase style, that the set of nets the TB waits on is
exactly the styled clock and that every such net is declared.

## 8. Limitations

- Smoke TBs are compile-checked in CI (`verilator --binary`, P2-14 gate) but not
  yet *run*; execution gating lands with the sim sandbox (P3-03/P3-09).
- Single clock/reset only; default parameterization only (widths from parameter
  defaults). Modules whose `TbSpec.clock` is `None` produce no TB file.
