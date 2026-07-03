# SemiCraft Implementation Plan

Version 0.1. Companion documents: [SemiCraft_PRD.md](../SemiCraft_PRD.md), [IR_SPEC.md](IR_SPEC.md).

This plan decomposes the MVP (RTL Snippet Generator) into work packages (WPs).
Each WP is scoped so a single sub-agent can implement it end-to-end from this
document plus the referenced specs, without needing conversation context.

## 1. Ground Rules (apply to every WP)

- **Stack:** Python 3.12+, `uv` for dependency management, `ruff` for lint+format,
  `pytest` for tests, FastAPI + Uvicorn for the API, Pydantic v2 for schemas.
  Frontend: Next.js (App Router, TypeScript), Monaco editor, Tailwind.
- **Layout:** monorepo as defined in §2. Backend core (`semicraft_core`) has
  zero web dependencies — importing it must not pull in FastAPI.
- **Determinism:** no timestamps, random values, dict-ordering dependence, or
  environment-dependent output anywhere in the generation path. Same config →
  byte-identical output. This is a release criterion (PRD §11).
- **Every WP ships its own tests.** A WP is not done until its tests pass and
  existing tests still pass. New generator output must pass
  `verilator --lint-only -Wall` once WP-04 lands (before that, mark golden
  files as `lint: pending`).
- **Interfaces are frozen by spec.** IR node shapes come from IR_SPEC.md §3.
  The snippet contract and API contract are frozen in §3 and §4 of this plan.
  A WP that needs an interface change must stop and surface the conflict, not
  silently change shared code.
- **Style:** generated RTL follows the SemiCraft default style (WP-09 style
  guide; until it exists: lower_snake_case, `_n` active-low suffix, 4-space
  indent, ANSI ports, `always_ff`/`always_comb` in SV).
- **License stamp:** every generated file header includes: tool name+version,
  config hash, and the disclaimer "Generated code is provided as-is, without
  warranty of any kind. Free for commercial and non-commercial use at the
  user's own risk."

## 2. Repository Layout (created in WP-00)

```
semicraft/
├── pyproject.toml               # uv-managed, workspace root for backend
├── .github/workflows/ci.yml
├── Dockerfile                   # backend + verilator
├── docs/
│   ├── IR_SPEC.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── STYLE_GUIDE.md           # WP-09
├── backend/
│   ├── semicraft_core/
│   │   ├── ir/
│   │   │   ├── __init__.py
│   │   │   ├── nodes.py         # WP-01
│   │   │   ├── build.py         # WP-01 (builder helpers)
│   │   │   └── validate.py      # WP-01
│   │   ├── render/
│   │   │   ├── base.py          # WP-02
│   │   │   ├── sv.py            # WP-02
│   │   │   ├── verilog.py       # WP-02
│   │   │   └── style.py         # WP-02
│   │   ├── snippets/
│   │   │   ├── __init__.py
│   │   │   ├── contract.py      # WP-03 (base classes, ExplanationDoc)
│   │   │   ├── registry.py      # WP-03
│   │   │   ├── counter.py       # WP-03 (reference snippet)
│   │   │   └── <snippet>.py     # WP-05a..05i
│   │   ├── lint/
│   │   │   └── verilator.py     # WP-04
│   │   └── version.py
│   ├── api/
│   │   └── main.py              # WP-06
│   └── tests/
│       ├── conftest.py
│       ├── ir/                  # WP-01
│       ├── render/              # WP-02
│       ├── snippets/            # WP-03, WP-05x
│       ├── golden/              # WP-08 infra; per-snippet dirs
│       ├── lint/                # WP-04
│       └── api/                 # WP-06
└── frontend/                    # WP-07 (Next.js app)
```

## 3. Frozen Contract: Snippet Module

Every snippet is one file in `semicraft_core/snippets/` exporting a
`SnippetDef`. WP-03 defines these types; snippet WPs implement against them.

