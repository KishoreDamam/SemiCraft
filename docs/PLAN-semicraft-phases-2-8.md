# SemiCraft Phases 2–8 — Implementation Plan

Version 0.1 (post-v0.1.0 MVP). Companions: [SemiCraft_PRD.md](../SemiCraft_PRD.md) §12,
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) (Phase 1, executed),
[IR_SPEC.md](IR_SPEC.md).

Same execution model as Phase 1: work packages (WPs) dispatched to sub-agents,
model per WP, frozen contracts, verify-commit-push per WP, PROGRESS.md as
handoff state. WP ids are `P<phase>-<nn>`. Ground rules of IMPLEMENTATION_PLAN
§1 apply throughout; the dispatch template of §7 and the VLSI-agkit skill
mapping of §6b extend to every RTL-producing WP below.

## Overview

Seven phases take SemiCraft from snippet generator to platform: full modules
(P2), verification artifacts + real simulation (P3), curated IP library (P4),
connected subsystems (P5), external IP integration (P6), application/reference
designs (P7), AI assistance over the deterministic core (P8). Each phase ships
usable value alone; each reuses the IR → render → lint → golden pipeline.

## Requirements (carried across all phases)

- Determinism and golden regression discipline stay mandatory everywhere.
- IR remains the single source of RTL; no phase introduces string-template RTL.
- Frozen-contract changes require a recorded decision, never a silent edit.
- PRD §11 post-MVP release criteria gate each phase's exit.

## Cross-cutting decisions (decide once, at P2 start)

These affect every later phase; lock them in P2-01 before parallel work.

1. **API v2 multi-file result.** Phases 2+ emit multiple files (RTL + TB +
   docs + filelist). `GenerateResult.code/filename` becomes
   `files: list[GeneratedFile(path, kind, text)]`; `/api/v1/generate` stays
   for snippets, new `/api/v2/generate` returns the file set + zip download.
   Frontend gains a file-tab preview. This is THE breaking contract change —
   do it first, once.
2. **IR versioning.** IR_SPEC gains a changelog section; every node addition
   states which phase needs it and which renderer behavior it implies. New
   nodes in P2: `GenFor` (genvar loops), `Memory` (unpacked array +
   sync read/write ports), `EnumType` reference on `DataType` (closes the
   deferred typed-state-signal gap), `Function` (small pure helpers). P3 adds
   a SEPARATE `tb` node family (Initial, Delay, ClockGen, Finish, Assert...)
   that the synthesizable validator rejects — TB and RTL never mix.
3. **Sim sandbox service.** One reusable runner (P3+): Docker image with
   Verilator (+ Icarus fallback), compile+run with wall-clock and output
   limits, no network, artifact capture (log, VCD on request). Local Windows
   dev keeps `unavailable` degradation; CI and deployed backend run it real.
4. **Catalog taxonomy.** Registry gains `kind: snippet|module|ip|subsystem|app`
   and `maturity: stable|beta`. One catalog, filterable; frontend groups by
   kind. Avoids parallel registries per phase.

---

## Phase 2 — RTL Module Generator + Early Validation

Goal: complete, reusable, parameterized modules (not fragments) with smoke
testbenches. PRD exit: "generated modules have basic validation coverage."

### Tasks

