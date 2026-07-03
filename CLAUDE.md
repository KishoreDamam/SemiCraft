# SemiCraft — Claude Code Project Guide

Deterministic, option-driven RTL snippet generator (MVP). No AI in the product
itself. Python backend (`backend/`), Next.js frontend (`frontend/`).

## Normative documents (read before changing anything)

- [SemiCraft_PRD.md](SemiCraft_PRD.md) — product scope; §15 holds locked decisions.
- [docs/IR_SPEC.md](docs/IR_SPEC.md) — IR node catalog, validation rules, rendering table. Source of truth for generator code.
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) — work packages (WPs), frozen snippet/API contracts (§3–§4), model assignments, execution waves, sub-agent dispatch template (§7), VLSI-agkit skill mapping (§6b).
- [docs/PROGRESS.md](docs/PROGRESS.md) — live WP status + next actions. UPDATE THIS after every WP lands.

## Workflow rules

- Work is executed as WPs dispatched to sub-agents per IMPLEMENTATION_PLAN §5–§7
  (model per WP header; escalate sonnet→opus on repeated failure).
- Verify each finished WP: `uv run ruff check .` and `uv run pytest` from repo
  root must pass before committing.
- Commit per WP with message `WP-NN: <summary>`; push to origin main (user has
  authorized pushes of completed WP work).
- Interface changes to frozen contracts (IR_SPEC §3, plan §3–§4) require an
  explicit decision recorded in the spec doc, never a silent edit.
- Domain reference: user's VLSI Agent Kit at `D:\Projects\VLSI-agkit\.agent\skills\`
  — feed relevant SKILL.md paths to RTL-producing sub-agents (plan §6b).
  SemiCraft specs win on conflicts (e.g. no `i_`/`o_` prefixes by default).

## Commands

- Backend tests: `uv run pytest` (repo root; testpaths backend/tests)
- Lint: `uv run ruff check .`
- Frontend: `cd frontend && npm run build && npm test && npm run lint`
- Verilator unavailable on this Windows host — lint via Docker or CI only;
  `status: "unavailable"` path keeps the API usable locally.
