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
| P4-04a sync RAM | DONE | `ips/ram.py`: single-port and simple dual-port synchronous RAM. **No reset at all** (storage must not be cleared; resetting only the output register is what blocks block-RAM inference), so it extends `CommonOptions` not `ClockedOptions` and `TbSpec.reset is None`. Read-during-write returns OLD data (READ_FIRST), pinned by a directed check and by a write-first mutation in the run gate. 7 golden cases x 2 languages |
| P4-04b ROM | BLOCKED — see below | needs memory initialisation, which the synthesizable IR does not express; two routes, both needing a recorded IR decision first |
| P4-05a composition + GPIO | DONE | `build_axil_regblock(..., field_ports=False)` emits the hardware face as internal signals, so a peripheral splices the register block into its own module — one flat module, no submodule instantiation. Standalone goldens byte-identical. `AxilSequencer`/`RegisterModel` promoted into `regblock.py` so composed IPs share the AXI timing. First composed IP: `axil-gpio` (DIR/OUT/IN + input synchroniser). 7 golden cases x 2 languages |
| P4-05b UART | DONE | `ips/axil_uart.py`: 8N1 UART, programmable baud divisor, TX/RX FSMs spliced onto the register block. Status flags are W1C (the block has no read-side effect); the transmit trigger is the register write strobe, delayed one cycle. 7 golden cases x 2 languages |
| P4-06 SPI master | DONE | `ips/axil_spi.py`: full-duplex 8-bit MSB-first master, all four CPOL/CPHA modes as generate-time options, programmable divider, manual chip select. CPHA=1 narrows the receive register to 7 bits (the last sample goes straight to RXDATA) — found by the `-Wall` gate. 8 golden cases x 2 languages |
| frontend CI | DONE | the frontend had 172 tests, a build and an eslint config and **no CI job ran any of them** — the gap that let a broken `npm ci` lockfile survive. All four commands verified locally before wiring |
| P4-07 I2C master | DONE | `ips/axil_i2c.py`: open-drain master (pull-down enables + sensed levels, no `inout`), START/STOP/byte primitives via CMD, ACK/NACK, **clock stretching** with the testbench stretching deliberately. Bus drivers are continuous functions of registered state, not FSM side effects. 7 golden cases x 2 languages |
| P4-08 timer + intc | DONE | `ips/axil_timer.py`: prescaled **down**-counter (zero test instead of a full-width comparator), one-shot or periodic, maskable level `irq`. One-shot stops via an internal `running` flop because `CTRL.enable` is an `rw` field only software can write. `ips/axil_intc.py`: `num_irq` sources, **mask on the output not on the latch** (a request masked at arrival must still be findable when software enables it later), edge or level trigger as a generate-time option, edge history taken *after* the synchroniser. 7 + 9 golden cases x 2 languages |
| Next | **P4-09 (per-IP verification scaffold)** — where the P3-06 checker/monitor/scoreboard generators, compile-gated and ready since Phase 3, finally get attached to real IPs — then P4-10 (per-IP doc generator, wavedrom timing diagrams) and P4-11 (example instantiations + release v0.4.0). The two blocked items (async FIFO, ROM) each need a recorded contract decision. Also open: wire the cocotb path into `POST /api/v2/simulate` (SV-only today); the full suite is now ~50 min and grows with each IP — if it becomes the bottleneck, move the per-IP run gates to the nightly matrix and keep `defaults` in the main loop, the same trade already made for the TB matrix; **v0.3.0 prepared but NOT tagged** (tag belongs on main after merge; CI does not run on this branch) | 2-agent budget per session |

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

### P4-04: the RAM, and the two decisions it forced

**No reset.** Storage must not be cleared — a deep memory's reset costs real
logic for no observable behaviour — and resetting *only* the output register is
what most often blocks block-RAM inference. So the module has a bare clock and
its options extend `CommonOptions`, not `ClockedOptions`: reset style and
polarity would be options with nothing to configure. This is the first IP with
`TbSpec.reset = None`, which `generate_tb` already handled but nothing had
exercised.