| WP | Scope | Size | Model | Depends |
|---|---|---|---|---|
| P2-01 | Cross-cutting decisions: API v2 files contract, catalog taxonomy, IR v0.2 spec deltas written into IR_SPEC (GenFor, Memory, EnumType-on-DataType, Function, changelog) | M | opus | — |
| P2-02 | IR v0.2 implementation + validation rules for new nodes | M | opus | P2-01 |
| P2-03 | Renderer support for new nodes both languages (generate blocks, memory decls, typed enum signals) | L | opus | P2-02 |
| P2-04 | Module contract: `ModuleDef` extends snippet contract with multi-file output, port-group metadata, per-module smoke-TB hook | M | opus | P2-01 |
| P2-05 | API v2 + zip download + frontend file tabs (backend sonnet + frontend opus split into P2-05a/b) | M/L | sonnet+opus | P2-04 |
| P2-06..12 | Module set, one WP each: edge detector; debouncer; clock divider; PWM generator; round-robin arbiter; LFSR; gray-code counter | S–M each | sonnet (arbiter: opus) | P2-04, P2-03 |
| P2-13 | Smoke-TB generator: per-module Verilator-compatible TB (clock gen, reset seq, N directed vectors from module metadata), emitted as second file; uses tb node family STUB (initial+delay only, spec'd in P2-01, full family lands P3) | L | opus | P2-04 |
| P2-14 | Golden matrix extension to modules incl. TB files; CI compiles every golden TB with `verilator --timing --binary` (compile-only) | M | sonnet | P2-13 |
| P2-15 | Docs + release v0.2.0 | S | sonnet | all |

- [ ] Exit: 7 modules × both languages, each with smoke TB compiling under Verilator in CI, golden-locked, catalog-filterable, zip-downloadable.

Key risks: renderer complexity jump (generate blocks interact with naming/style
engine — P2-03 carries the same poison-downstream risk WP-02 did; give it an
extra review pass); TB determinism (no timestamps, fixed seeds).

---

## Phase 3 — Verification Artifact Generator

Goal: verification as product: directed TBs, assertions, checkers, monitors,
scoreboards, sim scripts, real simulation runs. PRD exit: "generated
testbenches run against at least one supported module family."

### Tasks

| WP | Scope | Size | Model | Depends |
|---|---|---|---|---|
| P3-01 | TB IR node family full spec + implementation (Initial, Delay, ClockGen, ResetSeq, Fork, Finish, Display, AssertProperty stub) + tb validator (rejects synthesizable-only nodes misuse and vice versa) | L | opus | — |
| P3-02 | TB renderers (SV-first; Verilog TB subset) + sim-script emitter (Makefile + run.sh for Verilator, Icarus fallback) | L | opus | P3-01 |
| P3-03 | Sim sandbox service (cross-cutting decision 3): container runner, API `/api/v2/simulate`, queue + timeout + artifact capture; frontend "Run smoke sim" button with log viewer | L | opus | P3-02 |
| P3-04 | Directed-TB generator upgrade: stimulus tables from module metadata (per-port constraints), self-checking expected-value hooks | L | opus | P3-02 |
| P3-05 | SVA assertion template generator: reset behavior, handshake (valid/ready), stability, onehot-state assertions bound to FSM/module metadata | M | opus | P3-01 |
| P3-06 | Checker/monitor/scoreboard scaffolds (SV classes/modules, directed not UVM per PRD non-goal) | M | sonnet | P3-02 |
| P3-07 | Test-plan/checklist document generator from module metadata | S | sonnet | P3-04 |
| P3-08 | cocotb alternative backend for TBs (Python TB emission; runs under sim sandbox) — beta flag | M | sonnet | P3-03 |
| P3-09 | Golden + CI: every generated TB RUNS (not just compiles) green in CI against its module; release v0.3.0 | M | sonnet | all |

- [ ] Exit: pick counter+register+fifo-lite module family; generated directed TB + assertions run green in CI sandbox; sim results surfaced in UI.

Key risks: sandbox security (only self-generated code initially — keep it
that way until P6 review); sim wall-clock in CI (cap vectors).

---

## Phase 4 — IP Block Library

Goal: curated configurable IP with docs + verification scaffold each. PRD
list: FIFO, RAM/ROM, UART, SPI, I2C, AXI-Lite register block, timer,
interrupt controller.

### Tasks

| WP | Scope | Size | Model | Depends |
|---|---|---|---|---|
| P4-01 | IP contract: `IpDef` = ModuleDef + register-map metadata + interface declarations (bus-side port bundles) + doc template + verification scaffold hook; interface abstraction (named port bundles — NOT SV interfaces yet, flat ports with bundle metadata) | M | opus | P3 done |
| P4-02 | Register-map model (fields, access types RW/RO/W1C, address calc) + AXI-Lite register block generator — the keystone IP others reuse | L | opus | P4-01 |
| P4-03 | Sync FIFO (+ async FIFO with gray-pointer CDC, reusing cdc discipline) | M | opus | P4-01 |
| P4-04 | RAM/ROM (single/dual port, init file support via Memory node) | M | sonnet | P4-01 |
| P4-05 | UART (tx/rx, param baud, AXI-Lite regblock frontend) | L | opus | P4-02 |
| P4-06 | SPI master | M | sonnet | P4-02 |
| P4-07 | I2C master | L | opus | P4-02 |
| P4-08 | Timer + basic interrupt controller (two IPs, shared WP) | M | sonnet | P4-02 |
| P4-09 | Per-IP verification scaffold (P3 generators applied: TB + assertions + smoke sim in CI) | L | opus | P4-03.. |
| P4-10 | Per-IP documentation generator (md datasheet from metadata: ports, regs, timing diagrams as wavedrom JSON) | M | sonnet | P4-01 |
| P4-11 | Example instantiations per IP + golden + release v0.4.0 | M | sonnet | all |

- [ ] Exit: 8+ IPs, each: both-language RTL (where sensible; AXI IPs SV-only is an allowed documented exception), regblock-driven where applicable, datasheet, TB running in CI.

Key risks: protocol correctness (UART/SPI/I2C — opus + agkit skills +
protocol checklists; sim-verified in CI is the safety net); async FIFO CDC
(dedicated review pass on P4-03 output).

---

## Phase 5 — Subsystem Generator

Goal: connected groups of IPs: register-mapped peripheral subsystem, address
map, interconnect glue, top wrapper, subsystem TB + docs. PRD exit:
"top-level wiring, address maps, filelists internally consistent."

### Tasks

| WP | Scope | Size | Model | Depends |
|---|---|---|---|---|
| P5-01 | Subsystem contract: `SubsystemDef` = composition model (instances of IpDefs + params), address-map allocator (auto + manual override, overlap validation), clock/reset domain declaration | L | opus | P4 done |
| P5-02 | Interconnect generator: AXI-Lite 1-to-N decoder/mux glue from address map | L | opus | P5-01 |
| P5-03 | Top-level wrapper emission: instance wiring, port promotion rules, filelist (.f) + dependency-ordered file emission | M | opus | P5-01 |
| P5-04 | Canned subsystems: UART+timer+GPIO peripheral subsystem; SPI+I2C comms subsystem; memory-mapped control subsystem | M each ×3 | sonnet | P5-02,03 |
| P5-05 | Subsystem TB: bus-functional master driving register reads/writes across the address map, smoke per instance | L | opus | P5-03 |
| P5-06 | Subsystem docs: memory map table, block diagram (mermaid/SVG), integration notes | S | sonnet | P5-03 |
| P5-07 | Frontend: composition UI (pick IPs, set base addresses, live address-map view) — biggest UI change since MVP | L | opus | P5-01 |
| P5-08 | Golden + consistency CI (address map ↔ RTL decode ↔ docs cross-check test) + release v0.5.0 | M | sonnet | all |

- [ ] Exit: user composes a 3-peripheral subsystem in UI, downloads zip (RTL + TB + filelist + memory-map doc), TB runs green in CI.

---

## Phase 6 — External IP Integration

Goal: user-provided/third-party IP into generated subsystems. PRD exit:
"metadata, port mapping, parameter mapping, wrappers reviewable by user."

### Tasks

| WP | Scope | Size | Model | Depends |
|---|---|---|---|---|
| P6-01 | External-IP metadata schema (the IP-XACT-aligned JSON subset locked in PRD §15): ports, params, interfaces, clocks/resets, files. Importer + validator + STRICT review report | L | opus | P5 done |
| P6-02 | Verilog/SV port-list extractor (parse module header only — slang or verible as parser dependency, decision WP) to bootstrap metadata from user RTL; user confirms/edits — never silently trusted | L | opus | P6-01 |
| P6-03 | Mapping engine: external interface ↔ SemiCraft bundle mapping, width/polarity adapters, clock/reset domain declaration | L | opus | P6-01 |
| P6-04 | Wrapper + glue generation, filelist merge, integration checklist doc (every assumption listed for human signoff) | M | opus | P6-03 |
| P6-05 | Subsystem integration: external IP as instance in P5 composer, address-map slot for mapped regblocks | M | opus | P6-04 |
| P6-06 | Sim scaffold with user IP as black box (compile-only gate; user code NEVER runs in shared sandbox — document threat model; optional local-run scripts instead) | M | sonnet | P6-04 |
| P6-07 | Frontend: metadata editor + mapping review UI + golden + release v0.6.0 | L | opus | P6-01 |

- [ ] Exit: import a third-party UART's metadata, map it into the P5 peripheral subsystem, download consistent wrapper+glue+filelist+checklist.

Key risk: parsing arbitrary user RTL — scope to header extraction only,
review-first workflow; security: uploaded RTL treated as data, not executed in
shared infra.

---

## Phase 7 — Application / Reference Design Generator

Goal: application-level starting points. PRD list: peripheral controller app,
sensor interface pipeline, memory-mapped accelerator shell, streaming datapath.

### Tasks

| WP | Scope | Size | Model | Depends |
|---|---|---|---|---|
| P7-01 | App contract: `AppDef` = subsystem(s) + project structure (rtl/, tb/, sim/, docs/, constraints-stub/), build+sim script generation, README generation | M | opus | P6 done |
| P7-02..05 | The four reference designs, one WP each (compose existing subsystems/IPs; new RTL only for app-specific glue) | M each | opus ×2 (accelerator shell, streaming) + sonnet ×2 | P7-01 |
| P7-06 | Vendor hooks (deferred from MVP decision "vendor-specific later"): optional Vivado XDC stub + project TCL, Quartus SDC stub — generation only, no tool execution | M | sonnet | P7-01 |
| P7-07 | Golden + docs + release v0.7.0 | S | sonnet | all |

- [ ] Exit: one-click reference design zip that simulates green out of the box with included scripts.

---

## Phase 8 — AI-Assisted SemiCraft

Goal: AI as assistant layer OVER deterministic flows (PRD §12 phase 8: AI uses
existing schemas/templates/validation; suggestions reviewable, never direct
output). MVP-era principle stands: AI never becomes the source of truth.

### Tasks

| WP | Scope | Size | Model | Depends |
|---|---|---|---|---|
| P8-01 | AI gateway design: server-side Claude API integration; every AI feature = structured tool call producing a SemiCraft config (validated by existing Pydantic schemas) + rationale; nothing AI-produced bypasses validation/lint/golden pipeline. Decision doc: model choice, cost caps, opt-in privacy posture (user design data never used for anything but the request) | M | opus | P5+ recommended |
| P8-02 | "Describe → configure": NL requirement → recommended catalog item + prefilled options, shown as a diff against defaults for user approval | L | opus | P8-01 |
| P8-03 | Explain assistant: chat over generated RTL/TB grounded in the ExplanationDoc + IR (not raw text guessing) | M | sonnet | P8-01 |
| P8-04 | Verification advisor: suggest missing test cases/assertions from module metadata; emits P3-generator configs, user approves each | L | opus | P8-01, P3 |
| P8-05 | Subsystem/config reviewer: address-map sanity, CDC pairing checks, option-combination smells — advisory report only | M | opus | P8-01, P5 |
| P8-06 | External-IP mapping assistant: propose port mappings for P6 review UI (highest-value AI use; still human-confirmed) | M | opus | P8-01, P6 |
| P8-07 | Frontend AI panel (clearly separated from deterministic UI per PRD §9), telemetry-free eval set + prompt regression harness, release v0.8.0 | L | opus | P8-02.. |

- [ ] Exit: every AI feature demonstrably constrained to schema-valid, human-approved suggestions; product fully usable with AI disabled.

---

## Deliverables (cumulative)

- [ ] v0.2.0 — modules + smoke TBs + API v2 files
- [ ] v0.3.0 — verification artifacts + sim sandbox
- [ ] v0.4.0 — 8-IP library with datasheets + CI-simulated scaffolds
- [ ] v0.5.0 — subsystem composer
- [ ] v0.6.0 — external IP integration
- [ ] v0.7.0 — reference designs + vendor constraint stubs
- [ ] v0.8.0 — AI assistant layer

## Dependencies

- Verilator-capable CI (exists) + container runtime for sim sandbox (P3).
- Parser library decision for P6-02 (slang vs verible) — spike WP before commit.
- Claude API key/billing for P8 (server-side only).
- VLSI-agkit skills per IMPLEMENTATION_PLAN §6b; add mappings: P3 →
  formal-verification + uvm-patterns (patterns only, no UVM output), P4 →
  axi-protocols + ip-reuse, P5/P6 → ip-reuse + timing-constraints, P7 →
  fpga-flows/asic-flows.

## Execution notes

- One phase active at a time; inside a phase, waves like Phase 1 (contract WP
  first, then parallel fan-out, then integration/release WP).
- Model tiering: two tiers only — opus for contracts, IR/renderer work,
  protocol IPs, and anything whose errors poison downstream WPs (P2-03,
  P3-01/02, P4-02, P5-01, P6-03 get an extra review pass in lieu of a higher
  tier); sonnet for pattern work against references. Fable is NOT used for
  any WP (user decision).
- Escalation rule stands: sonnet stuck twice → re-dispatch opus.
- Each phase ends by updating PROGRESS.md, RELEASE_CHECKLIST-style gate vs the
  PRD §11 post-MVP criteria, tag, push.
