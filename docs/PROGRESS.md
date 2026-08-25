# SemiCraft Progress Tracker

Updated: 2026-08-20. Keep current — this file is the session-handoff state.

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
| run-gate first execution | DONE — 12/14 cold pass; clock-divider check-timing bug fixed (71a4c01); gate now ENFORCING | ~~timing model recorded in clock_divider.py: at TB cycle c, c-1 post-reset edges elapsed~~ **SUPERSEDED at P3-09a** — that `c-1` was reverse-engineered from a testbench with a reset-deassertion race, not real divider behavior. Correct model: at cycle c, exactly c post-reset edges. See "Full TB run matrix" below |
| P3-02 TB renderers | DONE, committed d76efc0, pushed | render_tb renders full node family (fork/join, tasks, timeout, dump, AssertProperty, ResetSeq); P2 goldens byte-identical; generate_tb did NOT adopt ResetSeq (byte-identity unproven, TB_SPEC §3.2); new tb/scripts.py run.sh/Makefile emitter; TB_SPEC v2.1. Agent cut at limit ~99% done, orchestrator verified inline |
| P3-05 SVA assertion generator | DONE, committed 3edc147, pushed | standalone semicraft_core/assertions: AssertionSpec -> AssertProperty tuple; families: reset-known-value, stability, handshake, onehot/onehot0, value-range, no-X; docs/ASSERTIONS.md; NOT wired into generate_files yet (later WP). 2413 backend tests green |
| P3-03 sim sandbox service | DONE, committed b25e693, pushed | POST /api/v2/simulate over run_smoke; status pass/fail/unavailable/no_tb/error; degrades to "unavailable" HTTP 200 (no Verilator locally); frontend Run button + SimPanel log viewer. 15 backend + 9 frontend tests; v2 additive |
| P3-04 directed-TB generator | DONE, committed dae8057, pushed | per-port width/PortConstraint clamping (no-op → drives byte-identical); TimeoutGuard watchdog forked atop stimulus initial (budget (reset_cycles+n_cycles+16)*8, never fires on pass); expected values still only from TbSpec.checks; ResetSeq NOT adopted; inert assertion_spec hook (no SVA for current modules). All 165 TB goldens regenerated (watchdog-only diff, 0 RTL/doc change). 2456 tests green |
| CI run-gate watch | DONE — CI GREEN on 482cd71 | first push (592000c) RED: all 165 TBs hit %Error-LIFETIME — watchdog `repeat` counter is automatic, may outlive join_none process under verilator --timing. Fixed (482cd71) with explicit `static int watchdog_i` for-loop (Verilator's own suggested fix); same posedge-count semantics. lint + tb-compile + tb-run all green |
| P3-06 checker scaffolds | DONE, committed 960894f | standalone semicraft_core/checkers: monitor (passive sampler) / checker (procedural reset+stability+latency checks) / scoreboard (SV class, expected queue, report()). Directed, not UVM. NOT wired into generate_files — no golden changes. docs/CHECKERS.md. Emitted SV is now COMPILE-VERIFIED (P3-06a): `tests/checkers/test_compile.py` runs all three families through `verilator --timing --lint-only` (11 tests, incl. a negative control so the gate can't rot into a no-op), wired into CI's lint-gate job. It caught a real defect on first run — the scoreboard-wrapper example in BOTH the golden fixture and docs/CHECKERS.md referenced `data` from push_expr/compare_expr without declaring it in `ScoreboardWrapper.ports`, emitting a module with an undeclared signal. Generator was correct; the examples were not. Both fixed |
| P3-07 test-plan doc gen | DONE, committed 596d81c | semicraft_core/testplan.py -> `<module>_testplan.md` as a SECOND doc-kind file appended after the datasheet (datasheet stays files[]'s first doc entry, so `next(f for f in files if f.kind=="doc")` still resolves to it). 165 testplan goldens; all pre-existing rtl/doc/tb goldens byte-identical. Gap list (undriven inputs / unchecked outputs) reports "None found" on all current modules — verified genuinely true, and the logic has synthetic tests proving it fires both ways. docs/TESTPLAN.md |
| P3-06a checker compile gate | DONE, committed b38ca85 | see P3-06 row: closes the "never compiled" gap that WP shipped with |
| P3-05a assertion restyle + first module | DONE, committed d9fc40c | `assertions/restyle.py`: module specs are written in CANONICAL names (`tb_spec(opts)` never sees the render style) and `generate_tb` now restyles them through the same name map as every other net. Without it an active-low reset — the DEFAULT — emitted `disable iff (!rst)` against a net rendered `rst_n`, i.e. the feature was broken out of the box. `when` antecedents stay opaque (renaming inside free text needs an SV parser); documented + asserted as a limitation |
| P3-05b remaining five modules | DONE, committed c6a8fff | clock-divider, debouncer, edge-detector, lfsr, rr-arbiter wired; every property derived from the RTL reset body and verified to HOLD in sim. rr-arbiter carries onehot0 on `grant` (its defining invariant). Deliberate exclusions, each pinned by a test: edge-detector `registered_output=False` (pulse is a continuous assign) and pwm entirely (only cnt is reset; pwm_out is combinational). Full matrix caught a width bug in this work: `pulse` is opts.width bits, not 1 — passed at default width, broke on wide configs |
| P3-09 release v0.3.0 | DONE (prep) — NOT TAGGED, see below | VERSION 0.1.0 -> 0.3.0 and pyproject 0.1.0 -> 0.3.0. **v0.2.0 shipped with VERSION=0.1.0**: every artifact it generated stamped `// SemiCraft v0.1.0`. Nothing caught it because VERSION is not part of config_hash, so no golden or hash moved. Guarded now by `backend/tests/release/test_version_consistency.py`, which ties VERSION + pyproject to the newest `# SemiCraft vX.Y.Z` heading in RELEASE_CHECKLIST.md (a file, so it works in a shallow clone / before the tag exists). All 876 goldens regenerated: banner-only diff, 149 config hashes byte-identical. RELEASE_CHECKLIST.md gains a v0.3.0 section incl. an explicit "Deliberate gaps" list |
| P3-06 wiring analysis | BLOCKED ON A DESIGN FINDING — see "Checker wiring" section below. Short version: for the *current* catalog the checker families duplicate the SVA wired in P3-05b, and the one non-duplicate family is fragile on its only candidate module. Recommend deferring to Phase 4 IPs | evidence recorded below |
| P3-08 cocotb beta | DONE | `tb/cocotb_tb.py` emits `test_<module>.py` as a SECOND tb-kind file (path-distinguished, NOT a widened GeneratedFile.kind — frozen contract + frontend `Record<FileKind,string>` build break). Same TbSpec, same name map, same reset settle (TB_SPEC §6a) as the SV backend; a test asserts both backends emit identical expected values. **Pinned cocotb==1.9.2**: cocotb 2.0.1's Verilator VPI shim calls `VerilatedVpi::doInertialPuts()`/`evalNeeded()`, absent from Verilator 5.020 (newest in apt) — verified by spike, it fails in make. All 7 modules RUN green (~70s); 165 goldens; docs/COCOTB.md | 45 unit + 7 run tests |
| Next | Phase 3 COMPLETE. Work moved to **Phase 4** — see its section below | 2-agent budget per session |

## Full TB run matrix — 17 pre-existing failures (found + fixed 2026-07-29)

**Verilator IS available in Linux remote containers** (`apt-get install -y
verilator` → 5.020). The "no Verilator locally" note under Environment facts
is a *Windows-host* fact only. In a container the compile and run gates can be
run before pushing instead of discovering breakage from CI logs — which is how
the P3-04 `%Error-LIFETIME` regression escaped.

Running the **full** matrix (`SEMICRAFT_TB_RUN_ALL=1 uv run pytest
backend/tests/golden/test_tb_run.py`, ~23 min) against clean HEAD 0d3466d:
**17 failed, 148 passed**. CI is green only because it defaults to the
`defaults` case per module — every failure is in a *non-default* option
variant, so this has been latent since the run gate went enforcing.

Failing cases: gray-counter (`enable_off` sv+v, `verilog_no_enable_wide`,
`wide_no_enable_sync_low` sv+v), lfsr (`enable_off` sv+v,
`output_style_serial` sv+v, `serial_no_enable_width32` sv+v,
`verilog_serial_width16`), clock-divider (`pulse_style.v`,
`verilog_pulse_wide.v`).

### RESOLVED (P3-09a) — and the first diagnosis here was wrong

The original entry blamed per-module expected values and prescribed
`bins[c+1]` in `gray_counter.py`. **That was wrong** — do not follow it. There
were two independent defects, and the dominant one was generator-side.

**Defect 1 — reset-deassertion race (`tb/generate_tb.py`, 15 of the 17).**
`generate_tb` drove the reset deassert in the *same timestep* as the rising edge
ending the reset hold, racing the DUT's own `always_ff @(posedge clk)`. A sync
reset can be observed already-deasserted on that edge, so the DUT takes a real
state update on an edge the TB still counts as "in reset". Masked whenever the
state update is gated by an enable still at 0 (all inputs initialise to 0) —
hence only *free-running* configs failed. Note TB_SPEC §6 already required this
discipline for vector drives ("no drive/sample race with the DUT's rising
edge"); the reset deassert was simply exempt from the generator's own rule.
Fixed by a `#1` settle before the deassert, now **normative in TB_SPEC §6a
(v2.2)**; the same settle was applied to `render_tb`'s `ResetSeq` path, which
had the identical race. Diff across all 165 TB goldens is one added `#1;` line;
**no module's expected values changed by this fix.**

**Defect 2 — expectations reverse-engineered from the racy sim.**
Fixing defect 1 *broke* clock-divider `defaults` + all 8 `reset_*` variants
(while fixing `pulse_style`). Cause: those toggle checks carried the comment
"Observed sim timing (first CI run-gate execution): at TB cycle c, c-1
post-reset rising edges have elapsed" — values reverse-engineered from the
**racy** run at 71a4c01, so they had encoded the bug as ground truth. Re-derived
from the RTL as `clk_out = (c // half) % 2` with exactly `c` post-reset edges
(checks now at cycle 0 → 0 and cycle `half` → 1), and verified against the DUT
by probe for `divide_by` 2 and 10 before changing any expectation.

**Defect 3 — lfsr serial model vs RTL (the remaining 5).**
`lfsr.py`'s `_observed` predicted the *feedback* bit for `output_style="serial"`,
but the RTL drives `assign out = q[0]` (the shifted-out bit, deliberate — its
inline comment calls it the conventional serial output and notes it also avoids
Verilator UNUSEDSIGNAL). The module's *documentation* was the stale part and said
"combinational feedback bit" in four places. Model corrected to `q_val & 1`; all
four doc sites corrected to describe `q[0]`. Verified by probe over 7 cycles.
The 5 serial cases' rtl/doc goldens change by the port **comment only** — the
`assign out = q[0]` logic is untouched.

**Lesson worth keeping:** never calibrate a `TbSpec` expected value from
observed simulation output. Derive it from the RTL and let the sim *disagree* —
an expectation fitted to a buggy sim silently freezes the bug, and here it also
misdirected the follow-up diagnosis. `clock_divider.py`'s comment now says the
checks are derived, not observed.

**CI gap that hid all of this — now closed.** `test_tb_run.py` defaults to the
`defaults` case per module; `SEMICRAFT_TB_RUN_ALL=1` runs the full 165-case
matrix (~20 min). Per user decision (2026-07-29), the full matrix now runs as
its own workflow — `.github/workflows/tb-matrix.yml`, nightly at 03:17 UTC plus
`workflow_dispatch` — rather than on every push, so regressions surface within a
day without adding ~20 min to the normal loop. It lives in a separate workflow
file on purpose: adding a `schedule:` trigger to `ci.yml` would have run *every*
job in it nightly.

## Checker wiring — deferred, with evidence (2026-07-29)

The plan says to wire P3-06's checker/monitor/scoreboard scaffolds into
`generate_files` alongside the assertions. Assertions landed (P3-05a/b). For
checkers, inspecting what they would actually add to the **current** catalog
argues for deferring rather than wiring:

**1. Two of the three check families duplicate the SVA just wired.** Their own
docstrings say so. `ResetValueCheck` is "distinct from
`assertions.spec.ResetKnownValue`" only in being *procedural* rather than
concurrent; `StabilityCheck` is the "procedural analogue" of `Stability` and its
docstring calls its reset guard "a weaker approximation than SVA". Attaching
them to the 7 current modules would emit a second, weaker copy of checks that
already run — including duplicate failure messages for a single real defect.

**2. The one non-duplicate family is fragile on its only candidate.**
`LatencyCheck` has no SVA counterpart, but no current module has a valid/ready
handshake. The nearest fit is rr-arbiter (`req` -> `grant_valid`), and the
emitted state machine arms on `request` and evaluates `response` on the
*following* edge. That works for `grant_style="registered"`, but for
`"combinational"` the grant is asserted in the *same* cycle as `req` and is gone
by the time the checker looks — a spurious failure. Making it correct would mean
a per-grant_style max_cycles and a same-cycle-response mode in the generator.

**3. Monitors and scoreboards need a transaction to be interesting.** A monitor
over a 1-bit `d`/`pulse` pair prints a line per cycle; a scoreboard needs
expected-vs-actual *transactions*, which these dataflow modules do not have.

**Where they do pay off: Phase 4 IPs.** FIFO, UART, SPI, I2C and the AXI-Lite
register block have real valid/ready handshakes (LatencyCheck, and the
`Handshake` SVA family), real transactions (monitor + scoreboard), and
request/response latencies worth bounding. P4-09 ("per-IP verification scaffold")
is the natural home, and by then P3-06's generators are compile-gated and ready.

**What is already done and not blocked by this:** the scaffolds generate, are
compile-verified in CI (P3-06a), and are documented. The gap is only that no
module *attaches* one — deliberately, per the above.

**If wiring is wanted anyway**, the mechanism is roughly: a `checker_spec` field
on `TbSpec` mirroring `assertion_spec`; a `restyle` for `CheckerSpec` (module
specs are canonical, same reason as assertions — P3-05a); emission as
`kind="tb"` at `<module>_checker.sv` (NOT a widened `GeneratedFile.kind` — that
is a frozen-contract change *and* breaks the frontend, whose `KIND_DOT` is an
exhaustive `Record<FileKind, string>`); an additive `checkers` field on
`TbModule` so the TB instantiates it (an un-instantiated checker file compiles
but verifies nothing — the exact "artifact that exists but does not run" pattern
this session kept finding); and both golden gates extended to pass the checker
file as an extra Verilator source.

## Phase 4 (started 2026-08-20)

| WP | Status | Notes |
|---|---|---|
| P4-01 IpDef contract | DONE | `semicraft_core/ips/`: `IpDef` (a strict superset of `ModuleDef` — an IP is a module plus `register_map(opts)` and `bundles(opts)`), the register-map model (`RegisterField`/`Register`/`RegisterMap`, rules R1–R6), bus-side `PortBundle`s over **flat** ports (no SV `interface` — locked decision), the two datasheet sections, and `check_bundles_against_module` (rules B1–B4) run during generation. Registry discovers a third catalog package; `by_kind("ip")` is empty until P4-02. Contract frozen in plan **Appendix B**; author guide `docs/IPS.md`. 91 tests in `backend/tests/ips/` (6 of them Verilator runs) |
| P4-02 AXI4-Lite regblock | DONE | `ips/regblock.py`: `build_axil_regblock(name, regmap, ...)` — a plain function over **any** register map, so P4-05..08 splice it in as their bus frontend rather than subclassing a catalog entry. Single-outstanding target, independent AW/W capture, exact byte-strobe merge, registered reads, per-access-type field semantics. `ips/axil_regblock.py` is the first shipped IP (`axil-regblock`). 8 golden cases x 2 languages; every one lints `-Wall` clean, compiles and runs green |
| P4-03a sync FIFO | DONE | `ips/sync_fifo.py`: power-of-two depth, wrap-bit pointers giving exact full/empty/count, registered reads, overflow/underflow ignored. **First consumer of the IR `Memory` node** (spec'd since IR v0.2, never emitted by any generator). Exercises the two `IpDef` branches the regblock could not: `register_map -> None`, and two bundles sharing one clock. 9 golden cases x 2 languages, all lint-clean, compiled and run |
| P4-03b async FIFO | BLOCKED — see below | needs a two-clock testbench; a tied-clock TB would verify the FIFO logic and nothing about the CDC |
| Next | **P4-04** (RAM/ROM — single clock, no register map, reuses the `Memory` node the FIFO just proved out); then P4-05..08 on top of the regblock. Also open: wire the cocotb path into `POST /api/v2/simulate` (SV-only today); add a frontend CI job (none exists — which is how a broken `npm ci` lockfile survived; note `npx tsc --noEmit` reports 10 pre-existing errors in *test* files, which `next build` does not typecheck); **v0.3.0 prepared but NOT tagged** (tag belongs on main after merge; CI does not run on this branch) | 2-agent budget per session |

### P4-01: the contract is proven by a real IP, not by its own docstrings

A contract with no implementor is the same "documented, never executed" shape
this project keeps finding defects in. So P4-01 ships a **test-only reference
IP** (`backend/tests/ips/reference_ip.py`) — a two-register CSR block on a
native bus — that goes through the entire pipeline: IR, both language
renderers, the datasheet, the smoke TB, SVA, and a **Verilator compile+run
gate over six configurations** (`backend/tests/ips/test_run.py`).

It is deliberately *not* a catalog item: P4-02's AXI4-Lite register block is
the first real IP, and shipping a throwaway CSR block first would mean golden
files and a datasheet for something P4-02 immediately supersedes. Tests
register it through the real registry, so it exercises no private back door.

### Bug found by that run gate: every generated testbench was uncompilable under any non-default naming style

`render_tb` held the clock net in a module-level `_CLOCK_NAME = "clk"`. That is
right for every *default* configuration — the default style renders the clock
port `clk` — but under any style with a prefix, suffix, or camelCase the DUT
clock renders (say) `p_clk` while every `@(posedge clk)` in the stimulus and
the watchdog still said `clk`. Verilator: `Can't find definition of variable:
'clk'`. All 7 modules, both languages, shipped in v0.2.0 and v0.3.0.

Why the 165-case golden matrix missed it: **no golden case sets a naming
style**, so the whole matrix exercises only the one spelling the constant
happened to match. The blind spot is naming, and it is the same shape as the
P3-05a assertion-restyle bug — metadata written in canonical names, rendered
without going through `build_name_map`.

Fixed by threading `TbModule.clock.signal` through the emitters (TB_SPEC §7a,
normative). Byte-identical at the default style, so **no golden file changed**
— which is exactly why nothing failed for two releases. Regression cover in
`tests/tb/test_directed_tb.py`: for every module under a prefix+camelCase
style, the set of nets the TB waits on must be exactly the styled clock, and
every such net must be declared.

### Still open from the same blind spot (NOT fixed here)

`generate._md_port_table` renders `PortGroup.ports` and `ExplanationDoc`
signal names **raw**, so under a naming style the datasheet documents ports the
RTL does not declare. Reproduced:

```
generate_files("gray-counter", {"naming": {"convention": "snake", "prefix": "p_"}})
  RTL:  input logic p_clk, p_rst_n, p_en; output logic [WIDTH-1:0] p_gray
  DOC:  | `clk` | | `rst_n` | | `en` | | `gray` |
```

Not fixed in P4-01 because the honest fix is not a display-time restyle: the 7
modules *hand-render* the `_n` suffix in `port_groups`/`explain` (e.g.
`gray_counter._reset_port_name`), so the name map — keyed on canonical `rst` —
does not match `rst_n`, and a prefix style would still emit `rst_n` rather than
`p_rst_n`. The fix is to make modules return canonical names and let
`generate_files` restyle, which touches all 7 modules and their tests. It is a
no-op at the default style (so no golden churn), and it is the same one-line
lesson as above. Worth its own WP.

P4-01's own new code does restyle correctly — `ips/bundles.restyle_bundles`,
covered by a test that asserts the rendered bundle names match the RTL under a
prefix+camelCase style.

### P4-02: three departures from a textbook AXI4-Lite target, all forced by the lint gate

This project lints every generated file with `verilator --lint-only -Wall` and
requires `status == "clean"` — **zero** warnings. A module that declares an
input it never reads fails. That single constraint drove three design
decisions, and I think it drove them in the right direction:

1. **No `awprot`/`arprot`.** A register block enforces no protection policy, so
   those spec-required inputs would be dead logic. Suppressing the warning with
   a lint pragma would have blinded the gate to genuine unused-signal bugs in
   the same file.
2. **The full byte address is decoded**, not just the word index — so the low
   offset bits are used, and a misaligned access returns SLVERR instead of
   silently aliasing onto the containing word.
3. **Reserved bits must be written as zero** (SLVERR otherwise, with no
   update). This is what makes every `wdata`/`wstrb` bit genuinely used no
   matter how sparse the register map is. Verified against a deliberately
   sparse map with no full-width writable field anywhere: `-Wall` clean in both
   languages.

The alternative — carving out a lint exception for IPs — would have weakened
the gate for exactly the most complex generated code in the project.

### The run gate is proved able to fail

An AXI transaction sequence is the kind of test that can look thorough while
proving nothing: drive some handshakes, check a response code, never actually
exercise the behaviour. So `tests/ips/test_axil_regblock_run.py` has two
halves — nine configurations that must pass, and **four deliberately broken
generators that must fail**: byte strobes ignored, write-only fields leaking on
read, the `w1c` hardware set dropped, the reserved-bit check disabled.

Building that caught two real problems:

- **A mutation that "passed".** Write-only readback was not covered, because
  `command_regs` defaulted to 0 and the phase was guarded on having such a
  register. The default configuration is what the standard CI run gate
  executes, so the default now includes one of every access type — pinned by
  `test_default_map_exercises_every_access_type`.
- **A flawed harness.** My first mutation run patched `regblock`'s globals
  before the registry had lazily imported `axil_regblock`, so the *reference
  model* got mutated alongside the hardware and the two agreed. The fix (force
  the import first) is in the test, with the reason, because the failure mode
  looks exactly like a passing test.

### Two more doc-vs-behaviour mismatches fixed on the way

- The generic register-map datasheet renderer stated reserved bits "ignore
  writes". This block **rejects** them with SLVERR. The renderer now describes
  only what the *model* owns — reserved bits read as zero — and leaves write
  policy to the generator, which states it in the IP's limitations.
- `bresp` was computed from the address hit alone, so a write rejected by the
  reserved-bit check still answered OKAY: the write silently vanished with a
  success response. Caught by the M4 mutation and pinned by
  `test_write_response_covers_both_error_causes`.

### Also closed

`test_cocotb_run.py` covered `by_kind("module")` only, so an IP's generated
cocotb testbench was committed as a golden and never executed — the
"artifact that exists but does not run" pattern again. It now covers IPs too.
`test_snapshots.py` filtered golden doc/tb cases on `kind == "module"`, which
would have silently skipped every IP golden.

### P4-03a: the sync FIFO, and why the async FIFO is not here

The plan pairs a synchronous FIFO with a gray-pointer asynchronous one. The
sync FIFO shipped; the async FIFO is **deferred, with a concrete unblock
path**, and the reason is the same one that has driven most of this project's
decisions.

The testbench framework drives **one** clock: `TbSpec.clock` is a single name
and `TbModule` holds a single `ClockGen`. An async FIFO's defining property is
safe transfer between two *independent* clocks. Tying both clocks together in
the testbench would exercise the pointer and memory logic and **nothing** about
the clock-domain crossing — while the datasheet claimed CDC safety. That is
the "artifact that exists but does not run" pattern, and CDC bugs are exactly
the class that cannot be caught by reading the RTL.

Unblocking it is a TB-IR work package: a second clock on `TbSpec`, a clock
selector on `WaitCycles`, and per-clock cycle anchoring for vectors and checks.
That touches TB_SPEC, a frozen contract, so it needs a recorded decision first
rather than a silent edit.

### What the FIFO proved out beyond itself

- **The IR `Memory` node had never been used.** Added in IR v0.2 (P2-02/03),
  spec'd in IR_SPEC §10.2, unit-tested — and no generator ever emitted one, so
  the render path was untried in a real module. It works: `logic [7:0] mem [8]`
  in SystemVerilog, `reg [7:0] mem [0:15]` in Verilog-2001, both lint-clean.
  Verified before building on it rather than after.
- **`register_map -> None` and shared-clock bundles.** P4-01 declared both
  branches; nothing demonstrated either until now. The datasheet correctly
  omits the register-map section, and the `wr`/`rd` bundles share `clk`.

### Keeping a deep FIFO's testbench small

Filling a 1024-entry FIFO one driven cycle per entry would emit a testbench of
thousands of lines — the shape that produced a 65k-line clock-divider TB and
timed out the compile gate. The fill and drain phases instead hold their enable
for a single driven cycle and then idle, which `generate_tb` coalesces into one
`repeat (N)`. A 1024-deep FIFO's TB is under 400 lines, pinned by a test.

### The run gate, again with a mutation half

Four broken generators that must fail: flow control removed (`!full`/`!empty`
guards neutered), read index taken from the write pointer, `full` stuck low,
`empty` stuck low. All four are caught. A FIFO testbench that pushes a few
words and pops them back is easy to write and proves almost nothing — the two
properties that matter are boundary flow control and ordering, and those are
what the mutations target.
