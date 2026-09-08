# SemiCraft

SemiCraft generates RTL, testbenches and documentation from structured
options. You pick a block, set its parameters in a form, and get back
lint-clean SystemVerilog or Verilog-2001 — together with a datasheet, a
runnable testbench, and an explanation of what was generated and why.

It is for RTL design and verification engineers, FPGA/ASIC/SoC engineers, and
students who want the boilerplate written correctly without handing design
decisions to something they cannot inspect.

**There is no AI in the product.** No prompting, no language model, no
generation you cannot predict. Every output is a deterministic function of the
options you chose: the same options always produce byte-identical files. AI is
planned only as a later assistant layer *over* these flows, and never as the
source of truth for generated code.

## What you get

Ask for an IP block and you get seven files, not one. This is the part worth
understanding before anything else:

| File | Kind | What it is for |
|---|---|---|
| `<name>.sv` / `.v` | RTL | The design. Lint-clean under `verilator -Wall`, zero warnings. |
| `<name>.md` | Doc | Datasheet: port tables grouped by function, the register map field by field, bus interfaces, a timing diagram, and the block's stated limitations. |
| `<name>_tb.sv` | TB | A directed SystemVerilog testbench that drives real stimulus and checks real values. It runs in CI. |
| `test_<name>.py` | TB | The same testbench as cocotb (beta), for a Python-based flow. |
| `<name>_checks.sv` | TB | Monitors and checkers, attached to the design with SystemVerilog `bind` — no testbench edit needed, and reusable in your own bench. |
| `<name>_example.sv` / `.v` | RTL | A worked instantiation with every port connected. Compiled and linted against the block itself, so it cannot drift. |
| `<name>_testplan.md` | Doc | What the testbench covers, and — honestly — what it does not. |

Simpler catalog items produce fewer files: a snippet is a single fragment, a
module adds a datasheet, testbenches and a test plan.

Everything downloads as a zip, or file by file.

## Catalog

26 items. All of them generate both SystemVerilog and Verilog-2001 unless
noted, and every one is `-Wall` lint-clean in both.

### Snippets

Small, self-contained fragments — the boilerplate you would otherwise retype.

| Item | Description |
|---|---|
| `cdc-synchronizer` | Multi-stage flip-flop synchronizer for crossing an asynchronous signal into a destination clock domain |
| `comparator` | Parameterizable width comparator, signed or unsigned, selectable relational outputs |
| `counter` | Parameterizable binary counter — up/down, enable, saturate or overflow |
| `decoder` | Binary-to-one-hot decoder with configurable width, enable and polarity |
| `demux` | Parameterizable one-to-many combinational demultiplexer |
| `encoder` | Priority or one-hot binary encoder |
| `fsm` | State machine skeleton — enum states, Moore/Mealy, binary/onehot/gray encoding, with `TODO` transition logic for you to fill in |
| `mux` | Parameterizable N-way multiplexer, case or ternary |
| `register` | Parameterizable synchronous register with enable and synchronous clear |
| `shift-register` | Serial-in shift register — left/right, parallel load, serial-out-only mode |

### Modules

Complete, parameterized blocks with a datasheet, a testbench and a test plan.

| Item | Description |
|---|---|
| `clock-divider` | Even-integer clock division, as a 50%-duty clock or a single-cycle enable pulse |
| `debouncer` | Filters a bouncy input with a disagreement counter — a new value is accepted only after holding steady for the full period |
| `edge-detector` | One-cycle pulse on a rising, falling or any transition; per-bit, optionally registered |
| `gray-counter` | Free-running counter with a Gray-coded output, for CDC-safe pointers |
| `lfsr` | Maximal-length Fibonacci LFSR, parallel or serial output |
| `pwm` | Single-channel PWM from a counter compared against a runtime or fixed duty |
| `rr-arbiter` | Round-robin arbiter — one-hot grant, rotating priority, no requester starved |

### IP blocks

Integratable blocks with register maps, bus interfaces and bound verification
scaffolds. The seven AXI blocks share one register-block generator, spliced in
rather than instantiated, so each is a single flat module.

| Item | Description |
|---|---|
| `axil-regblock` | AXI4-Lite target serving a configurable register map — byte-strobe writes; RW/RO/WO/W1C fields; `SLVERR` on unmapped or reserved-bit accesses |
| `axil-gpio` | GPIO controller — per-pin direction, output values, synchronised inputs |
| `axil-uart` | 8N1 UART with a programmable baud divisor and TX/RX state machines |
| `axil-spi` | Full-duplex 8-bit SPI master, programmable divider, manual chip select, CPOL/CPHA fixed at generate time |
| `axil-i2c` | Open-drain I2C master — START/STOP primitives, ACK/NACK, clock stretching |
| `axil-timer` | Prescaled down-counter, one-shot or periodic, maskable level interrupt |
| `axil-intc` | Interrupt controller aggregating edge- or level-triggered sources into one masked request |
| `sync-fifo` | Single-clock FIFO — wrap-bit pointers giving exact full/empty and an occupancy count |
| `sync-ram` | Single-port or simple dual-port synchronous RAM; no reset, for block-RAM inference |

The AXI blocks are marked **beta**: their RTL, testbenches and run gates are
complete, but the AXI4-Lite target is single-outstanding and the interface has
not yet been exercised against a third-party master.

## Why you can trust the output

Generated RTL is easy to produce and hard to believe. This is the evidence
behind it:

- **Every block runs.** Not "compiles" — runs. Each one has a directed
  testbench executed under Verilator in CI, checking real values at real
  cycles.
