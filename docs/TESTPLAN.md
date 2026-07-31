# SemiCraft Test-Plan Document Generator (P3-07)

**Owner:** verification core (`semicraft_core/testplan.py`). Companion to
[TB_SPEC.md](TB_SPEC.md) (the TB IR family and `generate_tb`'s own rendering
rules) and [ASSERTIONS.md](ASSERTIONS.md) (the SVA template generator this
document reports on, when a module uses one).

`generate_testplan(item, opts, rtl_module, explanation, config_hash_value)`
renders a markdown **test-plan / verification-checklist** document for one
generated module configuration. It adds **no new metadata** to `ModuleDef` —
it is derived entirely from the three method surfaces every module already
implements: `explain(opts)`, `port_groups(opts)`, and `tb_spec(opts)`. Wired
into `generate_files()` (`semicraft_core/generate.py`) as a second
`doc`-kind file, `<module>_testplan.md`, appended **after** the datasheet
(`<module>.md`) so existing code that picks "the" doc file via
`next(f for f in files if f.kind == "doc")` keeps resolving to the datasheet.

## Design rule: every claim must be true of the generated TB

This is the house rule the whole generator is built around (CLAUDE.md:
"honesty over polish"). `generate_testplan` never invents test coverage —
every sentence in the Test Plan and Coverage sections is re-derived from the
exact same facts `semicraft_core.tb.generate_tb.generate_tb` uses to render
the TB text, using the same algorithms where it matters:

- the **Test Plan table** groups `Check`s by cycle using the identical
  `checks_by_cycle` grouping `generate_tb` builds internally, so a table row
  corresponds 1:1 to a real "drive, settle, sample" block in the rendered
  `.sv` file;
- signal names shown anywhere in the document are resolved through
  `render.style.build_name_map` against the *stamped* `rtl_module` — the same
  name map `generate_tb` builds — so a `naming`/`prefix`/`suffix` option that
  changes the rendered TB's identifiers changes this document's identifiers
  identically;
- the **Assertions** section, when `tb_spec.assertion_spec` is set, tabulates
  the literal output of `assertions.generate_assertions(...)` — the same call
  `generate_tb` makes — rather than re-describing the spec's item types, so it
  cannot drift from the concurrent-assertion block the TB actually emits.

A module whose `tb_spec(opts).clock` is `None` gets no smoke TB at all
(`generate_tb` returns `""`, no `tb` file is emitted). The test-plan document
is still generated for it — the doc-file and tb-file existence are
independent in `generate_files()` — but its Test Plan and Coverage sections
say plainly that no TB is generated instead of describing one that does not
exist.

## Document structure

| Section | Derived from | Notes |
|---|---|---|
| Title + purpose + provenance | `item.name`, `explanation.purpose`, `config_hash` | Mirrors `generate._module_doc`'s provenance line so the datasheet and test plan read as a matched pair. The provenance sentence names the exact `<module>_tb.sv` file the table below mirrors (or says plainly that none is generated). |
| **Features Under Test** | `explanation.configuration`, `explanation.reset_behavior`, `explanation.enable_behavior` | The module's own stated intent, restated as a checklist. `enable_behavior` is omitted when `None` (module has no enable). |
| **Test Plan** | `tb_spec(opts).checks`, grouped by `cycle` | One row per checked cycle (`checks_by_cycle`, matching `generate_tb`), not one row per `Check` — a module with many checks on the same cycle still gets one table row. Each row's Stimulus cell reports the actual `vectors[cycle]` drive (or "no new stimulus this cycle" when the cycle only carries checks). Status is always the literal generated form (`if (sig !== expected) $fatal(...)`) — every row is a real, directed, self-checking assertion. If `tb_spec.checks` is empty, the table is replaced by an explicit statement that the smoke TB self-checks nothing. If `tb_spec.clock` is `None`, the whole section is replaced by a statement that no TB exists. |
| **Coverage / Stimulus Summary** | `tb_spec.clock`/`reset`/`reset_cycles`, `len(vectors)` vs. the cycle count implied by `checks`, `tb_spec.port_constraints`, `port_groups(opts)` × `rtl_module.ports` | Clock/reset facts, then a **Ports exercised** table grouped exactly like the datasheet's port table (reusing `port_groups()`), each port marked Driven (for inputs: does any vector key ever set it?) and Checked (does any `Check` target it?). Ends in an explicit **Gaps** list: every input that is never driven (held at the TB's blanket initial value, 0, for the whole run) and every output that is never checked, named individually — see "The Gaps list" below. |
| **Assertions (SVA)** | `tb_spec.assertion_spec` | `None` (true of every module shipped as of P3-07): states plainly that no SVA is generated. Set: tabulates the actual `AssertProperty` tuple from `assertions.generate_assertions(...)` (name, property text, clock, `disable iff` guard). |
| **Not Covered / Limitations** | `explanation.limitations` verbatim, plus fixed structural limitations, plus one dynamic note | `explanation.limitations` first (module-specific, human-written), then three limitations that are structurally true of every `generate_tb` output (directed not randomized; default parameterization only, no parameter overrides at TB-instantiation time; single clock/reset domain, no CDC), then — only when true — a note that no `Check` samples cycle 0 (the first cycle after reset release), meaning reset behavior is exercised but not self-checked. |

