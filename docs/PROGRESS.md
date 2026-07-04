# SemiCraft Progress Tracker

Updated: 2026-07-04. Keep current — this file is the session-handoff state.

## WP status

| WP | Status | Notes |
|---|---|---|
| WP-00 scaffold | DONE, committed d14c4c1, pushed | ruff/pytest/frontend build green |
| WP-09 docs draft | DONE, committed cb458a1, pushed | STYLE_GUIDE draft-flagged; async+active-high reset examples are EXTRAPOLATED — verify against WP-02 renderer output, then remove draft flag (final verify = wave 6) |
| WP-01 IR core | DONE, committed 4ad7b03, pushed | 29 tests. Spec decisions codified in IR_SPEC: Param names UPPER_SNAKE_CASE; Instance params/conns as sorted tuples with .params_dict/.conns_dict; comment level 'none' is filter-only |
| WP-02 renderers | DONE, committed, pushed | 37 render tests (66 total). §9 byte-identical; all 8 reset idioms match STYLE_GUIDE §2.1–2.8 (draft flag can drop at WP-09 verify). render() validates IR first. Shared walker in base.py; sv/verilog are keyword hooks only |
| WP-07 frontend mock-first | DONE, committed, pushed | 48 vitest tests, lint clean. Full UI vs mocks: schema-driven form (lib/schema.ts = core IP), Monaco preview, lint badge, permalink, copy/download. Real-API integration: set NEXT_PUBLIC_API_BASE once WP-06 lands. Monaco lacks a systemverilog language id — both HDLs use the verilog grammar |
| WP-03 framework+counter | DONE, committed b7ccab0, pushed | 42 tests; SnippetDef protocol; generate() entry point |
| WP-04 lint + WP-06 API | DONE (checkpoint b2877a1, pushed) | Wave-5 agents cut by session limit but work survived; API smoke-verified contract-exact (422 loc shape correct) |
| WP-05 snippets | 7 of 10 done at b2877a1 (counter..shift-register); GAP-FILL IN FLIGHT | 4 agents running: (A) tests+cases for shift-register/mux/demux, (B) tests+cases encoder/decoder, (C) comparator+cdc-synchronizer full, (D) fsm full (opus). After all land: run `uv run pytest backend/tests/golden --update-golden` to create new snapshots, full verify, commit |
| WP-08 golden infra | DONE at b2877a1 | counter+register snapshots committed; --update-golden pytest flag |
| WP-10 release | after gap-fill + wave 6 (WP-07 API integration check, WP-09 verify) | |

## Environment facts

- Git: origin = https://github.com/KishoreDamam/SemiCraft.git, branch main.
  Pushing completed WP work is authorized. Direct-to-main is the flow (no PRs
  requested).
- Windows host: no Docker, no Verilator locally. WP-04's `unavailable` path
  matters; real lint runs in CI (workflow already has lint-gate job, dormant).
- uv env at .venv works: `uv run pytest`, `uv run ruff check .`.
- User's VLSI Agent Kit: D:\Projects\VLSI-agkit (see plan §6b + CLAUDE.md).

## Open items

- WP-02 flags for WP-09 style-guide verify: (a) §7 "parameter doc inline
  comments" wrong — renderer emits no param doc comments (IR_SPEC §9 wins);
  (b) document unsized-const rule: minimal-width binary literal in expression
  context (`1'b1`), plain number in size/param context; (c) IR_SPEC §7 table's
  `S_IDLE` is illustrative — enum members are lower_snake per §6 rule 1.
- IR gap (decide at WP-05i): SV state signals render `logic [N-1:0]`, not the
  enum type — DataType has no enum-type reference. Legal SV; add typed-signal
  support only if FSM snippet wants it (IR change, needs decision).

- STYLE_GUIDE draft flag removal after WP-02 verification (wave 6).
- create-next-app scaffolded frontend/AGENTS.md + frontend/CLAUDE.md (stock) —
  harmless, review/remove at WP-10.
- Verilator flag check at WP-04: prompt says `--lint-only -Wall --timing`;
  verify `--timing` behaves on pure-synthesizable code with the CI Verilator
  version (Ubuntu apt); drop if it errors.
- WP-06 dispatch MUST pin the 422 envelope to FastAPI's standard
  `{ detail: [{ loc: ["body","options","<field>"], msg, type }] }` — the
  frontend's field-error mapping (frontend/lib/api.ts fieldErrorsFrom)
  assumes it.
