# SemiCraft — v1 Launch Readiness Review

Reviewed: 2026-09-08, at `6ab155e` (branch `claude/continue-previous-p5qub7`,
one commit ahead of `main`). Phase 4 is complete and merged; **Phase 5 is not
being started** — this launch ships the product as it stands at the end of
Phase 4.

Launch shape, as decided: **repository release now, hosted deployment later.**
Everything below is scoped to that. Blockers that belong only to hosting are
recorded in §5 as deferrals, not fixed.

This document is the review and the plan. **Nothing in §4–§6 has been
executed** — the work packages in §7 are proposed, not started.

---

## 1. What was verified, and how

Claims in `PROGRESS.md` were re-run rather than trusted:

| Check | Command | Result |
|---|---|---|
| Backend lint | `uv run ruff check .` | **PASS** — all checks passed |
| Frontend build | `npm run build` | **PASS** — 4/4 static pages |
| Frontend tests | `npm test` | **PASS** — 172 passed, 12 files, 6.2s |
| Frontend lint | `npm run lint` | **PASS** — eslint clean |
| Catalog size | `registry.by_kind(...)` | 10 snippets, 7 modules, **9 IPs** = 26 |
| End-to-end generation | `generate_files("axil-uart", {})` | **7 files, 1595 lines**, `config_hash 596505f8263a` |
| Toolchain | `verilator --version` | 5.020 (matches CI) |
| API surface | `app.openapi()` | 7 routes; Swagger UI live at `/docs` |
| Backend suite | `uv run pytest` | in progress at time of writing; last full run 6002 passed / 415 skipped |

The generated output was read, not just counted. It is good: the UART
datasheet opens with a real description, groups ports by function, documents
every register field with reset values and access types, and states its own
limitations. This is a substantial product.

## 2. Verdict

**The engineering is launch-ready. The packaging is not.**

Nothing in the generator, the verification stack, or the test discipline is
holding this release back. What is holding it back is everything a stranger
touches first: there is no license, the front door describes a product four
releases smaller than the one that exists, and the default frontend
configuration serves fabricated data with no warning.

None of the four blockers in §4 is hard. None is more than a day. But each of
them is the kind of defect that is invisible from inside the project and
immediate from outside it — which is the same shape as every bug this project
has spent four phases finding.

## 3. What is genuinely ready

Recorded so the fix list below is not mistaken for the whole picture.

- **26 catalog items**, all generating both SystemVerilog and Verilog-2001,
  every one `-Wall` clean with zero warnings.
- **Seven artifacts per IP** — RTL, datasheet, SV testbench, cocotb
  testbench, bound check scaffold, example instantiation, test plan.
- **Every run gate has a mutation half.** Deliberately broken generators that
  must fail. This is the single strongest thing about the project and it
  should be said out loud in the launch material — most generators cannot
  demonstrate that their tests can fail.
- **Determinism is real and proven**: identical options give byte-identical
  output, config hashes are stable across two releases (588 hashes unchanged
  through the v0.4.0 banner bump), and zip entries carry a fixed timestamp so
  even the archive bytes match.
- **Timing diagrams are rendered from the executed testbench**, so a diagram
  cannot be wrong while CI is green.
- **The API degrades honestly** — no Verilator gives `status: "unavailable"`
  and HTTP 200, never a 500.
- Request bodies are capped at 64 KB; lint, compile and run each carry their
  own subprocess timeout (10s / 90s / 30s).

## 4. Launch blockers

Ordered by how badly each one hurts a first-time visitor.

### B1 — There is no LICENSE file

`README.md` says SemiCraft "is licensed separately (see repository license,
**if/when added**)". It was never added. A public repository with no license
grants no rights: nobody may legally use, fork, redistribute, or contribute,
and no company will let an engineer near it.

