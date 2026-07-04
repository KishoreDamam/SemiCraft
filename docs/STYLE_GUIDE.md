# SemiCraft RTL Style Guide

This is the default coding style SemiCraft generates. It applies to every
snippet unless the user overrides a style option (naming convention, comment
verbosity, language). See [`IR_SPEC.md`](IR_SPEC.md) for the underlying IR and
[`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) §1 for the ground rules
this guide implements.

## 1. Naming

- **Case:** `lower_snake_case` for all signals, ports, parameters (parameter
  *names* are `UPPER_SNAKE_CASE`, see §5), module names, and instance names.
  This is the canonical IR naming (IR_SPEC §2 rule 5) and the default style
  engine convention (`naming: snake`).
- **Active-low suffix:** any active-low signal — reset, enable, chip-select,
  etc. — gets an `_n` suffix, appended by the style engine at render time.
  The IR itself never carries the suffix; it is derived from
  `ResetSpec.active_low` (or an equivalent polarity flag) purely during
  rendering (IR_SPEC §2 rule 5). Example: canonical IR name `rst` renders as
  `rst_n` when `reset_polarity = active_low`.
- **Canonical signal names:**
  - Clock: `clk` (see `ClockSpec.name`, default `"clk"`).
  - Reset: `rst` (active-high) / `rst_n` (active-low), from `ResetSpec.name`.
  - Enable: `en`.
  These are the defaults every snippet uses unless a snippet-specific option
  renames them (e.g. `cdc-synchronizer` uses `sync_ff1..N` for its internal
  chain, per IMPLEMENTATION_PLAN.md §5 WP-05h).
- **Module naming:** the module name is the snippet's generated identifier
  (e.g. `counter`), `lower_snake_case`, matching the output filename
  (`<module_name>.sv` / `<module_name>.v`, or `<module_name>_fragment.<ext>`
  in fragment mode).
- **Reserved words:** the renderer rejects any name that collides with a SV
  or Verilog reserved word *after* style transformation (naming prefix/suffix
  applied) — checked against both languages' keyword sets regardless of
  target, since either may be rendered from the same IR (IR_SPEC §6 rule 7).
- **Enum members (FSM states):** rendered exactly as declared in the IR,
  `lower_snake_case` (e.g. `idle`, `run`, `done`, or `s0`..`s4` for an
  auto-generated state list) — see golden `fsm/defaults.sv`. Any
  `S_IDLE`-style `UPPER_SNAKE_CASE` state name seen elsewhere (e.g.
  [`IR_SPEC.md`](IR_SPEC.md) §7's rendering table) is illustrative shorthand
  for the `EnumDecl`/`localparam` row, not a naming-convention override.

## 2. The Four Reset Idioms

`AlwaysFF` reset behavior is declarative in the IR (`ResetSpec.kind`,
`ResetSpec.active_low`) — generators never hand-write the `if (reset) ...
else ...` skeleton. The renderer composes exactly one of four variants
per IR_SPEC §4:

| `reset_style` | `reset_polarity` | Sensitivity list | Reset condition |
|---|---|---|---|
| sync | active-high | `posedge clk` | `if (rst)` |
| sync | active-low | `posedge clk` | `if (!rst_n)` |
| async | active-high | `posedge clk or posedge rst` | `if (rst)` |
| async | active-low | `posedge clk or negedge rst_n` | `if (!rst_n)` |

Same body IR, four textual variants — this table is the single point where
`reset_style` and `reset_polarity` options take effect.

### 2.1 Sync, active-high (SystemVerilog)

```systemverilog
always_ff @(posedge clk) begin
    if (rst) begin
        count <= {WIDTH{1'b0}};
    end else begin
        if (en) begin
            count <= count + 1'b1;
        end
    end
end
```

### 2.2 Sync, active-high (Verilog)

```verilog
always @(posedge clk) begin
    if (rst) begin
        count <= {WIDTH{1'b0}};
    end else begin
        if (en) begin
            count <= count + 1'b1;
        end
    end
end
```

### 2.3 Sync, active-low (SystemVerilog)

```systemverilog
always_ff @(posedge clk) begin
    if (!rst_n) begin
        count <= {WIDTH{1'b0}};
    end else begin
        if (en) begin
            count <= count + 1'b1;
        end
    end
end
```

### 2.4 Sync, active-low (Verilog)

```verilog
always @(posedge clk) begin
    if (!rst_n) begin
        count <= {WIDTH{1'b0}};
    end else begin
        if (en) begin
            count <= count + 1'b1;
        end
    end
end
```

### 2.5 Async, active-high (SystemVerilog)

```systemverilog
always_ff @(posedge clk or posedge rst) begin
    if (rst) begin
        count <= {WIDTH{1'b0}};
    end else begin
        if (en) begin
            count <= count + 1'b1;
        end
    end
end
```

### 2.6 Async, active-high (Verilog)

```verilog
always @(posedge clk or posedge rst) begin
    if (rst) begin
        count <= {WIDTH{1'b0}};
    end else begin
        if (en) begin
            count <= count + 1'b1;
        end
    end
end
```

### 2.7 Async, active-low (SystemVerilog) — canonical IR_SPEC §9 example

```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= {WIDTH{1'b0}};
    end else begin
        if (en) begin
            count <= count + 1'b1;
        end
    end
end
```

### 2.8 Async, active-low (Verilog)

```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= {WIDTH{1'b0}};
    end else begin
        if (en) begin
            count <= count + 1'b1;
        end
    end
end
```

If `reset=None` (no-reset register), the sensitivity list is `posedge clk`
only and the body is emitted with no `if`/`else` skeleton at all — just the
clocked body statements directly inside the `always_ff` / `always` block.

## 3. Always-Block Rules

- **SystemVerilog** uses `always_ff @(...)` for clocked (sequential) logic and
  `always_comb` for purely combinational logic. **Verilog** uses
  `always @(posedge clk [or ...])` and `always @(*)` respectively
  (IR_SPEC §7 rendering table).
- **Assignment operator is inferred from context, never chosen by the
  generator** (IR_SPEC §2 rule 3, design rule for the single `Assign` node):
  - Inside `AlwaysFF`: non-blocking `<=`.
  - Inside `AlwaysComb`: blocking `=`.
  - `ContAssign`: `assign lhs = rhs;`.
  A generator cannot produce a mixed-style process because there is only one
  `Assign` node and the renderer picks the operator by enclosing context.
- **Default-assignment-first pattern for comb blocks.** Every `AlwaysComb`
  that contains a `Case` assigns a default value to the target(s) *before*
  the case statement (or the `Case.default` arm is mandatory — see IR_SPEC §6
  rule 5), so there is no latch inference and no missing-arm hazard. Example
  (verbatim from golden `demux/defaults.sv`; case labels are the selector
  width composed as a replication/concat per §6's unsized-const rule, not a
  sized-literal shorthand like `2'd0`):

  ```systemverilog
  always_comb begin
      out0 = {WIDTH{1'b0}};
      out1 = {WIDTH{1'b0}};
      out2 = {WIDTH{1'b0}};
      out3 = {WIDTH{1'b0}};
      case (sel)
          {SEL_WIDTH{1'b0}}: out0 = din;
          {{(SEL_WIDTH-1){1'b0}}, 1'b1}: out1 = din;
          {{(SEL_WIDTH-2){1'b0}}, 2'b10}: out2 = din;
          {{(SEL_WIDTH-2){1'b0}}, 2'b11}: out3 = din;
          default: ;
      endcase
  end
  ```
- **`unique case`:** when `Case.unique = True`, SV emits `unique case`
  (verified in every `fsm/*.sv` golden). Verilog has no equivalent and emits
  plain `case`; a `// unique case intent: labels are mutually exclusive`
  comment is added *only* when `comment_verbosity = verbose` — at `normal`
  (the default) and `none`, the Verilog `case` carries no such comment (see
  `fsm/defaults.v`, which has no intent comment at the default verbosity).
- **No latches, ever.** Combinational output ports and internal signals are
  always fully assigned in every path; this is enforced by the
  default-assignment-first pattern above and checked by the Verilator
  `--lint-only -Wall` gate (WP-04).

## 4. ANSI Port Style and Alignment

Ports use ANSI-style declarations inside the module header (both SV and
Verilog-2001; IR_SPEC §7). Direction, type, and name are column-aligned so
the port list reads as a table; inline `//` comments (from `Port.doc`) are
also aligned. This is the `counter` snippet's module header, verbatim from
golden `counter/reset_async_active_low.sv` (async reset, active-low):

```systemverilog
module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Async reset, active-low
    input  logic             en,      // Count enable (holds when low)
    output logic [WIDTH-1:0] count    // Current count value
);
```

Every port that has a `Port.doc` gets an aligned trailing comment — including
`clk`, which is easy to assume is undocumented but is not, in this snippet.

Notes:

- `input`/`output` are padded to the same width (`input `/`output`, note the
  extra space after `input` to align with `output`).
- The type column (`logic`, `logic [WIDTH-1:0]`, or in Verilog `wire`/`reg`
  `[WIDTH-1:0]`) is padded so every port name starts in the same column.
  Widths use `[MSB:0]` form, e.g. `[WIDTH-1:0]`.
  Verilog uses reg/wire keywords per the reg/wire inference rule (IR_SPEC §2
  rule 6: procedurally-driven output ports render as `output reg`;
  continuous-assign-driven ports render as `output wire`).
- Trailing comma on every port except the last.
- Per-port doc comments (from `Port.doc`) are aligned in a trailing comment
  column when present; ports without a `doc` have no trailing comment.
- No `inout` ports exist in v0.1 (IR_SPEC §8 non-goals).

## 5. Parameter Style

- SystemVerilog: `parameter int unsigned NAME = <default>;` inside the
  `#( ... )` port-list-adjacent parameter block (IR_SPEC §7 table). Verilog:
  `parameter NAME = <default>;` (no type keyword — Verilog-2001 parameters
  are untyped).
- Parameter *names* are `UPPER_SNAKE_CASE` (e.g. `WIDTH`, `DEPTH`,
  `NUM_INPUTS`) — the one deliberate exception to the otherwise
  `lower_snake_case` naming convention, matching common RTL convention and
  distinguishing compile-time parameters from signals at a glance.
- `local=True` on a `Param` renders as `localparam` instead of `parameter`
  (used for derived/internal constants such as a computed select width).
- v0.1 parameters are unsigned integers only (IR_SPEC §3.3 `Param` notes).
- Width expressions built from parameters render as arithmetic on the
  parameter name, not a resolved literal: `BinOp('-', Ref('WIDTH'),
  Const(1))` renders `WIDTH-1`, e.g. `logic [WIDTH-1:0] count`.

## 6. Formatting

- **Indentation:** 4 spaces per nesting level, no tabs.
- **One statement per line.** No comma- or semicolon-joined statements on a
  single line.
- **Full parenthesization of nested expressions.** Renderers do not rely on
  operator precedence to keep output unambiguous; nested operator
  expressions are fully parenthesized except at statement top level
  (IR_SPEC §3.1). For example `a + b * c` — if `b * c` is itself a compound
  expression passed as an operand — renders as `a + (b * c)`, not relying on
  `*` binding tighter than `+`. Simple single-operator statement-level
  expressions (e.g. `count <= count + 1'b1;`) are not artificially
  parenthesized further, since there is no nested sub-expression to
  disambiguate.
- **`begin`/`end` on all blocks**, including single-statement `if`/`else`
  bodies (see the reset idiom examples in §2) — no bare single-statement
  `if` without `begin`/`end`.
- Blank line separates the module header (ports/parameters) from the first
  body item, and separates top-level items (each `always_ff`/`always_comb`/
  `assign` block) from one another.
- **Unsized-constant rendering depends on expression context** (two contexts,
  `render/base.py` module docstring):
  - **Data context** (the default — right-hand sides of assignments, case
    labels, operands in expressions): an unsized `Const` renders as a
    **minimal-width binary literal**, e.g. `Const(1)` → `1'b1`,
    `Const(0)` → `1'b0` (see every reset idiom in §2:
    `count <= count + 1'b1;`). A `Const` whose *width* is itself a
    non-literal expression (e.g. a parameter) composes a **replication**
    instead: `Const(0, width=Ref("WIDTH"))` → `{WIDTH{1'b0}}` (the reset
    value in every clocked snippet's reset branch), and a non-zero value
    with a parameterized width composes a concatenation of a replicated
    pad plus a sized literal for the low bits, e.g.
    `{{(WIDTH-3){1'b0}}, 3'b101}` (golden `register/reset_value_5.sv`) or
    `{{(SEL_WIDTH-1){1'b0}}, 1'b1}` (golden `demux/defaults.sv` case
    labels).
  - **Size context** (declaration ranges, indexes, slice bounds, replication
    counts, parameter default values): an unsized `Const` renders as a
    **plain number**, no width/base prefix — e.g. `parameter int unsigned
    WIDTH = 8;` (not `8'd8`), and width expressions stay compact arithmetic
    on the parameter name (`WIDTH-1`, §5). A `Const` that already carries an
    explicit width/base (e.g. `2'b10` in a case label) renders sized in
    either context — only *unsized* constants switch representation by
    context.

## 7. Comment Conventions

Comments are data, not text embedded in code (IR_SPEC §2 rule 7): generators
emit `Comment` nodes with an explicit verbosity `level`, and the renderer
filters them according to the `comment_verbosity` style option:

| `comment_verbosity` | Emitted comments |
|---|---|
| `none` | No `Comment` nodes rendered. Port `doc` inline comments are also suppressed. |
| `normal` | `Comment(level="normal")` nodes rendered, plus port `doc` inline comments. This is the default. |
| `verbose` | All comments rendered, including `level="verbose"` nodes (extra rationale, e.g. per-case-arm notes, `unique case` intent notes on Verilog, CDC multi-bit assumption warnings). |

Port documentation (`Port.doc`) always feeds the trailing `//` comment shown
in §4 at `normal` and `verbose` levels, and is suppressed at `none`.

**Parameter `doc` is not rendered.** `Param` carries a `doc` field in the IR
(for tooling/documentation use, e.g. a future param-doc surface), but the
renderer's `_param_decl` (`render/base.py`) never emits it as a comment, at
any `comment_verbosity` level — parameter declarations in `#( ... )` never
have a trailing `//` comment in current golden output (see every
`counter/*.sv`, `demux/*.sv`, `mux/*.sv` golden: `parameter int unsigned
WIDTH = 8` has no comment, unlike ports on the following lines). Do not
assume parameter docs appear in generated code.

## 8. File Header Format

Every generated file begins with a header comment rendered from the IR
`Header` node (`license`, `config_hash`, `tool_version`, `description` —
IR_SPEC §3.3), via `BaseRenderer._emit_banner` (`render/base.py`). The header
carries no timestamp (determinism is a release criterion: same config →
byte-identical output). The banner is always exactly five `//` lines —
version, snippet+hash, description, a bare `//` separator, then the
(possibly word-wrapped) disclaimer — followed by one blank line before the
`module` declaration (or the fragment-mode comment block). Verbatim from
golden `counter/defaults.sv`:

```systemverilog
// SemiCraft v0.1.0
// Snippet: counter (config hash: 559db01d8e5a)
// Up counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.
```

The config hash and description change per snippet/options (every golden
file has its own hash), but the five-line shape and the disclaimer wording
are identical across every generated file, in both languages.

- **Tool name + version:** `SemiCraft v<VERSION>`, from
  `semicraft_core.version.VERSION`.
- **Config hash:** `sha256(snippet_id + canonical sorted-keys options JSON)`
  truncated to 12 hex characters (IMPLEMENTATION_PLAN.md §4), shown so a
  regenerated file can be checked against the exact configuration that
  produced it.
- **Description:** the snippet's one-line `Header.description`.
- **Disclaimer (exact text, single-sourced in
  `backend/semicraft_core/license.py` as `DISCLAIMER`):**

  > Generated code is provided as-is, without warranty of any kind. Free for
  > commercial and non-commercial use at the user's own risk.

This is the literal text required by IMPLEMENTATION_PLAN.md §1 and
SemiCraft_PRD.md §15 ("Licensing" decision) and must not be paraphrased by
renderer code — always imported from the `DISCLAIMER` constant.

## 9. Worked Example

The full worked example below is the canonical reference (IR_SPEC §9):
8-bit up counter, async active-low reset, enable, default width 8 — verbatim
from golden `counter/reset_async_active_low.sv`, including the generated-file
header (§8):

```systemverilog
// SemiCraft v0.1.0
// Snippet: counter (config hash: c75d0b6e7aea)
// Up counter, 8-bit
//
// Generated code is provided as-is, without warranty of any kind. Free for
// commercial and non-commercial use at the user's own risk.

module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,     // Clock
    input  logic             rst_n,   // Async reset, active-low
    input  logic             en,      // Count enable (holds when low)
    output logic [WIDTH-1:0] count    // Current count value
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else begin
            if (en) begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
```

The Verilog rendering of the same IR (golden `counter/reset_async_active_low.v`)
differs only per the IR_SPEC §7 table: `clk`/`rst_n`/`en` become `input wire`,
`count` becomes `output reg  [WIDTH-1:0] count` (procedurally driven → `reg`,
IR_SPEC §2 rule 6), the always block becomes
`always @(posedge clk or negedge rst_n)`, and the parameter becomes
`parameter WIDTH = 8` (no `int unsigned`) — the config hash also differs
(`1108fcd9886d`) since it is computed per rendered-language target.
