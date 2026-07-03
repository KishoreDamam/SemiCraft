# SemiCraft Module IR Specification

Version 0.1 (MVP scope). Owner: generator core (`semicraft_core/ir/`).

## 1. Purpose and Scope

The IR (intermediate representation) is a small, language-neutral AST for the
**synthesizable RTL subset** needed by SemiCraft generators. Snippet generators
build IR trees; renderers walk the tree to emit SystemVerilog or Verilog text.

The IR is deliberately *not* a general Verilog AST. It cannot represent
testbench constructs, delays, events, hierarchical references, generate loops,
or interfaces. Anything the IR cannot express, a generator cannot emit — this
is the mechanism that keeps output reviewable and lint-clean by construction.

Scope covers all 10 MVP snippets plus Phase 2 module generation headroom
(instances, parameterized widths). Explicit non-goals for v0.1 are listed in
§8.

## 2. Design Rules

These rules are invariants; renderers and generators may rely on them.

1. **Immutable nodes.** All nodes are frozen dataclasses (or frozen Pydantic
   models). Generation is a pure function `options -> Module`; the same options
   produce a structurally identical tree, and rendering is deterministic.
2. **Language decisions live in renderers, not IR.** The IR never contains
   `always_ff` vs `always @`, `logic` vs `reg`/`wire`, or blocking vs
   non-blocking assignment. Renderers own these.
3. **Assignment operator is inferred.** A single `Assign` node is used
   everywhere. Inside `AlwaysFF` the renderer emits non-blocking (`<=`);
   inside `AlwaysComb` it emits blocking (`=`); `ContAssign` emits
   `assign ... = ...`. Generators cannot produce mixed-style processes.
4. **Reset is declarative.** `AlwaysFF` carries a `ResetSpec` plus a dedicated
   `reset_body`. Renderers synthesize the sensitivity list and the
   `if (reset) ... else ...` skeleton. Generators never hand-write reset
   if-trees, so sync/async and polarity options cannot be applied
   inconsistently.
5. **Canonical naming in IR; style applied at render.** IR names are
   `lower_snake_case` ASCII identifiers, with one exception: `Param` names are
   `UPPER_SNAKE_CASE` (RTL convention, e.g. `WIDTH`, `DEPTH`); validation
   enforces both patterns. The style engine (`render/style.py`)
   applies user naming options (prefixes, suffixes, alternative conventions)
   and enforces the `_n` suffix for active-low signals during rendering. The
   renderer rejects names that collide with SV/Verilog reserved words *after*
   style transformation.
6. **Net/variable kind is inferred.** Generators declare `Signal`s without
   specifying reg/wire/logic. The Verilog renderer classifies: driven by a
   procedural block → `reg`; driven by `ContAssign` or instance output →
   `wire`. The SV renderer emits `logic` for both. A signal driven from both a
   procedural block and a continuous assign is an IR validation error.
7. **Comments are data.** Explanatory comments are `Comment` nodes emitted by
   generators. The renderer filters them by the comment-verbosity style option
   (`none` / `normal` / `verbose`, each Comment carries a level). Code text is
   never used to carry commentary.

## 3. Node Catalog

Three layers: **expressions**, **statements**, **module items**. `Expr` and
`Stmt` are abstract bases.

### 3.1 Expressions (`Expr`)

| Node | Fields | Notes |
|---|---|---|
| `Ref` | `name: str` | Reference to a signal, port, or param. Must resolve within the module (validated, §6). |
| `Const` | `value: int`, `width: Expr \| None`, `base: dec\|hex\|bin`, `signed: bool = False` | `width=None` → unsized literal. Sized renders as `8'hFF` etc. |
| `UnaryOp` | `op`, `a: Expr` | Ops: `~ - ! & \| ^ ~& ~\| ~^` (last six are reductions). |
| `BinOp` | `op`, `a: Expr`, `b: Expr` | Ops: `+ - * == != < <= > >= << >> >>> & \| ^ && \|\|`. No `/` or `%` in v0.1 (see §8). |
| `Ternary` | `cond, then, else_: Expr` | |
| `Bit` | `target: Expr`, `index: Expr` | `x[i]` |
| `Slice` | `target: Expr`, `msb: Expr`, `lsb: Expr` | `x[msb:lsb]`, constant or param-derived bounds only. |
| `Concat` | `parts: list[Expr]` | `{a, b, c}` |
| `Repl` | `count: Expr`, `value: Expr` | `{N{x}}` |
| `EnumRef` | `enum: str`, `value: str` | Reference to a declared enum member (FSM states). SV renders the enum name; Verilog renders the corresponding localparam. |

Renderers fully parenthesize nested operator expressions (except at statement
top level) rather than encoding precedence — verbosity over ambiguity.

