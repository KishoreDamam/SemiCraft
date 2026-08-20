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

---

# SemiCraft v0.2.0 — Phase 2 Release

Verified 2026-07-11 against the Phase 2 exit criteria
(docs/PLAN-semicraft-phases-2-8.md).

| Criterion | Status | Evidence |
|---|---|---|
| 7 modules, both languages | PASS | edge-detector, debouncer, clock-divider, pwm, rr-arbiter, lfsr, gray-counter |
| Each module ships a smoke TB compiling under Verilator in CI | PASS | tb-compile gate green on b2bf088 (verilator --timing --binary per golden TB) |
| Golden-locked | PASS | rtl + tb + doc snapshots per case, byte-exact, determinism-checked |
| Catalog-filterable | PASS | kind/maturity taxonomy; /api/v2/catalog; UI groups Snippets/Modules |
| Zip-downloadable | PASS | /api/v2/generate/zip, byte-deterministic archives |
| Lint-clean guarantee upgraded | PASS | golden lint gate now enforcing (continue-on-error removed); all RTL passes verilator --lint-only -Wall |

Phase 2 additions: IR v0.2 (GenFor, Memory, enum-typed DataType, validation
rules 8–11), API v2 multi-file contract, ModuleDef/TbSpec contracts, TB stub
node family (docs/TB_SPEC.md), schema-driven multi-file frontend (file tabs,
zip download, maturity badges).

Quality notes: the enforcing lint gate exposed and fixed four generator bug
classes (unused parameters, parameter-default width mismatches, incomplete
case coverage, unread LSB in LFSR serial mode); TB idle-cycle coalescing
fixed a 65k-line pathological testbench.

Test counts at tag: 2282 backend + 163 frontend, CI green end to end.

---

# SemiCraft v0.3.0 — Phase 3 Release

Phase 3 goal (plan): "verification as product" — directed TBs, assertions,
checkers, monitors, scoreboards, sim scripts, real simulation runs.
PRD exit criterion: *generated testbenches run against at least one supported
module family.*

| Criterion | Status | Evidence |
|---|---|---|
| Generated TBs **run** (not just compile) green | PASS | full 165-case matrix green: `SEMICRAFT_TB_RUN_ALL=1 pytest backend/tests/golden/test_tb_run.py` |
| Directed TB generator from module metadata | PASS | P3-04: per-port width/`PortConstraint` clamping, timeout watchdog, expected values from `TbSpec.checks` |
| Full TB IR node family + validator | PASS | P3-01/P3-02: fork/join, loops, conditionals, tasks, timeout, dump, SVA property; `validate_tb` rules T1–T8 |
| Concurrent SVA generated and running | PASS | P3-05a/b: 6 of 7 modules carry a `TbSpec.assertion_spec`; assertions run live in every golden TB for those modules |
| Sim sandbox + results surfaced in UI | PASS | P3-03: `POST /api/v2/simulate`; frontend Run button + `SimPanel` log viewer; degrades to `unavailable` (HTTP 200) without Verilator |
| Sim-script emitter | PASS | P3-02: deterministic `run.sh` / `Makefile` mirroring the runner's Verilator flow |
| Test-plan document per module | PASS | P3-07: `<module>_testplan.md`, golden-locked, derived from `ExplanationDoc`/`port_groups`/`tb_spec` |
| Checker/monitor/scoreboard generators | PASS (generators), NOT WIRED (by decision) | P3-06 + P3-06a: compile-gated in CI. No module attaches one — see "Deliberate gaps" |
| Regression gates | PASS | per-push: ruff, pytest, Verilator lint gate, TB compile gate, TB run gate (defaults). Nightly: full 165-case run matrix (`.github/workflows/tb-matrix.yml`) |

## Deliberate gaps at this release

These are decisions with recorded reasons, not oversights. Each is documented
where a reader will hit it.

- **Checkers/monitors/scoreboards generate but no module attaches one.** For the
  current catalog, `ResetValueCheck`/`StabilityCheck` are (per their own
  docstrings) procedural analogues of SVA families already wired in P3-05b, so
  attaching them would emit a second, weaker copy of checks that already run.
  `LatencyCheck` has no SVA counterpart, but its only candidate module
  (rr-arbiter) asserts a combinational grant in the same cycle as the request,
  which the checker's arm-then-look-next-edge state machine reports as a
  spurious failure. Their payoff is Phase 4's IP blocks (real valid/ready
  handshakes and transactions) — see `docs/PROGRESS.md`, "Checker wiring".
- **pwm carries no assertions.** Only its counter is reset; `pwm_out` is
  combinational from it, so there is no reset value true of every
  configuration. A property that merely usually holds is worse than none.