The consequence is honest rather than hidden: `dout` holds no defined value
until the first completed read (X in a four-state simulator, **zero** in
Verilator). A test asserts the generated testbench never checks `dout` before
a read completes, because doing so would encode one simulator's
initialisation convention as a requirement of the design.

**Read-during-write returns OLD data.** Both accesses are non-blocking in one
process, so a same-address read-during-write yields the previous contents
(READ_FIRST). This is the one RAM behaviour nothing in the port list reveals,
so it gets a directed check *and* a `write_first_bypass` mutation in the run
gate — in both single and dual-port mode. A generator that got it wrong would
compile, lint clean, and pass any testbench that keeps writes and reads on
separate cycles.

### ROM: blocked on a contract decision, not on effort

P4-04 pairs the RAM with a ROM, which is not here. A ROM is only useful if its
contents are specified, and nothing available today can express that:

- The **synthesizable IR has no memory-initialisation construct**.
  `initial`/`$readmemh` belong to the testbench node family, which the
  synthesizable validator rejects by design (TB_SPEC §1 separation rule).
- The **options form has no array-of-integers widget**, so contents cannot
  come from options either (the same constraint that made the AXI register
  block take counts rather than a user-authored map).
- A **case-statement lookup** works only for tiny depths — a 1024-entry ROM
  would emit 1024 case arms.

Two viable routes, each needing a recorded decision before any code:

1. An additive `init_values` on `Memory`, rendered as an `initial` block.
   FPGA-friendly; not portable to ASIC flows.
2. A generated `.hex` file plus `$readmemh`. Portable, but
   `GeneratedFile.kind` is a frozen Literal (`rtl`/`tb`/`doc`) and a data file
   is none of those — so it is a frozen-contract change as well.

Choosing between them is the first task of that work package. Guessing now and
discovering the constraint later is how a frozen contract gets edited silently.

### A test bug worth recording

`test_read_enable_can_be_omitted` asserted `"re" not in sv`. That is true of
almost no generated file: the license banner contains "Free". Fixed with a
whole-identifier regex helper, and the same helper now guards the `rst`/`addr`
absence checks in that file — a bare substring test for a short identifier is
close to worthless against generated text.

### P4-05a: prove the composition before betting a UART on it

P4-05 is the UART, and its real prerequisite is the *composition* mechanism —
a peripheral needs its own logic plus a register frontend, and nothing had ever
spliced the register block into a larger module. So the mechanism landed first,
proved on the simplest peripheral that can exercise it, rather than being
debugged for the first time underneath a baud-rate generator.

`build_axil_regblock(..., field_ports=False)` emits the hardware face as
internal signals instead of ports; the peripheral appends its pins and logic
and gets one flat module. Two obligations fall out of the `-Wall` gate: a
composer must **use every field it declares** (an unused signal fails), and
must **drive the read-only ones** (the block reads them; nothing else will).
The standalone `axil-regblock` goldens are byte-identical, which is the check
that the flag did not change the default path.

`AxilSequencer` and `RegisterModel` moved into `regblock.py`, beside the
generator whose timing they encode, so a composed IP's testbench cannot drift
from the standalone block's.

### The GPIO check that nearly did not work

A synchroniser is invisible to an ordinary readback test: read `IN` after the
pins settle and it passes whether the guard exists or not. So the testbench
also reads `IN` while the value is still in flight and requires the **old**
one.

The first version of that check was placed wrong. A read issued in the *same*
cycle as the pin change captures one edge later, which reads old even with no
synchroniser at all — the `one_stage_short` mutation sailed straight through
it. Delaying the read by one cycle is what makes it discriminate. Both
mutations (bypass, and one stage instead of two) now fail as they should.

Worth recording because a missing metastability guard is the classic defect
that **never shows up in simulation**: the check has to be timed deliberately,
and writing it by feel produced something that looked right and tested
nothing.

### P4-05b: the UART, and two things worth carrying forward

