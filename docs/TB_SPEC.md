# SemiCraft Testbench IR Specification

**Version 2 (Phase 3, P3-01).** Owner: verification core (`semicraft_core/tb/`).

The testbench (TB) IR is a small, frozen-dataclass node family for directed
**SystemVerilog** testbenches, entirely separate from the synthesizable IR
(`semicraft_core/ir/`, see [IR_SPEC.md](IR_SPEC.md)). It began (P2-13) as a tiny
"smoke" set — clock, reset, per-cycle drives, self-checking expects — that
`generate_tb` still uses to emit compile-checked smoke testbenches. P3-01 extends
it into the full Phase 3 family (fork/join, loops, conditionals, timeout
watchdog, waveform dump, reusable tasks, an SVA-property stub) and adds a
validator (`validate_tb`). Renderers for the new nodes land with P3-02; only the
P2 smoke subset is rendered today.

The stable public seams are unchanged:
`semicraft_core.tb.generate_tb(module_def, opts, rtl_module) -> str`,
`semicraft_core.tb.render_tb(TbModule) -> str`, and the
`GeneratedFile(kind="tb", path="<module>_tb.sv")` output of `generate_files`.

## Changelog

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

**P3-01 additions (renderers land P3-02):**

| Node | Fields | Intended render |
|---|---|---|
| `WaitUntil` | `condition_text: str` | `wait (condition_text);` (level-sensitive) |
| `ForkJoin` | `branches: tuple[tuple[Stmt,...],...], join: "all"\|"any"\|"none"` | `fork ... join[_any\|_none]` |
| `RepeatBlock` | `count: int, stmts: tuple[Stmt,...]` | `repeat (count) begin ... end` |
| `IfTb` | `condition_text: str, then, else_: tuple[Stmt,...] \| None` | `if (condition_text) begin ... end [else ...]` |
| `TimeoutGuard` | `cycles: int, message: str` | forked watchdog: `repeat (cycles) @(posedge clk); $fatal(1, message);` |
| `Dump` | `file: str, levels: int = 0` | `$dumpfile("file"); $dumpvars(levels, ...);` |
| `CallTask` | `name: str` | `name();` |

`join` allowed values are `JOIN_KINDS = {"all","any","none"}` mapping to
`join` / `join_any` / `join_none`.

### 3.2 Module-level structural nodes

**P2 smoke set:** `Decl(name, width)`, `ClockGen(signal, half_period_ns=5)`,
`DutInstance(module, instance, connections)`, `Initial(stmts)`.

**P3-01 additions:**

| Node | Fields | Notes |
|---|---|---|
| `ResetSeq` | `signal: str, active_low: bool, cycles: int` | Declarative assert/hold/deassert. Formalizes what `generate_tb` inlines today as raw drives/waits. `generate_tb` may adopt it (P3-02/04) **only if the rendered text stays byte-identical**. |
| `Task` | `name: str, stmts: tuple[Stmt,...]` | Named reusable sequence (`task name; ... endtask`), invoked via `CallTask`. |
| `AssertProperty` | `name: str, property_text: str, clock: str, disable_iff: str \| None` | **SVA stub** — see §5. |

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

## 6. Rendering rules (`render_tb`, P2 smoke subset)

- **SystemVerilog only**, even for Verilog DUTs (a `.sv` TB instantiating a `.v`
  module elaborates fine under Verilator; single simplest path).
- `timescale 1ns/1ps`; free-running clock `always #5 clk = ~clk`.
- Reset asserted from time 0, held `TbSpec.reset_cycles` rising edges, then
  deasserted; polarity from the DUT's `ResetSpec` (active-low → assert=0/
  deassert=1 on the styled `_n` net).
- Directed cycle `c`: inputs driven on the `negedge` (no drive/sample race with
  the DUT's rising edge); checks sample after a `#1` settle. Runs of idle cycles
  are coalesced into a single `repeat (N) @(negedge clk);`.
- Checks: `if (sig !== expected) $fatal(1, "SMOKE FAIL: ...")`; success path
  prints `SMOKE PASS: <module>` then `$finish`.
- Deterministic: no timestamps; banner mirrors the RTL header (tool version,
  config hash, disclaimer).

New P3-01 nodes are **not** rendered by `render_tb` yet — `_emit_stmt` raises on
any statement outside the P2 smoke set. Their renderers land with P3-02.

## 7. Name/width consistency (the correctness anchor)

`generate_tb` receives the *stamped IR module* the RTL was rendered from and
resolves every net through the same style name map the RTL renderer used. Port
widths are evaluated from the module's default parameter values (`Const`/`Ref`/
`+ - *` expressions only — anything else raises rather than guessing).

## 8. Limitations

- Smoke TBs are compile-checked in CI (`verilator --binary`, P2-14 gate) but not
  yet *run*; execution gating lands with the sim sandbox (P3-03/P3-09).
- Single clock/reset only; default parameterization only (widths from parameter
  defaults). Modules whose `TbSpec.clock` is `None` produce no TB file.