- **edge-detector's `registered_output=False` cases carry no assertions**, for
  the same reason: `pulse` is a continuous assign with no reset value.
- **cocotb backend (P3-08) is beta.** Landed after the first cut of this
  section: every module now also emits `test_<module>.py`, and all 7 run green
  under Verilator (`backend/tests/tb/test_cocotb_run.py`). It is beta because
  the SV backend remains the default, carries the exhaustive option matrix, and
  is the only one wired into `POST /api/v2/simulate`; the cocotb path also
  emits no SVA, since assertions are a SystemVerilog construct. Pinned to cocotb
  1.9.2 — cocotb 2.x cannot build against Verilator 5.020. See `docs/COCOTB.md`.
- **Phase 3's planned module family** in the plan text named
  "counter+register+fifo-lite". No fifo-lite module exists (FIFO is a Phase 4
  IP). The exit criterion is met against the seven Phase-2 modules instead,
  which is a superset in module count if not the exact named list.
- **`ResetSeq` still not adopted by `generate_tb`** — reset stays inline
  (TB_SPEC §3.2); the node exists for hand-built TBs.

## Defects found and fixed during Phase 3

Recorded because they were all invisible to the tests that existed at the time:

- **TB reset-deassertion race** (P3-09a): the deassert shared a timestep with the
  rising edge ending the reset hold, so a sync-reset DUT could take a state
  update on an edge the TB counted as "in reset". 17 of 165 golden TBs failed.
  Masked in any configuration gated by an enable, so only free-running configs
  broke. Now normative — TB_SPEC §6a.
- **Expected values fitted to that racy sim**: clock-divider's toggle checks were
  annotated "Observed sim timing" and encoded the bug as ground truth. Re-derived
  from the RTL and probe-verified.
- **lfsr serial model contradicted its RTL**: predicted the feedback bit while the
  RTL drove `q[0]`; the port comment shipped to users was wrong in four places.
- **Assertion specs were never restyled** (P3-05a): module specs are canonical, so
  an active-low reset — the default — emitted `disable iff (!rst)` against a net
  rendered `rst_n`. The feature would have been broken out of the box.
- **Checker scaffolds had never been compiled** (P3-06a): the scoreboard-wrapper
  example, in both the golden fixture and the docs, referenced a signal it never
  declared.
- **Every generated testbench was uncompilable under any non-default naming
  style** (found at P4-01, fixed before this tag): `render_tb` held the clock net
  in a module-level `_CLOCK_NAME = "clk"` constant, so a prefix/suffix/camelCase
  style renamed the DUT clock to (say) `p_clk` while the stimulus and the
  watchdog still waited on `clk`. Affected all 7 modules in both languages, and
  shipped in v0.2.0. **No golden case sets a naming style**, so the 165-case
  matrix only ever exercised the one spelling the constant happened to match;
  the fix is byte-identical at the default style, which is exactly why nothing
  failed for two releases. Now normative — TB_SPEC §7a.
- **`VERSION` was never bumped for v0.2.0** — that release shipped stamping
  "SemiCraft v0.1.0" into every generated artifact. `VERSION` is not part of
  `config_hash`, so nothing detected it. Guarded now by
  `backend/tests/release/test_version_consistency.py`, which ties the constant to
  this checklist.

## Frontend at this release

| Check | Status | Evidence |
|---|---|---|
| Unit tests | PASS | 172 tests / 12 files (`npm test -- --run`) |
| Lint | PASS | `npm run lint` clean |
| Production build | PASS | `npm run build` — static prerender of `/` and `/_not-found` |
| Reproducible install | FIXED HERE | `npm ci` was **broken**: the lockfile was out of sync with `package.json` (missing `@emnapi/core` / `@emnapi/runtime`, a stale `@emnapi/wasi-threads` pin). Refreshed; `npm ci` now succeeds from a clean `node_modules`. Additive only — two optional wasm-shim transitive deps, nothing removed. |

**The frontend is not in CI.** `.github/workflows/ci.yml` runs ruff, pytest and
the Verilator lint/TB gates — there is no job that installs, tests, lints or
builds `frontend/`. That is why a broken lockfile survived unnoticed: nothing
automated has run `npm ci` since it drifted. Adding a frontend job is the
obvious follow-up; it is called out here rather than done silently because it
adds a new CI job and its runner cost is the owner's call.

## Environment note

Verilator installs and runs in Linux containers (`apt-get install -y verilator`,
5.020) and in CI. The "no Verilator locally" note in `CLAUDE.md` is a
Windows-host fact only; on a container both the compile and run gates can be
exercised before pushing.