```python
class SnippetDef:
    id: str                      # kebab-case, e.g. "shift-register"
    name: str                    # display name
    description: str             # one sentence, shown in catalog
    options_model: type[BaseModel]   # Pydantic v2 model, all fields have
                                     # defaults, constraints, and descriptions
    def generate(self, opts) -> Module: ...        # pure; IR per IR_SPEC.md
    def explain(self, opts) -> ExplanationDoc: ... # pure

class ExplanationDoc(BaseModel):
    purpose: str                     # what the snippet does
    configuration: list[str]         # human-readable summary of chosen options
    signals: list[SignalDoc]         # name, direction, description
    reset_behavior: str
    enable_behavior: str | None
    assumptions: list[str]
    limitations: list[str]
```

Common option fields (defined once in `contract.py`, mixed into snippets that
support them — do not redefine per snippet):

```python
class CommonOptions(BaseModel):
    language: Literal["sv", "verilog"] = "sv"
    reset_style: Literal["sync", "async"] = "sync"      # clocked snippets only
    reset_polarity: Literal["active_high", "active_low"] = "active_low"
    include_wrapper: bool = True     # False => fragment mode (render/base.py)
    comment_verbosity: Literal["none", "normal", "verbose"] = "normal"
    naming: NamingOptions            # convention + optional prefix/suffix
```

Registration: `registry.py` discovers all `SnippetDef` instances in the
package at import time and exposes `get(id)`, `all()`. Adding a snippet file
requires no registry edits.

## 4. Frozen Contract: HTTP API

```
GET /api/v1/snippets
  200 → { "snippets": [ { "id", "name", "description",
                          "json_schema": <Pydantic JSON Schema>,
                          "defaults": { ... } } ] }

POST /api/v1/generate
  body: { "snippet_id": str, "options": { ... } }     # options incl. language
  200 → { "code": str, "filename": str,               # e.g. "counter.sv"
          "language": "sv" | "verilog",
          "explanation": ExplanationDoc,
          "lint": { "status": "clean" | "warnings" | "unavailable",
                    "messages": [ { "severity", "code", "line", "text" } ] },
          "config_hash": str }                        # sha256[:12] of canonical options JSON
  422 → Pydantic validation errors (invalid options — user error)
  404 → unknown snippet_id
  500 → IR validation failure (generator bug; log + generic message)
```

`config_hash` = sha256 of `snippet_id` + canonical (sorted-keys) JSON of
options, truncated to 12 hex chars. Used in the file header and as the
frontend permalink key.

## 5. Work Packages

Dependency DAG:

```
WP-00 ──► WP-01 ──► WP-02 ──► WP-03 ──► WP-05a..i  (9 parallel)
                                 ├────► WP-04 ─┐
                                 ├────► WP-06 ─┼─► WP-08 ──► WP-10
WP-00 ─────────────────────────► WP-07 ────────┘
WP-09 (docs) anytime after WP-02
```

WP-07 (frontend) depends only on WP-00 plus the §4 contract — it develops
against a mock and integrates when WP-06 lands.

---

### WP-00 — Repo scaffold and tooling

**Depends on:** nothing. **Size:** S. **Parallel:** no (everything waits on it).
**Model:** sonnet — mechanical multi-tool scaffolding, no design decisions.

Tasks:
1. Create the §2 layout with empty packages and `pyproject.toml` (uv):
   deps `pydantic>=2`, `fastapi`, `uvicorn`; dev deps `pytest`, `ruff`, `httpx`.
2. `ruff` config: line length 100, `select = ["E","F","I","UP","B"]`, format on.
3. `pytest` config: `testpaths = ["backend/tests"]`.
4. CI (`ci.yml`): jobs = ruff check, pytest, and (once WP-04 exists) a job that
   installs Verilator (`apt-get install verilator`) and runs the golden lint gate.
5. `Dockerfile`: python:3.12-slim + `verilator` apt package + backend;
   entrypoint `uvicorn api.main:app`.
