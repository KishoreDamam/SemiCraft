# SemiCraft

SemiCraft is an engineering productivity platform for generating RTL,
verification artifacts, subsystem scaffolds, IP integrations, and
application/reference-design starting points from structured user inputs. It
targets RTL design and verification engineers, FPGA/ASIC/SoC engineers, and
students who want to skip repetitive boilerplate without handing design
decisions to a black box.

SemiCraft begins as a **deterministic, option-driven generation platform.**
There is no AI, no natural-language prompting, and no AI-based generation
anywhere in the MVP — AI is planned only as a later assistant layer over the
existing deterministic flows (see [Roadmap](#roadmap)), and it is never the
source of truth for generated output.

## MVP: RTL Snippet Generator

The current MVP lets a user pick an RTL snippet category, configure it via a
structured options form (no free text), and get back deterministic,
lint-checked RTL — with an explanation of what was generated and why.

**Supported snippet categories (MVP):**

- Counter
- Register
- Shift register
- Mux
- Demux
- Encoder
- Decoder
- Comparator
- 2-flip-flop CDC synchronizer
- Simple FSM template (state list input, binary/onehot/gray encoding,
  Moore/Mealy)

**MVP features:**

- HDL output: SystemVerilog (default) or Verilog, from one shared internal
  IR — same generator, both languages.
- Common configuration: data width, reset style (sync/async), reset polarity
  (active-high/active-low), enable signal, clocked vs. combinational
  behavior where applicable, naming style, comment verbosity, and optional
  module wrapper (fragment mode when disabled).
- Live code preview (Monaco editor), copy-to-clipboard, and download as
  `.sv`/`.v`.
- Explanation panel: purpose, selected configuration, signal descriptions,
  reset/enable behavior, assumptions, and limitations for every generated
  snippet.
- Server-side lint via `verilator --lint-only -Wall` on every generated
  snippet, surfaced as a lint-clean indicator in the UI.
- Deterministic generation: the same options always produce byte-identical
  output, and internal generator regression tests cover every snippet
  category.
- Explicitly **not** in the MVP: natural-language generation, AI, full
  subsystem generation, external IP import, full simulation, UVM, VHDL, and
  no production/signoff or timing-closure claims.

## Quickstart

### Backend (API)

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
uv run uvicorn api.main:app --reload
```

The API serves `GET /api/v1/snippets` (catalog) and `POST /api/v1/generate`
(generate a snippet). See `docs/IMPLEMENTATION_PLAN.md` §4 for the full
contract.

### Backend (Docker)

The Docker image bundles Python, the backend, and Verilator (needed for the
lint gate):

```bash
docker build -t semicraft .
docker run -p 8000:8000 semicraft
```

> **Windows note:** Verilator is Linux-first. On native Windows dev
> environments there is no Verilator binary, so lint reports come back as
> `status: "unavailable"` (the API and UI remain fully usable without it).
> To exercise real lint results on Windows, run the backend inside the
> Docker image or WSL rather than natively.

### Frontend

Requires Node.js and npm.

```bash
cd frontend
npm install
npm run dev
```

The frontend is a Next.js (App Router, TypeScript) single-page generator UI:
snippet picker + dynamic options form on the left, live Monaco preview on the
right. It can run against a mock API layer before the backend is available;
see `frontend/mocks/`.

## Architecture

- [`docs/IR_SPEC.md`](docs/IR_SPEC.md) — the language-neutral intermediate
  representation (IR) generators build and renderers walk to emit
  SystemVerilog or Verilog, including the reset-composition and
  reset/rendering tables.
- [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) — repository
  layout, frozen snippet/API contracts, and the work-package breakdown used
  to build the MVP.
- [`docs/STYLE_GUIDE.md`](docs/STYLE_GUIDE.md) — the published SemiCraft
  default RTL style (naming, reset idioms, always-block rules, formatting,
  comments, file headers) that all generated output follows.

## License and Disclaimer

Generated RTL is free to use, including commercially, and is provided
**as-is with no warranty of any kind** — use it at your own risk. Every
generated file header stamps this disclaimer alongside the tool version and
a config hash (see `backend/semicraft_core/license.py`, `DISCLAIMER`):

> Generated code is provided as-is, without warranty of any kind. Free for
> commercial and non-commercial use at the user's own risk.

This disclaimer covers generated *output* only; SemiCraft itself (this
repository) is licensed separately (see repository license, if/when added).

## Roadmap

Phase 1 (this MVP) is RTL snippets. The plan beyond that is: full
parameterized **modules** with early validation, then a **verification**
artifact generator (testbenches, assertions, checkers), then a curated
**IP library** (FIFO, RAM/ROM, UART, SPI, I2C, AXI-Lite, timer, interrupt
controller), then **subsystem** generation (connected IP + address maps +
top-level wiring), external IP integration, application/reference-design
scaffolds, and finally an AI assistant layer over all of the above. See
`SemiCraft_PRD.md` §12 for the full phase-by-phase breakdown.