**A strobe and its value are not available in the same cycle.** `TXDATA` is a
write-only field: its storage holds the byte, but storage cannot say *when* a
write happened. The register block already computes that —
`write_strobe_name("TXDATA")` is high for exactly one cycle per accepted write
— but `txdata_data` only takes the new byte on the same edge the strobe is
sampled, so a transmitter triggered directly off the strobe would send the
*previous* byte. The one-cycle delay is now documented as part of the
composition contract, because every future peripheral with a command register
hits it.

**Read-to-clear was the obvious design and the wrong one.** The natural UART
idiom is "reading RXDATA clears rx_valid", but the block's read path is a mux
with no per-register read strobe. Adding one meant a new access type plus a
signal on every register, for exactly one user. The flags are W1C instead —
something the block already implements exactly, and a real UART interface in
its own right. A contract stayed the size it was.

### The test bytes were bit-palindromes

The mutation gate includes "transmits MSB first", which leaves a perfectly
well-formed frame behind. Writing it exposed that my chosen test bytes, `0xA5`
and `0x3C`, both read the **same backwards** — a reversed transmitter would
emit an identical frame and every check would pass. Changed to `0x4B`/`0x2D`,
and a test now asserts the transmitted byte is not a palindrome.

This is the same failure shape as the GPIO synchroniser check from P4-05a: a
test that looks thorough, exercises the right signal, and cannot fail. Both
were found only by trying to break the hardware on purpose.

### Three test bugs of mine, all from guessing at the RTL

`2'b00:` (the renderer emits minimal-width constants, `2'b0:`), slicing the
*first* `if (!areset_n)` block when the UART has two clocked processes and its
own is the second, and a `zip(..., strict=True)` over lists of different
length. All three were assertions about output I had not looked at. Reading
the generated RTL first would have avoided all of them.

### P4-06: two timing lessons, both bought with a failing run

**A flag set by peripheral logic is readable one cycle later than the event
that set it.** The completing sclk edge raises the W1C *set request*; the
register block latches it in its **own** always block, so the flag crosses a
clock edge on the way to being readable. I collapsed "transfer done" and
"status readable" into one cycle and every mode failed with
`rdata expected 2, got 0`. This applies to every composed IP — the UART has the
same structure and happened to have enough slack to hide it.

**Check a level at the first cycle of a half period, not one cycle into it.**
The original sclk check sat at `active + div + 1`, which is inside the first
half period for any divisor above 1 and inside the *next* one at divisor 1. It
passed everywhere except the fastest clock.

The second fix is also a caution about fixing two things at once: correcting
the sclk offset and moving the miso drive in the same edit turned 3 failures
into 10, because the `+1` I removed was load-bearing for the *other* reason.
Reading the failure values (`expected 2, got 0` — a status flag, not a clock
level) is what separated them.

### A mutation that ate itself

`clock_never_toggles` was written as "call the real `_transfer_body` and drop
the sclk assignment" — but it looked the function up through the module, which
`monkeypatch` had just replaced with the mutation. It recursed until the
interpreter gave up, and the traceback blamed the generator. The original is
now captured at import time, with a comment saying why.

### CPHA=1 needs a narrower receive register

With CPHA=0 the last sample lands on edge 14, so all eight bits live in the
shift register. With CPHA=1 the last sample *is* edge 15 and goes straight into
RXDATA, so bit 7 of the register would be written and never read. The `-Wall`
gate flagged it; the fix is a 7-bit register for that phase, which is smaller
hardware as well as clean lint.

### Frontend CI, finally

I had flagged "no frontend CI job" in six consecutive handoffs without fixing
it. It is now a real job — `npm ci`, lint, tests, production build — and all
four commands were verified locally first. `npm ci` rather than `npm install`
is deliberate: it fails on a lockfile that does not match `package.json`, which
is the exact failure the job exists to catch.

### P4-07: two bugs, and how each was found