6. Scaffold `frontend/` with `create-next-app` (TypeScript, App Router,
   Tailwind, ESLint); add `monaco-editor/react` dependency. No features yet.
7. `semicraft_core/version.py` with `VERSION = "0.1.0"`.

Done when: `uv run pytest` passes (zero tests OK), `ruff check` clean,
`docker build` succeeds, `npm run build` in frontend succeeds, CI green.

---

### WP-01 — IR core

**Depends on:** WP-00. **Size:** M. **Spec:** IR_SPEC.md §2–§6 is normative.
**Model:** opus — foundational, spec-exact node/validation semantics; every later WP builds on it.

Tasks:
1. `ir/nodes.py`: all nodes from IR_SPEC §3 as frozen dataclasses
   (`@dataclass(frozen=True, slots=True)`). Enums for ops, directions,
   reset kind, encodings. Type-annotate fully.
2. `ir/build.py`: ergonomic helpers — `bit()`, `vec(width)`, `width(n_or_name)`,
   `IN`/`OUT` constants, small factories so generator code reads like the
   IR_SPEC §9 example.
3. `ir/validate.py`: `validate(module) -> None` raising `IRValidationError`
   with all seven checks from IR_SPEC §6 (reserved-word check takes the
   keyword sets as a parameter — style engine calls it post-transform).
4. Tests (`tests/ir/`): node construction/immutability; a hand-built valid
   module passes; one failing test per validation rule (7 minimum);
   the IR_SPEC §9 counter example builds and validates.

Done when: all IR_SPEC §3 nodes exist with matching fields, validation rules
1–7 each have a passing negative test.

---

### WP-02 — Renderers and style engine

**Depends on:** WP-01. **Size:** L. **Spec:** IR_SPEC §2 (rules 2,3,5,6,7),
§4 (reset composition), §7 (rendering table).
**Model:** fable — hardest WP: shared walker design, reset composition, reg/wire
inference, two-language correctness; subtle bugs here poison all snippets.

Tasks:
1. `render/base.py`: single tree walker with overridable emission hooks;
   handles indentation, statement blocks, expression rendering with full
   parenthesization, comment filtering by verbosity, **fragment mode**
   (`include_wrapper=False`: emit only declarations-as-comment + processes +
   continuous assigns, no `module`/`endmodule`).
2. `render/sv.py` and `render/verilog.py` per the IR_SPEC §7 table, including
   reg/wire inference (Verilog) and reset composition (§4) — reset composition
   logic lives in `base.py`, only keywords differ per language.
3. `render/style.py`: `StyleOptions` (naming convention: `snake` default,
   `camel`; prefix/suffix; active-low `_n` enforcement; indent width; comment
   verbosity). Applies name transforms to a rendered-name map before emission;
   runs reserved-word validation post-transform for BOTH language keyword sets.
4. Header rendering from `Header` node (license stamp per §1 ground rules).
5. Tests (`tests/render/`): golden strings for the IR_SPEC §9 counter in both
   languages × all four reset variants (8 outputs); fragment mode output;
   naming transform cases incl. reserved-word collision raising; comment
   verbosity none/normal/verbose; blocking vs non-blocking operator selection
   (Assign in AlwaysFF vs AlwaysComb); reg/wire inference cases.

Done when: §9 example renders exactly as shown in IR_SPEC (modulo header),
all reset variants correct, both renderers share the walker (no copy-paste
between sv.py and verilog.py beyond the keyword table).

---

### WP-03 — Snippet framework + counter reference snippet

**Depends on:** WP-02. **Size:** M.
**Model:** opus — counter is the reference implementation nine agents will copy;
quality here multiplies.

Tasks:
1. `snippets/contract.py`: `SnippetDef`, `ExplanationDoc`, `SignalDoc`,
   `CommonOptions`, `NamingOptions` exactly per §3 of this plan.
2. `snippets/registry.py`: import-time discovery of `SnippetDef` instances in
   the package; `get(id)`, `all()`; duplicate-id detection (hard error).
