# SemiCraft Testbench Node Family — Stub Specification

**Status: stub (P2-13).** The full TB node family lands with Phase 3 (plan
P3-01) and will replace these internals; the stable public seam is
`semicraft_core.tb.generate_tb(module_def, opts, rtl_module) -> str` and the
`GeneratedFile(kind="tb", path="<module>_tb.sv")` output of `generate_files`.

## Separation rule (normative, from plan cross-cutting decision 2)

Testbench constructs live in `semicraft_core/tb/`, entirely outside the
synthesizable IR (`semicraft_core/ir/`). The synthesizable validator never
sees TB nodes; generators can never emit TB constructs into RTL. The stub
family reads the synthesizable IR (ports, params, reset specs) but shares no
node types with it.

## Stub node set (`tb/nodes.py`)

`TbModule(name, decls, clock, dut, initial, banner)`, `Decl(name, width)`,
`ClockGen(signal, half_period_ns=5)`, `DutInstance(module, instance,
connections)`, `Initial(stmts)`; statements: `DriveSignal(signal, value,
width)`, `WaitCycles(n, edge)`, `Delay(ns)`, `ExpectSignal(signal, expected,
width, label)`, `Display(text)`, `Finish()`, `TbComment(text)`.

## Rendering rules (`tb/render_tb.py`)

- SystemVerilog only, even for Verilog DUTs (a `.sv` TB instantiating a `.v`
  module is fine under Verilator; simplest single path).
- `timescale 1ns/1ps`; free-running clock `always #5 clk = ~clk`.
- Reset asserted from time 0, held `TbSpec.reset_cycles` rising edges, then
  deasserted; polarity taken from the DUT's `ResetSpec` (active-low renders
  assert=0/deassert=1 on the styled `_n` net).
- Directed cycle `c`: inputs driven on the `negedge` (no drive/sample race
  with the DUT's rising edge); checks sample after a `#1` settle, so they see
  registered state from prior rising edges plus just-driven combinational
  inputs — the convention `TbSpec.checks[].cycle` indices assume.
- Checks: `if (sig !== expected) $fatal(1, "SMOKE FAIL: ...")`; success path
  prints `SMOKE PASS: <module>` and `$finish`.
- Deterministic: no timestamps; banner mirrors the RTL header (tool version,
  config hash, disclaimer).

## Name/width consistency (the correctness anchor)

`generate_tb` receives the *stamped IR module* the RTL was rendered from and
resolves every net through the same style name map (`render.style
.build_name_map`) the RTL renderer used. Port widths are evaluated from the
module's default parameter values (`Const`/`Ref`/`+ - *` expressions only —
anything else raises rather than guessing).

## Limitations (stub)

- Compile-checked in CI (`verilator --binary`, P2-14 gate); smoke TBs are not
  yet *run* in CI — execution gating lands with the Phase 3 sim sandbox
  (P3-03/P3-09).
- No waveform dump, no per-test reporting, no randomization, no assertions
  beyond `ExpectSignal`, single clock/reset only, default parameterization
  only (widths resolved from parameter defaults).
- Modules whose `TbSpec.clock` is `None` produce no TB file.