**The quarter counter kept counting while the clock was stretched.** The stall
branch incremented `q_cnt` unconditionally, so it would wrap all the way round
before `q_cnt == div-1` came true again — a 2**16-cycle hang. Only reachable
*with* stretching, which is exactly why the testbench stretches instead of
assuming a cooperative bus. Found while writing the stretch into the
testbench, before the first run.

**A guard named in a function's name is not a guard.** `_sample_at_phase2`
never checked the phase: it sampled on every quarter, so a read shifted in
four samples per bit. The write transaction passed anyway — its only sample is
the ACK, and the slave holds SDA low across all four ACK quarters, so sampling
four times gave the same answer. It took reading a byte back to expose it.

And the read transaction only existed because **ruff flagged `rxdata` as
assigned but never used** — my own docstring said "write a byte, then read one
back" while the testbench only ever wrote. The lint error was the thing that
noticed the docstring was lying.

### Why the bus drivers are combinational

An I2C bit is four quarter-phases and there are five states, so the sequential
form is twenty little bundles of side effects, each of which has to set SCL and
SDA correctly on entry. As continuous functions of the registered state they
change only just after a clock edge — no glitch risk — and each line's whole
behaviour reads in one expression, which is what made `_expected_drive` in the
testbench writable as an independent restatement rather than a copy.

### P4-08: the timer and the interrupt controller, and what each mutation had to attack

Two IPs, one work package, sharing nothing but the P4-05a composition. Both
landed lint-clean and green on the first Verilator run — which is exactly when
the mutation half stops being a formality and becomes the only evidence that
the testbenches check anything.

**Checking an expiry from one side proves nothing.** "`irq` high at cycle N"
passes for any timer that fires *at or before* N, so a prescaler that is
ignored outright, or a terminal count one tick early, would both pass. Each
expiry is now checked from both sides — low on the cycle before the derived
rise, high on it — and that pair is what `prescaler_ignored` and
`terminal_off_by_one` fail against. `always_reload` fires at exactly the right
moment and diverges only afterwards, so it needed a different check entirely:
three idle periods after the one-shot expiry, with `COUNT` and `STATUS` both
required to have stayed put.

**A one-shot cannot stop itself through `CTRL.enable`.** That field is `rw` —
the register block owns it and software alone writes it. Hardware stopping the
counter needs its own state, which is what `running` is. Worth remembering for
every future peripheral: the composition gives you the register's *value*, not
a way to change it from the hardware side unless the field is `ro` or `w1c`.

**Masking before the latch is the bug that looks like a simplification.** The
interrupt controller latches every request regardless of `ENABLE` and masks
only the output. Folding the mask into the latch is one fewer signal and loses
precisely the request software wants to find when it enables a source later.
The opening section of the sequence exists to catch it: a request is
deliberately raised while everything is masked, and unmasking alone must raise
`irq_out` with no new request.

**A latency bug has no wrong value to catch it by.** Taking the request one
flop earlier than the settled synchroniser stage changes nothing a simulator
can see — simulation has no metastability — only *when* it happens. So the
sequence reads `PENDING` on the exact cycle the last stage goes high and
requires zero, then reads again two cycles later and requires the request.
`synchroniser_bypassed` and `one_stage_short` both die on the first read. This
is the same shape as the GPIO's `one_stage_short` from P4-05a, and it is now
clear that it generalises: **for anything crossing a clock domain, pin the
latency, because the value will look right either way.**

**The edge history flop belongs after the synchroniser, not inside it.** With
two stages the chain already holds a previous value in `irq_sync0`, and using
it saves a flop. It is also one flop deep from an asynchronous pin, so feeding
it into the edge comparison puts the metastability hazard back into the very
latch the synchroniser protects. Cheap to get wrong; free to get right.

**Edge and level are invisible to a pulse.** Every pulse earlier in the
sequence latches identically under both modes, so the two swap mutations
survive all of it. They are caught only by the final section, which holds a
source asserted across a write-1-to-clear: level re-arms the flag on the same
clock the write clears it, edge does not.

Phase 4's exit criterion — "8+ IPs, each: both-language RTL, regblock-driven
where applicable, datasheet, TB running in CI" — is met at nine.