The distinction the project already draws correctly must survive the fix:
generated **output** carries its own terms, stamped into every file header
from `semicraft_core/license.py` ("free for commercial and non-commercial use
at the user's own risk"). The **repository** is a separate question and
currently has no answer.

Needs a decision, then a file. Apache-2.0 is the recommendation over MIT: it
carries an explicit patent grant, which matters more than usual for a tool
whose output goes into silicon, and corporate legal review waves it through.

### B2 — The README describes a product four phases out of date

The front door still opens "## MVP: RTL Snippet Generator", presents the ten
snippet categories as **the** supported set, describes the feature list as
snippet preview plus download, and lists "full simulation" among the things
explicitly not in scope.

The product today has 26 catalog items, generates testbenches in two
frameworks, binds verification scaffolds into every IP, emits datasheets, test
plans, timing diagrams and lint-gated example instantiations, and ships a
working `POST /api/v2/simulate`. Modules, IPs and the entire verification
stack — three phases of work — appear in the README only as future roadmap
bullets. A reader who trusts it will conclude SemiCraft is a boilerplate
snippet toy and leave.

### B3 — Mock mode is the default, and the mock catalog is stale

`frontend/lib/api.ts`:

```ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE;
// isMock() === !API_BASE
```

With that variable unset — the default — the app serves `mocks/catalog.ts`,
which holds **11 items** (ten snippets plus `edge-detector`) against the real
26. No IPs at all, so the "IP Blocks" group the picker renders is empty.

A deployment that forgets one environment variable therefore ships a
convincing fake of a four-phase-old product: no error, no banner, no
indication whatsoever that the data is invented. And `frontend/README.md`
directs the reader to "see `.env.example`" — **that file does not exist.**

Three fixes, all small: ship the `.env.example`, make mock mode announce
itself unmistakably in the UI, and regenerate the mock catalog from the live
backend so that even the fallback is honest.

### B4 — CORS is hardcoded, and the backend has no configuration at all

```python
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], ...)
```

A grep for `environ`/`getenv` across `backend/api/` and
`backend/semicraft_core/` returns exactly one hit, and it is a comment in
`tb/scripts.py` about deliberately *not* probing the environment.

So a self-hoster running the frontend anywhere other than
`http://localhost:3000` gets silently browser-blocked API calls and no
diagnostic. The product does not run outside one hardcoded origin. This is a
blocker for the self-hosted release and becomes a hosting blocker later.

Needs a small, explicit configuration surface — allowed origins at minimum —
documented in one place.

## 5. Should fix before tagging

### S1 — Two releases are untagged, and the version number contradicts the launch

`v0.3.0` and `v0.4.0` were both prepared and neither was tagged (this
session's credentials return HTTP 403 on tag refs; recommended commits are
recorded in `PROGRESS.md`). Separately: shipping "our first product launch" as
**v0.4.0** tells users the opposite of what the launch says. Decide whether
this is **v1.0.0**.

The rename is cheap and pre-proven: `VERSION` + `pyproject.toml` +
a `RELEASE_CHECKLIST.md` heading, tied together by
`tests/release/test_version_consistency.py`, then a golden regeneration that
has twice produced a banner-only diff with every config hash unchanged.

### S2 — There is no way to *deploy* the product

There is a backend `Dockerfile`. There is no frontend image, no compose file,
and no single command that brings up the pair. The two-terminal flow in
`frontend/README.md` is a development loop, not a deployment. For a
self-hosted release this is the whole difference between "clone and run" and
"read three documents and guess".

### S3 — Seven of nine IPs are badged `beta`, and `beta` is undefined

`axil-*` are `beta`; `sync-fifo` and `sync-ram` are `stable`; the seven
modules are `stable`; snippets carry no maturity attribute at all. The badge
is shown to users and its meaning is written down nowhere.

Either define the levels in user-facing terms, or promote what the evidence
supports — every AXI IP has a Verilator run gate with a mutation half that
must fail, which is stronger evidence than most hand-written RTL ships with.
Leaving the flagship Phase-4 deliverable badged `beta` with no definition
undersells it and explains nothing.

### S4 — The AXI port table says nothing

Seventeen of an AXI IP's ports are documented as "AXI4-Lite signal; see the
register block's datasheet." That is the most-read table in the datasheet the
product is being sold on. A cheap fix in `ips/bundles.py`.

### S5 — The timing diagrams are invisible in the UI

`CodePreview.tsx` renders every `doc` file as raw markdown in Monaco, so
P4-10's headline feature reaches the user as a JSON blob inside a fenced code
block. The generated markdown is correct; the viewer simply does not render
it. Either render markdown (with a WaveDrom pass) in the doc tab, or say
plainly in the docs that datasheets are meant to be read outside the app.

### S6 — No CHANGELOG, SECURITY.md, or CONTRIBUTING.md

`RELEASE_CHECKLIST.md` is excellent evidence and a poor changelog — it is
organised as per-release criteria tables, not as "what changed for you".

### S7 — Two locked PRD decisions no longer match the build

- **§15 "Jinja2 templates"** — the engine is an IR plus renderers. There is no
  Jinja2 anywhere. The implementation is better; the PRD is stale.
- **§15 "adopt an IP-XACT-aligned JSON subset *from the start* to avoid
  migration pain in Phase 6"** — nine IPs have now shipped with a Python
  register-map model and no IP-XACT export, and IP-XACT is deferred to P6-01.
  This is precisely the debt that decision existed to prevent.

Both should be reconciled *explicitly* in the PRD. The house rule is that
frozen decisions change by recorded decision, never by drift — and this is
drift.

### S8 — One frozen contract is now blocking three separate features

`GeneratedFile.kind` is a frozen `Literal["rtl","tb","doc"]`. It has
independently blocked:

1. the ROM's `$readmemh` init file (P4-04b),
2. a standalone WaveDrom `.json` (P4-10, worked around by inlining),
3. an IP-XACT JSON export (S7).

Three blockers from one contract is the point at which the decision gets
scheduled rather than routed around again.

## 6. Deferred on purpose — for the release notes, not the fix list

Already recorded in the v0.4.0 checklist and correct as-is: the async FIFO
(needs a two-clock testbench), the ROM (needs memory initialisation in the
IR), the unattached scoreboard family, cocotb still beta and not wired into
`POST /api/v2/simulate`, and `bind` being SystemVerilog-only.

**Sim-sandbox hardening belongs to the hosting phase, not this one.** Worth
recording the actual exposure so it is not overstated or forgotten: the input
is option-driven and pydantic-validated, so a user **cannot inject arbitrary
HDL** — the risk is CPU exhaustion, not arbitrary code execution. Per-request
timeouts exist; a concurrency cap, a rate limit and process resource limits do
not. That combination is fine for a self-hosted tool where the operator is the
user, and must be closed before a public URL exists.

## 7. Release documentation plan

Twelve work packages. Sizes: S ≈ half a day, M ≈ a day, L ≈ two.

The last column is the part that matters for this project. SemiCraft has spent
four phases finding artifacts that exist, pass their own tests, and verify
nothing — the checker generators that shipped unattached for a phase, the
integration test that had never run in CI, the datasheet port table that was
wrong for four releases. **Documentation is the easiest place in a repository
for that to happen again**, so every package below carries a gate that fails
when the document drifts from the code.

| WP | Deliverable | Size | Anti-rot gate |
|---|---|---|---|
| **R-01** | `LICENSE` + rewritten legal section; output-vs-repository boundary stated once, precisely | S | test: `LICENSE` exists and the README's SPDX id matches it |
| **R-02** | `README.md` rewrite — the real product, its evidence, and an honest scope | M | test: catalog counts quoted in the README equal `registry.by_kind()` |
| **R-03** | `docs/GETTING_STARTED.md` — install, run, first generation, in that order | S | the commands are executed by CI, not just printed |
| **R-04** | `docs/USER_GUIDE.md` — the option model, the seven files and what each is *for*, lint badge, Run, permalinks, naming styles | L | test: every option named in the guide exists in the JSON schema |
| **R-05** | `examples/` — a curated tree of real generated output, one per family | M | test: every file is byte-identical to freshly generated output |
| **R-06** | `docs/CATALOG.md` — all 26 items in one table, plus **maturity levels defined** (closes S3) | M | test: the table's rows equal the registry, ids and maturity both |
| **R-07** | `docs/INTEGRATION.md` — dropping the output into a real flow: filelists, Verilator/Questa/Vivado, running the cocotb TB, reusing the `bind` scaffold | M | the filelist snippets compile in CI |
| **R-08** | `docs/DEPLOYMENT.md` + frontend image + `docker compose` (closes S2, needs B4) | M | CI brings the stack up and hits `/healthz` and one real generate |
| **R-09** | `docs/API.md` — mostly *linking*: Swagger UI and `/openapi.json` already exist. Add response examples and the error envelopes | S | contract tests already exist; assert the documented routes equal `app.openapi()` |
| **R-10** | `CHANGELOG.md` + v1.0.0 release notes, incl. §6 verbatim as known limitations | S | test: the newest heading matches `VERSION` (extend the existing consistency test) |
| **R-11** | `SECURITY.md`, `CONTRIBUTING.md`, issue/PR templates | S | none needed |
| **R-12** | PRD reconciliation (S7) + the version decision (S1) | S | the existing version-consistency test covers the rename |

### Notes on the two that are easy to get wrong

**R-05, the examples.** The obvious shortcut is to publish
`backend/tests/golden/` — 2050 files, 14 MB. Don't: those are snapshot
fixtures organised for the harness, and a reader drowns. The examples tree
should be a **script-generated, CI-verified** handful — one snippet, one
module, one simple IP, one AXI IP with its full seven-file set — so a visitor
can read real output, with its datasheet and its testbench, without installing
anything. Because it is generated, the freshness test is one line and the tree
can never drift.

**R-04, the user guide.** The single most valuable page in it is not the
option reference. It is *"you asked for one IP and got seven files — here is
what each is for and which ones you actually need."* Nothing in the product
explains that today, and it is the first question every user will have.

### Suggested order

1. **B1, B2, B3, B4** — the blockers. Nothing else matters until a stranger
   can legally and accurately see what this is.
2. **R-01, R-02, R-03, R-05** — license, front door, first run, something real
   to look at. This is the minimum coherent launch.
3. **R-06, R-04, R-09** — catalog and depth for the users the front door
   brings in.
4. **R-10, R-11, R-12, S1** — changelog, community files, PRD reconciliation,
   version decision. Then tag.
5. **R-07, R-08** — integration and deployment. Both are real work and neither
   blocks a repository release.

`S4`, `S5` and `S8` are product work rather than release documentation and
should be scheduled alongside, not inside, the above.