- **Every run gate has a mutation half.** Alongside the configurations that
  must pass sit deliberately broken generators that must *fail*: byte strobes
  ignored, FIFO flow control removed, a write-1-to-clear dropped. A test suite
  that cannot be shown to fail is decoration, so these prove it can.
- **Zero lint warnings, not few.** Every generated file passes
  `verilator --lint-only -Wall` with nothing suppressed. That constraint shaped
  the designs rather than being papered over.
- **Byte-identical determinism.** The same options give the same bytes, down to
  a fixed timestamp inside the zip. Every file carries a config hash so you can
  prove which options produced it.
- **The timing diagrams come from the executed testbench**, so a diagram cannot
  be wrong while CI is green.
- **The documentation is generated too**, from the same source as the RTL, so
  the datasheet cannot drift away from the design.

## Quickstart

### Backend

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
uv run uvicorn api.main:app --port 8000 --app-dir backend
```

`GET /api/v2/catalog` lists everything; `POST /api/v2/generate` generates it.
Interactive API docs at <http://localhost:8000/docs>.

Verilator is optional but recommended — without it the API still works and
reports lint and simulation as `unavailable` rather than failing.

Configuration: `SEMICRAFT_CORS_ORIGINS` (comma-separated, default
`http://localhost:3000`) sets which browser origins may call the API. Set it if
you serve the frontend from anywhere else.

### Frontend

Requires Node.js and npm.

```bash
cd frontend
npm install
cp .env.example .env.local     # points at http://localhost:8000
npm run dev
```

Then open <http://localhost:3000>.

Leaving `NEXT_PUBLIC_API_BASE` unset runs the UI against built-in demo data —
useful for working on the interface with no backend, and the app displays a
permanent banner saying so. Do not deploy it that way.

### Docker (backend)

The image bundles Python, the backend and Verilator:

```bash
docker build -t semicraft .
docker run -p 8000:8000 semicraft
```

### Windows

Verilator is Linux-first. On a native Windows host there is no binary, so lint
and simulation report `unavailable` and everything else works normally. Use WSL
or the Docker image for real lint results.

## Documentation

- [`docs/IPS.md`](docs/IPS.md) — the IP contract: register maps, port bundles,
  and how to add a block.
- [`docs/IR_SPEC.md`](docs/IR_SPEC.md) — the language-neutral IR that
  generators build and renderers walk to emit SystemVerilog or Verilog.
- [`docs/STYLE_GUIDE.md`](docs/STYLE_GUIDE.md) — the RTL style all output
  follows: naming, reset idioms, always-block rules, file headers.
- [`docs/TB_SPEC.md`](docs/TB_SPEC.md) — the testbench contract.
- [`docs/CHECKERS.md`](docs/CHECKERS.md) and
  [`docs/ASSERTIONS.md`](docs/ASSERTIONS.md) — the verification artifacts.
- [`docs/COCOTB.md`](docs/COCOTB.md) — the cocotb backend (beta).
- [`docs/TESTPLAN.md`](docs/TESTPLAN.md) — how test plans are derived.
- [`docs/LAUNCH_READINESS.md`](docs/LAUNCH_READINESS.md) — an honest review of
  what is and is not ready.
- [`SemiCraft_PRD.md`](SemiCraft_PRD.md) — product scope and locked decisions.

## What SemiCraft does not do

Stated plainly, because a generator that overclaims is worse than one that does
less:

- **It is not a signoff tool.** No production, timing-closure or silicon
  correctness claim. Review and simulate the output in your own flow.
- **No subsystem generation yet** — no multi-IP top level, address decode or
  interconnect. That is the next phase.
- **No external IP import**, no IP-XACT ingest.
- **No VHDL.** An explicit non-goal.
- **No UVM.** The generated verification is directed, not constrained-random.
- **No AI or natural-language generation**, by design.

Known gaps at this release, with reasons, are listed in
[`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md) — including the
asynchronous FIFO and ROM, both deliberately withheld rather than shipped
unverified.

## License and Disclaimer

Two separate things are licensed here, and they are licensed differently.
Read both lines before using either.

### The generated output — yours, unencumbered

**SemiCraft claims no rights over the RTL, testbenches, or documentation it
generates for you.** Use it however you like, including commercially, in
proprietary and closed-source designs, with no attribution, no notice file,
and no obligation of any kind back to this project. Generated output is *not*
a derivative work of SemiCraft for licensing purposes, and the MIT terms below
do not attach to it.

It is provided **as-is with no warranty** — use it at your own risk. Every
generated file header stamps that disclaimer alongside the tool version and a
config hash (single-sourced from `backend/semicraft_core/license.py`,
`DISCLAIMER`):

> Generated code is provided as-is, without warranty of any kind. Free for
> commercial and non-commercial use at the user's own risk.

SemiCraft is a generator, not a signoff tool. It makes no production, timing
closure, or silicon correctness claim. **Review, simulate, and lint generated
RTL against your own flow before committing it to a design.** The lint gate,
the run gates, and the generated verification artifacts are evidence, not a
substitute for your own verification.

### SemiCraft itself — MIT

This repository is licensed under the **MIT License** — see
[`LICENSE`](LICENSE). Copy it, fork it, embed it in a commercial product; keep
the copyright notice.

## Roadmap

Shipped: snippets, parameterized modules, the verification stack (testbenches,
assertions, checkers, test plans, a sim sandbox), and the IP library.

Next: **subsystem generation** — connected IP, address maps and top-level
wiring — then external IP integration, application scaffolds, and finally an AI
assistant layer over the deterministic flows beneath it. See
[`SemiCraft_PRD.md`](SemiCraft_PRD.md) §12 for the full breakdown.