3. `snippets/counter.py` — the reference implementation others copy:
   - Options (extends common clocked options): `width: int (1..1024, default 8)`,
     `direction: up|down|updown (default up)` (`updown` adds `up_dn` input),
     `enable: bool (default True)`, `wrap: overflow|saturate (default overflow)`,
     `reset_value: int (default 0, validated < 2^width)`.
   - `generate()` builds IR (param `WIDTH`, ports, one `AlwaysFF`).
   - `explain()` fills every `ExplanationDoc` field meaningfully.
   - Cross-field validation via Pydantic `model_validator` (e.g. reset_value
     range) — invalid combos must fail validation, never generate silently
     wrong code (PRD §11).
4. End-to-end helper `semicraft_core.generate(snippet_id, options_dict)`
   returning `(code, filename, explanation, config_hash)` — the single entry
   point WP-04/06 build on. Implements config-hash per §4.
5. Tests: registry discovery; counter generates+validates+renders in both
   languages; option effects (width changes vector, direction=down uses `-`,
   updown adds port, saturate emits comparison, enable off removes port);
   determinism (two calls → identical bytes); invalid options raise.

Done when: `semicraft_core.generate("counter", {...})` produces lint-clean
(manually verified until WP-04) SV and Verilog for the default config and at
least 6 option variants, with complete explanations.

---

### WP-04 — Verilator lint integration

**Depends on:** WP-03. **Size:** S.
**Model:** sonnet — bounded subprocess wrapper + parser, well-specified.

Tasks:
1. `lint/verilator.py`: `lint(code: str, language, top: str) -> LintReport`.
   Writes code to a temp dir, runs
   `verilator --lint-only -Wall --timing <file>` (add `--default-language`
   per target), subprocess timeout 10 s, parses stderr into structured
   messages `(severity, code, line, text)`.
2. Graceful degradation: Verilator binary missing → `status: "unavailable"`
   (API still works; UI shows badge greyed). Never crash the request.
3. Fragment mode: lint the wrapped version (generate with wrapper forced on)
   so fragments are still checked; report notes this.
4. Tests: clean module → `clean`; module with intentional width mismatch →
   parsed warning with correct line; missing binary path → `unavailable`;
   timeout path (mock).
5. Wire the CI golden-lint job (WP-00 task 4 placeholder): every golden file
   must lint clean; failures list file + messages.

Done when: counter default config reports `clean` in both languages inside
the Docker image, and CI runs the lint gate.

---

### WP-05a..i — Remaining nine snippets (nine parallel packages)

**Depends on:** WP-03 (and WP-04 for the lint gate). **Size:** S–M each.
**Parallel:** yes — one sub-agent per snippet, no shared file edits (each
snippet = one new file + its tests + golden entries).
**Model:** sonnet for 05a–05h (pattern-following against the counter reference);
opus for 05i `fsm` (hero snippet: enum encodings, Moore/Mealy variants,
list-valued options — most design judgment of the nine).

Common requirements for every snippet WP: follow `counter.py` as the
template; options extend `CommonOptions` (omit reset/clock fields for purely
combinational snippets); `explain()` fully populated; cross-field validation
for illegal combos; tests mirror WP-03 task 5 (option effects, determinism,
both languages, invalid combos); golden files registered per WP-08 layout;
all goldens lint clean.

