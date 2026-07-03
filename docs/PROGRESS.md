# SemiCraft Progress Tracker

Updated: 2026-07-04. Keep current — this file is the session-handoff state.

## WP status

| WP | Status | Notes |
|---|---|---|
| WP-00 scaffold | DONE, committed d14c4c1, pushed | ruff/pytest/frontend build green |
| WP-09 docs draft | DONE, committed cb458a1, pushed | STYLE_GUIDE draft-flagged; async+active-high reset examples are EXTRAPOLATED — verify against WP-02 renderer output, then remove draft flag (final verify = wave 6) |
| WP-01 IR core | DONE, committed 4ad7b03, pushed | 29 tests. Spec decisions codified in IR_SPEC: Param names UPPER_SNAKE_CASE; Instance params/conns as sorted tuples with .params_dict/.conns_dict; comment level 'none' is filter-only |
| WP-02 renderers | IN FLIGHT (fable sub-agent, background) | If session ended before it finished: check for uncommitted files under backend/semicraft_core/render/ + backend/tests/render/. Verify (ruff+pytest), check §9 golden match, compare async/active-high output vs STYLE_GUIDE §2.5/2.6, commit as "WP-02: ...". If absent/incomplete, re-dispatch per plan §5 WP-02 + §7 template (model: fable, or opus if unavailable) |
| WP-07 frontend mock-first | IN FLIGHT (opus sub-agent, background) | Same procedure: check frontend/ for new app code (dynamic form renderer, mocks/, lib/api.ts, vitest). Verify npm build/test/lint, commit as "WP-07: mock-first UI". Integration with real API waits for WP-06 |
| WP-03 framework+counter | NEXT after WP-02 | opus; dispatch prompt must include VLSI-agkit clean-rtl + systemverilog-patterns paths (plan §6b) |
| WP-04 lint / WP-05a–i / WP-06 / WP-08 | Wave 5 after WP-03 | up to 12 parallel; models per plan §5/§6 |
| WP-10 release | last | |

## Environment facts

- Git: origin = https://github.com/KishoreDamam/SemiCraft.git, branch main.
  Pushing completed WP work is authorized. Direct-to-main is the flow (no PRs
  requested).
- Windows host: no Docker, no Verilator locally. WP-04's `unavailable` path
  matters; real lint runs in CI (workflow already has lint-gate job, dormant).
- uv env at .venv works: `uv run pytest`, `uv run ruff check .`.
- User's VLSI Agent Kit: D:\Projects\VLSI-agkit (see plan §6b + CLAUDE.md).

## Open items

- STYLE_GUIDE draft flag removal after WP-02 verification (wave 6).
- create-next-app scaffolded frontend/AGENTS.md + frontend/CLAUDE.md (stock) —
  harmless, review/remove at WP-10.
- Verilator flag check at WP-04: prompt says `--lint-only -Wall --timing`;
  verify `--timing` behaves on pure-synthesizable code with the CI Verilator
  version (Ubuntu apt); drop if it errors.
