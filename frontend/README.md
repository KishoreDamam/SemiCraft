This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

## Mock mode vs. real backend

The single API client (`lib/api.ts`) has two modes, selected by the
`NEXT_PUBLIC_API_BASE` env var (see `.env.example`):

- **Unset (default):** all data is served from the local mock layer (`mocks/`).
  `npm run dev` works standalone — no backend needed.
- **Set:** calls hit the real FastAPI backend at `${NEXT_PUBLIC_API_BASE}/api/v1/...`
  (the frozen §4 contract in `docs/IMPLEMENTATION_PLAN.md`).

### Two-terminal dev flow (frontend against the real backend)

Run the backend and the frontend in separate terminals.

**Terminal 1 — backend** (from the repo root `SemiCraft/`):

```bash
uv run uvicorn api.main:app --port 8000 --app-dir backend
```

Verify it's up: `curl http://localhost:8000/api/v1/snippets` should return 10 snippets.
(CORS is preconfigured for `http://localhost:3000`.)

**Terminal 2 — frontend** (from `frontend/`):

```bash
# point the client at the running backend
echo 'NEXT_PUBLIC_API_BASE=http://localhost:8000' > .env.local
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

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
