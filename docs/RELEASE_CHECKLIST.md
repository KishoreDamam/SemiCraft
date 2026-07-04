# SemiCraft v0.1.0 — MVP Release Checklist

Verified 2026-07-04 against PRD §11 MVP release criteria.

| # | Criterion (PRD §11) | Status | Evidence |
|---|---|---|---|
| 1 | At least 8 RTL snippet categories | PASS (10) | counter, register, shift-register, mux, demux, encoder, decoder, comparator, cdc-synchronizer, fsm — `registry.all()` |
| 2 | Each snippet exposes structured configuration options | PASS | Pydantic options models per snippet; JSON Schema served by `GET /api/v1/snippets`; schema-driven form renders all 10 (frontend/tests/real-schemas.test.ts) |
| 3 | Verilog or SystemVerilog output per snippet | PASS | Both languages, golden snapshots per snippet × per case (backend/tests/golden/) |
| 4 | Output can be copied and downloaded | PASS | Copy button + blob download with server-provided filename (frontend/components/GeneratorApp.tsx) |
| 5 | Explanation and assumptions per snippet | PASS | ExplanationDoc fully populated for all 10; completeness asserted per snippet test suite |
| 6 | Generator regression tests per category | PASS | 864 backend tests: per-snippet suites + golden byte-exact snapshots + determinism checks |
| 7 | Invalid option combinations blocked or clearly reported | PASS | Pydantic model_validators; API 422 with field-level detail; frontend maps errors inline |
| 8 | No natural-language or AI generation flow | PASS | Option-driven only; no NL input anywhere in product |

## Success metrics (PRD §13, MVP)

- Snippet generation < 1 minute: PASS — live preview regenerates on 300 ms debounce.
- Deterministic output for same configuration: PASS — byte-identity tests in-process and cross-process; config_hash stable across option key order.
- Copy/download without manual formatting fixes: PASS — rendered output is final; lint-clean gate in CI.

## Known limitations at release

- Verilator lint runs in CI and Docker only; on hosts without the binary the
  API returns lint status "unavailable" (by design).
- FSM snippet generates a transition skeleton (TODO arms) — transitions are
  user-completed; documented in its explanation.
- Multi-bit CDC synchronizer emits a mandatory gray-code/quasi-static warning;
  it does not enforce it.
- Fragment mode lints the wrapped equivalent, not the fragment text itself.

## Deploy

- Backend + Verilator: `docker build -t semicraft . && docker run -p 8000:8000 semicraft`
- Frontend: `cd frontend && NEXT_PUBLIC_API_BASE=<backend-url> npm run build && npm start`
- Live smoke: `node scripts/integration-check.mjs` with backend running.

## CI at tag time

- CI (ruff + pytest + Verilator lint-gate) green at 2c7b2a7; wave-6 commit
  cc5e50d in progress at checklist time — confirm green before announcing.