**Width expressions.** Anywhere a width appears (`DataType.width`,
`Const.width`), the value is an `Expr` so parameterized widths work:
`BinOp('-', Ref('WIDTH'), Const(1))` renders as `WIDTH-1`. Helper
`width(n_or_name)` builds the common cases.

### 3.2 Statements (`Stmt`) — bodies of processes

| Node | Fields | Notes |
|---|---|---|
| `Assign` | `lhs: Expr`, `rhs: Expr` | Operator chosen by context (design rule 3). `lhs` restricted to `Ref`, `Bit`, `Slice`, `Concat` of those. |
| `If` | `cond: Expr`, `then: list[Stmt]`, `elifs: list[tuple[Expr, list[Stmt]]]`, `else_: list[Stmt] \| None` | |
| `Case` | `sel: Expr`, `items: list[CaseItem]`, `default: list[Stmt] \| None`, `unique: bool = False` | `CaseItem(labels: list[Expr], body: list[Stmt])`. `unique=True` → SV `unique case`; Verilog renders plain `case` (a `Comment` notes the intent). `default` required unless the case is an enum case covering all members (validated). |
| `Comment` | `text: str`, `level: normal\|verbose` | Filtered by style option (design rule 7). `none` is a render-time filter setting only, never a node level. |

No loops, no blocking sequencing subtleties, no task/function calls in v0.1.

### 3.3 Module items

| Node | Fields | Notes |
|---|---|---|
| `Module` | `name: str`, `params: list[Param]`, `ports: list[Port]`, `items: list[ModuleItem]`, `header: Header` | Root node. `items` may contain `Signal`, `EnumDecl`, `ContAssign`, `AlwaysFF`, `AlwaysComb`, `Instance`, `Comment`. |
| `Header` | `license: str`, `config_hash: str`, `tool_version: str`, `description: str` | Rendered as the file banner comment. **No timestamps** — determinism. |
| `Param` | `name: str`, `default: Expr`, `local: bool = False`, `doc: str = ""` | `local=True` → `localparam`. v0.1 params are unsigned integers. |
| `Port` | `name: str`, `dir: input\|output`, `dtype: DataType`, `doc: str = ""` | No `inout` in v0.1. `doc` feeds both port comments and the ExplanationDoc. |
| `DataType` | `width: Expr \| None`, `signed: bool = False` | `width=None` → 1-bit scalar. Packed 1-D vectors only; no arrays/structs in v0.1. |
| `Signal` | `name: str`, `dtype: DataType`, `doc: str = ""` | Internal declaration. Kind inferred (design rule 6). |
| `EnumDecl` | `name: str`, `members: list[str]`, `encoding: binary\|onehot\|gray` | FSM state types. SV: `typedef enum logic [...]` + typed state signal. Verilog: `localparam` per member with encoding applied + plain vector state signal. |
| `ContAssign` | `lhs: Expr`, `rhs: Expr` | `assign lhs = rhs;` |
| `AlwaysFF` | `clock: ClockSpec`, `reset: ResetSpec \| None`, `reset_body: list[Stmt]`, `body: list[Stmt]` | See §4. `reset=None` → no-reset register (then `reset_body` must be empty). |
| `AlwaysComb` | `body: list[Stmt]` | SV: `always_comb`. Verilog: `always @(*)`. Full-assignment (no latch) checked by Verilator lint gate. |
| `Instance` | `module: str`, `name: str`, `params: dict[str, Expr]`, `conns: dict[str, Expr]` | Named connections only, always `.port(expr)`. Used by the optional wrapper and Phase 2. Implementation note: stored internally as sorted tuples (nodes are frozen/hashable); renderers use the `.params_dict` / `.conns_dict` properties. Rule 3 (single driver) conservatively skips instance connections — the IR lacks the instantiated module's port directions. |

Supporting specs:

- `ClockSpec(name: str = "clk", edge: pos|neg = pos)`
- `ResetSpec(name: str, kind: sync|async, active_low: bool)` — the canonical
  IR name is `rst`; the style engine appends `_n` when `active_low=True`.

## 4. Reset Composition (renderer behavior)

Given `AlwaysFF(clock=C, reset=R, reset_body=RB, body=B)`:

| `R.kind` | Sensitivity list | Skeleton |
|---|---|---|
| `sync` | `posedge clk` | `if (<rst-active>) RB else B` |
| `async` | `posedge clk or negedge rst_n` (edge matches polarity) | same skeleton |
| `None` | `posedge clk` | `B` only |

`<rst-active>` is `!rst_n` for active-low, `rst` for active-high. SV emits
`always_ff`; Verilog emits `always @(...)`. Identical body IR, four reset
variants — this is the single point where the PRD's reset-style and
reset-polarity options take effect.

## 5. FSM Support

The FSM snippet (hero snippet) exercises `EnumDecl` + `Case`:

- One `EnumDecl` for the state type with user-selected encoding.
- State register: `AlwaysFF` whose body is `Assign(state, state_next)`.
- Next-state logic: `AlwaysComb` with a `Case` over `state` using `EnumRef`
  labels; default assignment of `state_next = state` emitted first (no
  latches, no missing-arm hazards).
- Moore outputs: separate `AlwaysComb` case or `ContAssign` per output.
  Mealy outputs: next-state `Case` bodies may also assign outputs.

Encoding is applied at declaration (Verilog localparam values / SV enum
values), not scattered through logic — changing encoding never touches the
case structure.

## 6. IR Validation (pre-render)

`ir.validate(module)` runs before any rendering. Errors here are generator
bugs, not user errors; they fail loudly in tests and return HTTP 500, never
silently degrade.

1. All names are valid canonical identifiers (`lower_snake_case`;
   `UPPER_SNAKE_CASE` for params — design rule 5); no duplicates among
   params/ports/signals/enums.
2. Every `Ref`/`EnumRef` resolves to a declared name.
3. Single-driver rule: each signal driven by exactly one of {one procedural
   block, one `ContAssign`, one instance output}. (Multiple assigns *within*
   one block are fine.)
4. `Assign.lhs` is a valid lvalue; ports of dir `input` are never driven.
5. `Case` over an enum either covers all members or has a `default`;
   non-enum `Case` always has a `default`.
6. `AlwaysFF` with `reset=None` has empty `reset_body`.
7. Post-style reserved-word check (SV *and* Verilog keyword sets, since either
   target may be rendered).

Deeper checks (width mismatch, latch inference, unused signals) are
delegated to the Verilator `--lint-only -Wall` gate — no duplication of a
lint engine inside the IR.

## 7. Rendering Summary (SV vs Verilog)

| IR | SystemVerilog | Verilog-2001 |
|---|---|---|
| `Signal` / `Port` type | `logic [W-1:0]` | `reg` or `wire` `[W-1:0]` (inferred, rule 6) |
| `AlwaysFF` | `always_ff @(...)` | `always @(...)` |
| `AlwaysComb` | `always_comb` | `always @(*)` |
| `Assign` in FF / comb | `<=` / `=` | `<=` / `=` |
| `EnumDecl` | `typedef enum logic [N-1:0] {...}` | `localparam [N-1:0] S_IDLE = ...` per member |
| `Case unique` | `unique case` | `case` + intent comment |
| `Param` | `parameter int unsigned` | `parameter` |
| Module ports | ANSI style | ANSI style (2001) |

Both renderers share one tree walker (`render/base.py`); language classes
override only the table above plus declaration syntax. Output formatting
(indent width, alignment, one-statement-per-line) lives in the style engine
and applies identically to both languages.

## 8. Non-Goals for v0.1 (planned extensions)

- Generate loops / genvar (Phase 2 modules will need them — add `GenFor`).
- Memories / unpacked arrays (Phase 4 RAM/FIFO — add `Memory` node).
- Division/modulo operators (add when a snippet needs them, with width notes).
- `inout` ports, tristate.
- Functions/tasks, packages, interfaces, structs.
- Assertions (Phase 3 — likely a parallel `sva` node family, not statements).
- Testbench constructs: `initial`, delays, `$display` (Phase 3 TB generator
  gets its own restricted node set; the synthesizable IR stays clean).
- JSON serialization of IR (debug dump may come earlier; not a stable format).

## 9. Example — 8-bit counter, async active-low reset, enable

Generator output (abridged builder code):

```python
m = Module(
    name="counter",
    header=Header(license=LICENSE_STAMP, config_hash=h, description="Up counter"),
    params=[Param("WIDTH", Const(8), doc="Counter width in bits")],
    ports=[
        Port("clk", IN, bit()),
        Port("rst", IN, bit(), doc="Async reset, active-low"),
        Port("en", IN, bit(), doc="Count enable"),
        Port("count", OUT, vec("WIDTH")),
    ],
    items=[
        AlwaysFF(
            clock=ClockSpec("clk"),
            reset=ResetSpec("rst", kind=ASYNC, active_low=True),
            reset_body=[Assign(Ref("count"), Const(0, width=Ref("WIDTH")))],
            body=[If(Ref("en"), then=[
                Assign(Ref("count"), BinOp("+", Ref("count"), Const(1)))
            ])],
        )
    ],
)
```

SystemVerilog rendering:

```systemverilog
module counter #(
    parameter int unsigned WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst_n,   // Async reset, active-low
    input  logic             en,      // Count enable
    output logic [WIDTH-1:0] count
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

Verilog rendering differs only per the §7 table (`reg [WIDTH-1:0] count` as
an output reg, `always @(posedge clk or negedge rst_n)`, `parameter WIDTH = 8`).
Same IR, both languages, all four reset variants from one generator.