| WP | Snippet id | Options (beyond common) | Design notes |
|---|---|---|---|
| 05a | `register` | `width (1..1024, def 8)`, `enable (def true)`, `reset_value (def 0)`, `clear_input: bool (def false)` — synchronous clear port | Single `AlwaysFF`. Clear beats enable. |
| 05b | `shift-register` | `depth (2..256, def 8)`, `direction: left\|right (def right)`, `parallel_load: bool (def false)`, `serial_out_only: bool (def false)` | `{q[D-2:0], si}` concat shift. Parallel load adds `load`, `d[D-1:0]` ports. |
| 05c | `mux` | `num_inputs (2..16, def 4)`, `width (1..512, def 8)`, `impl: case\|ternary (def case)` | Inputs as numbered ports `in0..inN-1` (no arrays in IR v0.1). Select width = clog2 — compute in Python, emit as localparam. Non-power-of-2 N: default arm assigns `in0` + assumption note. |
| 05d | `demux` | `num_outputs (2..16, def 4)`, `width (def 8)`, `default_value: zeros\|hold (def zeros)` — hold only meaningful when clocked; MVP is combinational, so `zeros` only + document | `AlwaysComb` case; all outputs assigned defaults first (no latches). |
| 05e | `encoder` | `kind: priority\|onehot (def priority)`, `num_inputs: 4\|8\|16 (def 8)`, `valid_output: bool (def true)` | Priority: if/elif chain, LSB lowest priority (documented). Onehot: case with onehot labels + default → `valid=0`. |
| 05f | `decoder` | `num_outputs: 2\|4\|8\|16 (def 8)`, `enable: bool (def true)`, `output_polarity: active_high\|active_low (def active_high)` | `ContAssign` with shift: `out = en ? (1 << sel) : '0`, inverted for active-low. |
| 05g | `comparator` | `width (def 8)`, `signed: bool (def false)`, `outputs: subset of {eq, ne, lt, le, gt, ge} (def {eq, lt, gt})` — min 1 | One `ContAssign` per selected output. Signed uses `signed` DataType on inputs. |
| 05h | `cdc-synchronizer` | `stages (2..4, def 2)`, `width (1..8, def 1)`, `use_reset: bool (def false)` | Chain of registers, canonical names `sync_ff1..N`. `width > 1` adds an assumption warning in explanation: multi-bit CDC only safe for gray-coded/quasi-static signals. This text is mandatory. |
| 05i | `fsm` | `states: list[str] (2..16 names, valid identifiers, unique)`, `encoding: binary\|onehot\|gray (def binary)`, `machine: moore\|mealy (def moore)`, `reset_state: str (must be in states)`, `outputs: list[str] (0..8 names)` | Hero snippet. Emits: `EnumDecl`, state reg `AlwaysFF`, next-state `AlwaysComb` with `state_next = state` default then one case arm per state containing a `Comment("TODO: transition logic for <state>")`, output logic skeleton (Moore: comb case on state; Mealy: comment in next-state arms). Explanation documents that transitions are user-completed. Largest snippet — size M. |

Done (each) when: snippet passes its tests, goldens lint clean in both
languages, registry exposes it, `explain()` renders sensibly.

---

### WP-06 — HTTP API

**Depends on:** WP-03 (WP-04 for lint field). **Size:** M.
**Model:** sonnet — contract is frozen in §4; implementation is standard FastAPI.

Tasks:
1. `api/main.py`: FastAPI app implementing §4 exactly. CORS for the frontend
   dev origin. `GET /api/v1/snippets` builds catalog from registry (JSON
   Schema via `model_json_schema()`; verify enums/constraints/descriptions
   survive — frontend forms depend on them).
2. `POST /api/v1/generate`: validate options against the snippet's model
   (422 with Pydantic error detail on failure), call
   `semicraft_core.generate`, run lint (WP-04), assemble response.
   `IRValidationError` → 500 + server log (generator bug).
3. Filename rule: `<module_name>.<sv|v>`; fragment mode: `<module_name>_fragment.<ext>`.
4. Basic hardening: request body limit, options dict depth/size limit,
   FSM state-name list already length-capped by schema.
5. Tests (`tests/api/`, httpx): catalog lists all 10 snippets with schemas;
   generate happy path for counter and fsm; 422 on bad option; 404 unknown id;
   response `config_hash` stable across calls; lint field present.

Done when: `uvicorn api.main:app` serves both endpoints, all API tests pass,
manual `curl` of counter returns compilable SV.

---

### WP-07 — Frontend

**Depends on:** WP-00 + §4 contract (mock until WP-06 lands). **Size:** L.
**Model:** opus — large scope; the schema-driven dynamic form renderer is the
core deliverable and needs real design judgment plus polished UX.

