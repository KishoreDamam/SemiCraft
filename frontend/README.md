# SemiCraft frontend

Next.js (App Router, TypeScript) single-page generator UI: catalog picker and
dynamic options form on the left, Monaco preview with per-file tabs on the
right. See the repository [README](../README.md) for the product itself.

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Edit `app/page.tsx` and it
hot-reloads.

## Mock mode vs. real backend

The single API client (`lib/api.ts`) has two modes, selected by the
`NEXT_PUBLIC_API_BASE` env var (see `.env.example`):

- **Unset (default):** all data is served from the local mock layer
  (`mocks/`) — a small hand-written sample with fabricated output, not the real
  catalog. `npm run dev` works standalone, no backend needed, and the app shows
  a permanent banner (`components/MockBanner.tsx`) so demo data can never be
  mistaken for the real thing. **Do not deploy in this mode.**
- **Set:** calls hit the real FastAPI backend at `${NEXT_PUBLIC_API_BASE}/api/...`
  (the frozen contracts in `docs/IMPLEMENTATION_PLAN.md` §4 and
  `docs/PLAN-semicraft-phases-2-8.md` Appendix A.1).

### API version

The UI runs entirely on **API v2** (multi-file). One code path serves both
snippets and modules:

- `getCatalog()` → `GET /api/v2/catalog` — `items[]` carry `kind`
  (`snippet`/`module`/`ip`) and `maturity` (`stable`/`beta`); the picker groups
  them into Snippets / Modules / IP Blocks and badges non-stable items.
- `generateV2(item_id, options)` → `POST /api/v2/generate` — returns
  `files[]` (`{path, kind: rtl|tb|doc, text}`), a per-file `lint[]` list
  (rtl files only; the badge aggregates to the worst status), plus
  `explanation`, `config_hash`, `language`.
- `downloadZip(item_id, options)` → `POST /api/v2/generate/zip` — saves the
  archive, filename taken from `Content-Disposition`. Single-file results use a
  plain blob download of the active file instead.

The v1 client helpers (`fetchCatalog`, `generate`) remain in `lib/api.ts` for
the frozen §4 contract tests, but the app itself no longer calls them.

### Two-terminal dev flow (frontend against the real backend)

Run the backend and the frontend in separate terminals.

**Terminal 1 — backend** (from the repo root `SemiCraft/`):

```bash
uv run uvicorn api.main:app --port 8000 --app-dir backend
```

Verify it's up: `curl http://localhost:8000/api/v2/catalog` should return the
full catalog. CORS defaults to `http://localhost:3000`; serving this frontend
from any other origin means setting `SEMICRAFT_CORS_ORIGINS` in the backend's
environment, or the browser will block every call with no server-side error.

**Terminal 2 — frontend** (from `frontend/`):

```bash
# point the client at the running backend
cp .env.example .env.local
npm run dev
```

`NEXT_PUBLIC_*` vars are inlined at build/dev-server start, so restart
`npm run dev` after changing `.env.local`.

### Integration check

With the backend running on port 8000, exercise every snippet's generate
round-trip plus the 422/404 paths:

```bash
node ../scripts/integration-check.mjs   # from frontend/, or run from repo root without ../
```

The captured real fixtures used by the interpreter/422 tests live in
`tests/fixtures/` (`real-catalog.json`, `real-422-counter.json`); regenerate
them from a running backend if the contract changes.
