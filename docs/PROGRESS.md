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
| P2-02 IR v0.2 | DONE, committed, pushed | 34 tests; rules 8-11; genvar cross-loop reuse forbidden |
| P2-04 ModuleDef | DONE, committed e1c0f68, pushed | 55 tests + 23 goldens; registry-side kind/maturity defaulting; generate_files() rtl+doc; edge-detector reference module; 999 total green |
| P2-03 renderers | DONE, committed a4c528d, pushed | 25 golden tests; explicit generate/endgenerate both languages; fixed 2 latent GenFor-scope bugs (reset naming, reg/wire inference) |
| P2-05a API v2 backend | DONE, committed e45f455, pushed | 14 tests; catalog+generate+deterministic zip; v1 regression-guarded |
| P2-05b frontend v2 UI | DONE, committed 53a35c1, pushed | full v2 migration single path; CatalogPicker kind groups + beta badges; FileTabs; zip download; 163 frontend tests |
| P2-06/07/08 debouncer+clock-divider+pwm | DONE, committed, pushed | 99 tests, 36 golden cases, snapshots generated; 1267 backend total |
| P2-10 rr-arbiter | DONE, committed, pushed | 38 tests; two-pass mask scheme, sim-verified fairness |
| P2-11/12 lfsr+gray-counter | DONE, committed, pushed | 85 tests; bit-sim-honest tb_specs; 1544 total green. All 7 planned modules now in catalog |
| P2-13 smoke-TB generator | DONE, committed 0c002b0, pushed | agent cut at limit ~95% done; orchestrator finished inline (wiring, EMIT_TB flip, tests/tb/, TB_SPEC.md). Name-map-consistent SV TBs for all 7 modules |
| P2-14 golden TB + CI gate | DONE, committed b64cf5f, pushed | tb+doc snapshots per case (<case>.sv_tb.sv / .sv.md); verilator --binary compile gate in CI. 2282 tests green |
| P2-15 release v0.2.0 | DONE — CI green on b2bf088 (all gates incl. enforcing lint + TB compile), v0.2.0 tagged | Phase 2 COMPLETE. Next: Phase 3 per PLAN-semicraft-phases-2-8.md (P3-01 TB node family first) |
| P2-05..15 | queued per plan | 2-agent budget per session (user constraint) |

## Phase 3 (started 2026-07-11)

| WP | Status | Notes |
|---|---|---|
| P3-01 TB node family | DONE, committed b16cffd, pushed | 70 tests; full family + validate_tb T1-T8; goldens byte-identical; TB_SPEC v2 |
| P3-03a sim runner + run gate | DONE, committed 1adb9cf, pushed | 10 mocked tests; advisory run gate in CI — CHECK ITS LOG for tb_spec value failures (follow-up WP) |
| run-gate first execution | DONE — 12/14 cold pass; clock-divider check-timing bug fixed (71a4c01); gate now ENFORCING | timing model recorded in clock_divider.py: at TB cycle c, c-1 post-reset edges elapsed |
| P3-02 TB renderers | DONE, committed d76efc0, pushed | render_tb renders full node family (fork/join, tasks, timeout, dump, AssertProperty, ResetSeq); P2 goldens byte-identical; generate_tb did NOT adopt ResetSeq (byte-identity unproven, TB_SPEC §3.2); new tb/scripts.py run.sh/Makefile emitter; TB_SPEC v2.1. Agent cut at limit ~99% done, orchestrator verified inline |
| P3-05 SVA assertion generator | DONE, committed 3edc147, pushed | standalone semicraft_core/assertions: AssertionSpec -> AssertProperty tuple; families: reset-known-value, stability, handshake, onehot/onehot0, value-range, no-X; docs/ASSERTIONS.md; NOT wired into generate_files yet (later WP). 2413 backend tests green |
| P3-03 sim sandbox service | DONE, committed b25e693, pushed | POST /api/v2/simulate over run_smoke; status pass/fail/unavailable/no_tb/error; degrades to "unavailable" HTTP 200 (no Verilator locally); frontend Run button + SimPanel log viewer. 15 backend + 9 frontend tests; v2 additive |
| P3-04 directed-TB generator | DONE, committed dae8057, pushed | per-port width/PortConstraint clamping (no-op → drives byte-identical); TimeoutGuard watchdog forked atop stimulus initial (budget (reset_cycles+n_cycles+16)*8, never fires on pass); expected values still only from TbSpec.checks; ResetSeq NOT adopted; inert assertion_spec hook (no SVA for current modules). All 165 TB goldens regenerated (watchdog-only diff, 0 RTL/doc change). 2456 tests green |
| CI run-gate watch | PENDING push CI | watchdog is fork/join_none under verilator --binary — run gate confirms all 165 defaults still exit 0 + SMOKE PASS. Verify CI green before declaring P3-04 closed |
| Next | P3-06 checker/monitor/scoreboard scaffolds (sonnet) + P3-07 test-plan doc gen (sonnet, dep P3-04) OR P3-08 cocotb beta (dep P3-03); then P3-09 golden+CI release v0.3.0 | 2-agent budget per session |