Tasks:
1. Single-page generator UI (PRD §9: opens directly into the experience).
   Layout: left panel = snippet picker + options form; right panel = Monaco
   preview (read-only, `systemverilog`/`verilog` syntax) always visible.
2. **Dynamic form renderer** from JSON Schema: string enum → segmented control
   (≤4 options) or dropdown; boolean → toggle; integer with min/max → numeric
   input with validation; `array of string` (FSM states/outputs) → tag/chips
   input; field descriptions as help tooltips. No per-snippet frontend code —
   this is the core deliverable.
3. Generation flow: debounce 300 ms on option change → POST /generate →
   update preview. Errors: 422 field errors mapped back onto the form inline.
4. Output affordances: copy button, download (blob, filename from response),
   lint badge (clean = green "Lint clean · verilator -Wall", warnings =
   amber with expandable message list, unavailable = grey).
5. Explanation panel: collapsible section rendering `ExplanationDoc`
   (purpose, configuration, signals table, reset/enable behavior,
   assumptions, limitations).
6. Permalink: serialize `snippet_id` + options into the URL query
   (compressed JSON, e.g. base64url); restore on load.
7. Mock layer: `frontend/mocks/` with recorded catalog + generate responses;
   env flag switches mock vs real API. Integration checklist against WP-06.
8. Tests: form renderer unit tests against the counter and fsm JSON Schemas
   (all widget types exercised); permalink round-trip; component test of the
   generate flow against the mock.

Done when: user can pick any snippet, edit options, see live-updating
lint-badged code, copy/download it, read the explanation, and share a URL
that restores the exact config. PRD MVP success metric: full flow < 1 minute.

---

### WP-08 — Golden matrix and regression infrastructure

**Depends on:** WP-03 (extends as WP-05x land). **Size:** M.
**Model:** sonnet — pytest plumbing with clearly specified case-selection rules.

Tasks:
1. `tests/golden/` framework: per snippet, a `cases.py` declaring a list of
   named option dicts. For each case × each language: snapshot file
   `tests/golden/<snippet>/<case>.<ext>`.
2. Case selection: defaults case + one case per option flipping it from
   default + 2–3 pairwise combination cases per snippet. Full cross-product
   explicitly out of scope. Every reset style × polarity combination must
   appear at least once per clocked snippet.
3. Snapshot runner: `pytest` compares generated output to golden byte-exact;
   `--update-golden` flag regenerates; CI never updates.
4. Lint gate: parametrized test running WP-04 lint over every golden file;
   must be `clean` (not just no-error).
5. Property test helpers used by snippet tests: `assert_port_present`,
   `assert_port_absent`, `assert_output_differs(opts_a, opts_b)`.
6. Determinism test: generate every golden case twice in separate processes,
   compare hashes.

Done when: all 10 snippets have golden coverage per rule 2, CI runs snapshot
+ lint gates, PRD release criterion "generator regression tests exist for
each supported snippet category" is met.

---

### WP-09 — Style guide + user docs

**Depends on:** WP-02. **Size:** S. **Parallel:** yes.
**Model:** sonnet — writing docs that must be verified against golden output;
haiku risks drift between guide and renderer behavior.

Tasks:
1. `docs/STYLE_GUIDE.md`: the published SemiCraft RTL style — naming rules,
   `_n` convention, reset idioms (the four §4 IR_SPEC variants), always-block
   patterns, comment conventions, formatting. Must match renderer output
   exactly (this doc is a selling point per PRD).
2. Root `README.md`: what SemiCraft is, MVP scope, quickstart (docker run +
   frontend dev), architecture pointer to IR_SPEC + this plan.
3. License/disclaimer text single-sourced in `semicraft_core` (used by header
   rendering) and referenced in README.

Done when: docs exist, style guide statements verified against actual
renderer golden output (no drift).

---

### WP-10 — Integration, deploy, release checklist