## The Gaps list

The Coverage section's Gaps list is deliberately the least softened part of
the document (P3-07 brief: "the honest gap list — this is the most valuable
part of the document, do not soften it"). Two categories, computed directly
from `tb_spec`, not estimated:

- **Undriven input.** An input port that never appears as a key in any
  `tb_spec.vectors[c]` dict. `generate_tb` still initializes every input to 0
  before the stimulus loop (`DriveSignal(name, 0, width)`), so the port *is*
  driven in the rendered TB — just never to anything but 0, for the entire
  run. The gap bullet says exactly that, not "not tested."
- **Unchecked output.** An output port that is never a `Check.signal`. It is
  wired into the DUT instantiation and its value is real in the waveform, but
  nothing in the generated TB compares it to an expected value.

A module where every input varies and every output is checked at least once
reports `None found` explicitly, rather than an empty section — silence is
not the same claim as a verified absence of gaps.

## Reset-port name matching (a real bug this generator has to avoid)

`port_groups(opts)` returns **canonical** IR port names with one documented
exception: each module's own `_reset_port_name` helper (see e.g.
`modules/edge_detector.py`) pre-appends `_n` to the reset port name when the
reset is active-low, to match the join key `explain()` also uses for its
`SignalDoc` rows. That pre-suffixed name (`"rst_n"`) does **not** equal the
canonical `tb_spec.reset` string (`"rst"`) for an active-low module.

`generate_testplan` matches a `port_groups()` entry against `spec.clock` /
`spec.reset` **and** their `_n`-suffixed forms, and — once matched — displays
the role using `styled(spec.clock)` / `styled(spec.reset)` (resolved through
the real `build_name_map`, so a user's naming `prefix`/`suffix`/`convention`
is honored), never `styled(port_name)` on the pre-suffixed group name (which
would be a no-op pass-through for `"rst_n"` and silently drop a prefix). Every
other `port_groups()` entry is a genuine canonical name and is styled
directly. This was caught during initial development by reviewing the
`edge-detector` output by hand: the reset port was initially misreported as
an "undriven input" gap, which was the wrong claim.

## Determinism

Same as every other generator in this codebase: identical `(item, opts,
rtl_module, explanation, config_hash_value)` produces byte-identical text —
no timestamps, no randomness, no dict/set iteration-order dependence (`Gaps`
and table rows are built by iterating `port_groups()`'s declared order and
`sorted(checks_by_cycle)`, never an unordered set except where the result is
itself re-sorted, as with `port_constraints`).

## Known limitations of the generator itself

- **Port width is not reported.** The Ports-exercised table shows direction
  and driven/checked status, not bit width, to avoid duplicating
  `generate_tb`'s parameter-width evaluator (`_eval_int`/`_width_of`) in a
  second place that could silently drift from it. A width-resolution failure
  in the TB generator itself already surfaces as a hard error at generation
  time; this document does not attempt to re-derive widths as informational
  text.
- **No cross-signal timing relationships.** A `Check` is reported as
  "signal == value at cycle N"; the document does not describe *why* that
  value is expected (e.g. "one cycle of registered-output latency after the
  edge") beyond what `explanation.reset_behavior`/`configuration` already say
  in prose. Readers needing that reasoning should read the module's
  `tb_spec()` source, which is usually commented with exactly this rationale
  (see `modules/edge_detector.py` for the reference example).
- **Reset-port name matching relies on the `_n`-suffix convention** described
  above, not a fully general canonical/rendered-name distinction. It is exact
  for every module shipped as of P3-07 (all of which name their reset port
  `"rst"`) and degrades gracefully (falls through to being treated as an
  ordinary data port, which would show up as a spurious Gap rather than
  silently mis-attributing driven/checked status) for a hypothetical future
  module using a different reset port name with a non-`_n` active-low
  convention.
