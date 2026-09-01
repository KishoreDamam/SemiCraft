# cocotb Testbench Backend (P3-08, beta)

**Status: beta.** The SystemVerilog smoke testbench remains the supported
default and the backend every golden/compile/run gate exercises across the full
option matrix. This backend emits the *same* `TbSpec` recipe as a Python
[cocotb](https://www.cocotb.org/) test module, so a user who would rather extend
stimulus in Python than in SystemVerilog can.

Owner: `semicraft_core/tb/cocotb_tb.py`. Emitted by `generate_files()` as a
second `tb`-kind file, `test_<module>.py`, when
`semicraft_core.generate.EMIT_COCOTB_TB` is true (it is).

## Why `kind="tb"` and not a new file kind

`GeneratedFile.kind` is the frozen `Literal["rtl","tb","doc"]` of plan Appendix
A.1. Widening it is a contract change *and* a frontend build break: `KIND_DOT`
in `FileTabs.tsx` is an exhaustive `Record<FileKind, string>`, so a new member
fails the TypeScript build until the type and the map are both updated. The file
is distinguished by its path instead — exactly as the datasheet
(`<module>.md`) and the test plan (`<module>_testplan.md`) already share
`kind="doc"`.

## Semantics: identical to the SV backend, by construction

Both backends read one `TbSpec` and resolve every net through the same style
name map (`render.style.build_name_map`), so they agree on identifiers and
expected values rather than by convention:

| Aspect | Both backends |
|---|---|
| Clock | free-running, 10 ns period |
| Input init | every input driven 0 before reset |
| Reset | asserted at time 0, held `reset_cycles` **rising** edges, **1 ns settle**, then deasserted |
| Directed cycle `c` | anchored to a **falling** edge: drive the vector, settle 1 ns, sample checks |
| Values | width-masked and `PortConstraint`-clamped by the shared `_constrain_value` |
| Timeout | the same `(reset_cycles + n_cycles + 16) * 8` cycle budget |
| Pass marker | `SMOKE PASS: <module>` |

The 1 ns settle before reset deassertion is **normative** (TB_SPEC §6a), not
cosmetic. A deassert sharing a timestep with the rising edge that ends the reset
hold races the DUT's own clocked process; that bug cost 17 golden SV testbenches
a correct run before it was found (P3-09a). A test asserts the settle is present
in the emitted Python so this backend cannot regress into the same race.

`test_expected_values_match_the_sv_backend` asserts both backends emit the same
expected value for every `TbSpec` check — a divergence means one of them
mis-renders the shared recipe.

## Toolchain: cocotb 1.x, and why

Generated code targets the **cocotb 1.x** API — `Clock(..., units="ns")` and
`cocotb.runner`. This is a verified constraint, not a preference:

- cocotb 2.x renames these (`unit=`, `cocotb_tools.runner`), and
- cocotb 2.0.1's Verilator VPI shim calls `VerilatedVpi::doInertialPuts()` and
  `VerilatedVpi::evalNeeded()`, **neither of which exists in Verilator 5.020** —
  the newest version available from apt on Ubuntu noble, and the one this
  project's sim sandbox and CI use. Building a cocotb 2.0.1 testbench against it
  fails in `make` with "is not a member of ‘VerilatedVpi’".

cocotb 1.9.2 runs clean against Verilator 5.020, so the dev dependency is pinned
there. **Revisit the pin only together with a newer Verilator**, and update
`cocotb_tb.py`'s emitted API spellings in the same change —
`test_targets_cocotb_1x_api` will fail loudly if the pin moves without them.

## Running a generated testbench

```python
from pathlib import Path
from cocotb.runner import get_runner

runner = get_runner("verilator")
runner.build(
    verilog_sources=[Path("gray_counter.sv")],
    hdl_toplevel="gray_counter",
    build_dir="sim_build",
    build_args=["--timing"],
    always=True,
)
runner.test(hdl_toplevel="gray_counter", test_module="test_gray_counter", build_dir="sim_build")
```

`--timing` is required, as it is for the SV backend: the testbenches use timing
controls that Verilator's default scheduling mode does not support.

## Gates

- `backend/tests/tb/test_cocotb_tb.py` — text-level properties: the emitted text
  **parses as Python** (`ast.parse`), is deterministic, keeps the 1.x API
  spellings, preserves the reset settle, resolves names under a naming style,
  and matches the SV backend's expected values.
- `backend/tests/tb/test_cocotb_run.py` — **executes** each module's generated
  testbench against its generated RTL under Verilator and asserts `FAIL=0` plus
  the pass marker. Skips (never fails) without `verilator` or `cocotb`.
  All 7 modules pass in ~70 s.
- `backend/tests/golden/test_snapshots.py::test_snapshot_cocotb` — byte-exact
  snapshot per case (165 goldens).

Note that cocotb's runner exits 0 even when a test fails unless results are
checked, so the run gate asserts on the regression summary and the pass marker
rather than trusting the exit code.

## Limitations

- **Defaults case only in the run gate.** Each case costs a full Verilator
  build; the SV backend carries the exhaustive matrix. The cocotb *text* is
  golden-locked for every case, so drift is still caught — only execution is
  sampled.
- **No assertions.** `TbSpec.assertion_spec` produces SVA in the SV backend
  (P3-05a/b); SVA is a SystemVerilog construct with no cocotb equivalent, so a
  module's assertions are simply absent from its cocotb testbench. The
  directed checks are identical.
- **Single clock/reset, default parameterization** — the same limits as the SV
  backend (TB_SPEC §8).
- **Not in the sim sandbox service.** `POST /api/v2/simulate` runs the SV smoke
  TB via `sim.runner`; wiring the cocotb path through the API is follow-up work.