**Depends on:** all. **Size:** S.
**Model:** sonnet — checklist execution and smoke scripts against existing pieces.

Tasks:
1. `docker compose` (or single Dockerfile multi-stage) serving API + built
   frontend; smoke script hitting /snippets and one /generate per snippet.
2. End-to-end check against PRD §11 MVP release criteria, item by item; record
   results in `docs/RELEASE_CHECKLIST.md`.
3. Cut `v0.1.0` tag.

---

## 6. Suggested Execution Waves

| Wave | WPs | Agents | Models |
|---|---|---|---|
| 1 | WP-00 | 1 | sonnet |
| 2 | WP-01; WP-07 (mock-first, long-running); WP-09 draft | 2–3 | opus; opus; sonnet |
| 3 | WP-02 | 1 | fable |
| 4 | WP-03 | 1 | opus |
| 5 | WP-04, WP-06, WP-05a–05i, WP-08 infra | up to 12 parallel | sonnet ×10, opus (05i) |
| 6 | WP-07 integration, WP-08 completion, WP-09 verify | 2–3 | opus; sonnet; sonnet |
| 7 | WP-10 | 1 | sonnet |

Model-tiering rationale: **fable** only for WP-02 (single hardest package;
errors there propagate into every generated file). **opus** for
foundation/reference/judgment work (IR, snippet framework, FSM, frontend form
engine). **sonnet** for everything with a frozen contract and a reference
implementation to follow. **haiku** deliberately unused — every WP either
touches shared correctness or must verify against specs; the review cost of a
weaker model exceeds its savings here.

Critical path: WP-00 → 01 → 02 → 03 → (05i fsm, longest snippet) → 08 → 10.

## 6b. Domain Reference: VLSI Agent Kit

The user's VLSI Agent Kit at `D:\Projects\VLSI-agkit\.agent\skills\` provides
domain knowledge modules. Dispatch prompts for RTL-producing WPs should
instruct the agent to read the relevant SKILL.md files as *reference material*
(SemiCraft's own specs remain normative where they conflict — e.g. the kit's
`i_`/`o_` port-prefix convention is NOT SemiCraft default style; prefixes are
a user style option):

| WP | Kit skills to read |
|---|---|
| WP-03, WP-05a–g | `clean-rtl`, `systemverilog-patterns` |
| WP-05h cdc-synchronizer | above + `clock-domain-crossing` (assumptions/limitations content) |
| WP-05i fsm | above + `fsm-design` |
| WP-02 renderers (review) | `clean-rtl` (synthesizable-pattern checks) |

## 7. Sub-Agent Prompt Template

When dispatching a WP, the prompt should contain: (1) pointer to this file +
IR_SPEC.md + PRD; (2) the WP section verbatim; (3) ground rules §1; (4) the
frozen contracts §3–§4 if touched; (5) instruction to run
`ruff check && pytest` before finishing and to report any needed interface
change instead of making it. Dispatch with the WP's **Model** line (also
summarized in the §6 table); if a sonnet-assigned agent reports repeated test
failures or an interface conflict, re-dispatch that WP on opus rather than
iterating.

## 8. Risks Specific to Implementation

- **JSON Schema fidelity (WP-06→07 seam):** Pydantic v2 schema output must
  carry enums, bounds, and descriptions the form renderer needs. Mitigation:
  WP-06 test asserts schema shape for counter + fsm; WP-07 builds its form
  tests on those exact schemas.
- **Verilog `reg` inference edge cases (WP-02):** output ports driven
  procedurally need `output reg`. Covered by explicit render tests + lint gate.
- **FSM options UX (05i + 07):** list-of-strings inputs are the only
  non-scalar form widgets; both sides must agree on JSON Schema `array` shape.
  Mitigation: fsm schema fixture shared into frontend tests.
- **Windows dev environment:** Verilator is Linux-first. Local dev on Windows
  runs lint via the Docker image (document in README); `status: "unavailable"`
  path keeps the API usable without it.
