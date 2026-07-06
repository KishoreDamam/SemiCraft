# SemiCraft Progress Tracker

Updated: 2026-07-04. Keep current — this file is the session-handoff state.

## WP status

| WP | Status | Notes |
|---|---|---|
| WP-00 scaffold | DONE, committed d14c4c1, pushed | ruff/pytest/frontend build green |
| WP-09 docs draft | DONE-verified, wave 6 | STYLE_GUIDE checked line-by-line against golden output (counter/register/demux/mux/fsm goldens); divergences fixed (§3 comb example, §4/§9 worked examples, §7 param-doc claim); unsized-const rule and header-format section added; draft flag removed |
| WP-01 IR core | DONE, committed 4ad7b03, pushed | 29 tests. Spec decisions codified in IR_SPEC: Param names UPPER_SNAKE_CASE; Instance params/conns as sorted tuples with .params_dict/.conns_dict; comment level 'none' is filter-only |
| WP-02 renderers | DONE, committed, pushed | 37 render tests (66 total). §9 byte-identical; all 8 reset idioms match STYLE_GUIDE §2.1–2.8 (confirmed at WP-09 verify, wave 6). render() validates IR first. Shared walker in base.py; sv/verilog are keyword hooks only |
| WP-07 frontend mock-first | DONE, committed, pushed | 48 vitest tests, lint clean. Full UI vs mocks: schema-driven form (lib/schema.ts = core IP), Monaco preview, lint badge, permalink, copy/download. Real-API integration: set NEXT_PUBLIC_API_BASE once WP-06 lands. Monaco lacks a systemverilog language id — both HDLs use the verilog grammar |
| WP-03 framework+counter | DONE, committed b7ccab0, pushed | 42 tests; SnippetDef protocol; generate() entry point |
| WP-04 lint + WP-06 API | DONE (checkpoint b2877a1, pushed) | Wave-5 agents cut by session limit but work survived; API smoke-verified contract-exact (422 loc shape correct) |
| WP-05 snippets | DONE all 10, committed 2c7b2a7, pushed | 864 tests total. Gap-fill wave fixed two generator crashes (demux Case default, shift-register serial_out_only undeclared q). Golden snapshots regenerated for all snippets |
| WP-08 golden infra | DONE at b2877a1 | counter+register snapshots committed; --update-golden pytest flag |
| WP-10 release | DONE — v0.1.0 tagged | docs/RELEASE_CHECKLIST.md: all 8 PRD §11 MVP criteria PASS; stock frontend AGENTS.md/CLAUDE.md removed |

## Environment facts

- Git: origin = https://github.com/KishoreDamam/SemiCraft.git, branch main.
  Pushing completed WP work is authorized. Direct-to-main is the flow (no PRs
  requested).
- Windows host: no Docker, no Verilator locally. WP-04's `unavailable` path
  matters; real lint runs in CI (workflow already has lint-gate job, dormant).
- uv env at .venv works: `uv run pytest`, `uv run ruff check .`.
- User's VLSI Agent Kit: D:\Projects\VLSI-agkit (see plan §6b + CLAUDE.md).

## Open items

- IR gap (decide at WP-05i): SV state signals render `logic [N-1:0]`, not the
  enum type — DataType has no enum-type reference. Legal SV; add typed-signal
  support only if FSM snippet wants it (IR change, needs decision).

- (resolved at WP-10) stock frontend AGENTS.md/CLAUDE.md removed; --timing
  not passed to Verilator (decision recorded in lint/verilator.py); 422
  envelope verified FastAPI-standard against real capture
  (frontend/tests/fixtures/real-422-counter.json).

## Phase 2 (started 2026-07-06)

| WP | Status | Notes |
|---|---|---|
| P2-01 decisions | DONE, committed 745b89e, pushed | IR_SPEC §10 (GenFor/Memory/enum_type, rules 8-11); plan Appendix A (API v2, taxonomy, ModuleDef/TbSpec) |
| P2-02 IR v0.2 | IN FLIGHT (opus, background) | owns ir/ + tests/ir/test_v02_*. Recovery: check uncommitted ir/ changes, verify ruff+pytest (existing 864 must stay green), commit "P2-02: ..." |
| P2-04 ModuleDef | IN FLIGHT (opus, background) | owns snippets/contract+registry+generate.py extensions, new modules/ pkg (edge_detector reference), tests/modules/. Recovery: same pattern; after both land run `uv run pytest backend/tests/golden --update-golden` for edge-detector snapshots |
| P2-03 renderers | NEXT (opus + extra review pass) | after P2-02 |
| P2-05..15 | queued per plan | 2-agent budget per session (user constraint) |
