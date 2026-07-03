# SemiCraft Product Requirements Document

## 1. Product Overview

SemiCraft is an engineering productivity platform for generating RTL, verification artifacts, subsystem scaffolds, IP integrations, and application/reference design starting points from structured user inputs.

The product is intended for engineers who understand their design requirements and architecture, but want to reduce the time spent writing repetitive boilerplate RTL, testbenches, wrappers, integration files, and basic validation scaffolds.

SemiCraft will begin as a deterministic, option-driven generation platform. AI will be introduced later as an assistant layer that drives, explains, recommends, and optimizes the existing SemiCraft flows. AI is not part of the initial MVP and is not the source of truth for generated output.

## 2. Problem Statement

Digital design and verification engineers frequently spend time creating repetitive design artifacts such as RTL snippets, module shells, parameterized blocks, testbenches, wrappers, address maps, filelists, and integration scaffolds.

This slows down early implementation, increases the chance of small but costly mistakes, and creates duplicated effort across projects. Engineers need a faster way to kick-start design work while keeping generated artifacts structured, reviewable, configurable, and validation-friendly.

## 3. Product Goal

SemiCraft helps engineers kick-start RTL, verification, subsystem, IP integration, and application development by generating clean, configurable, and reusable engineering artifacts from selected options and structured requirements.

## 4. Target Users

- RTL design engineers
- Verification engineers
- FPGA developers
- ASIC/SoC engineers
- Students and early-career engineers learning reusable RTL and verification patterns
- Engineers building portfolio-quality digital design projects

## 5. Core Product Principles

- Deterministic generation first
- Verification early
- Structured inputs before natural language
- Reviewable output over black-box automation
- Templates, metadata, and validation rules as source of truth
- AI as a later assistant layer, not the foundation
- Incremental releases with useful output at every phase

## 6. MVP Scope

### 6.1 MVP Name

RTL Snippet Generator

### 6.2 MVP Objective

Allow users to generate common RTL code snippets from selected options without using natural language input or AI.

### 6.3 MVP User Flow

1. User selects artifact type: RTL snippet.
2. User selects snippet category.
3. User configures available options.
4. SemiCraft generates RTL code.
5. User previews, copies, or downloads the snippet.
6. User can optionally view explanation, assumptions, and validation notes.

### 6.4 MVP Supported Snippet Categories

- Counter
- Register
- Shift register
- Mux
- Demux
- Encoder
- Decoder
- Comparator
- 2-flip-flop CDC synchronizer
- Simple FSM template (state list input, binary/onehot/gray encoding, Moore/Mealy)

### 6.5 MVP Configuration Options

- HDL language: SystemVerilog (default), Verilog
- Data width
- Reset style: synchronous, asynchronous
- Reset polarity: active-high, active-low
- Enable signal: enabled, disabled
- Clocked or combinational behavior, where applicable
- Naming style
- Comment verbosity
- Include module wrapper: yes/no

### 6.6 MVP Outputs

- Generated RTL snippet
- Optional complete module wrapper
- Copy-to-clipboard output
- Downloadable `.v` or `.sv` file
- Basic explanation of selected configuration
- Assumptions and limitations for the generated snippet

### 6.7 MVP Non-Goals

- No natural language prompt-based generation
- No AI integration
- No full subsystem generation
- No external IP import
- No full simulation environment
- No UVM generation
- No production signoff claims
- No timing closure or synthesis optimization
- No VHDL support (explicit non-goal)

## 7. User Stories

### MVP User Stories

- As an RTL engineer, I want to generate a counter snippet with my preferred reset, enable, and width options so that I can avoid rewriting common boilerplate.
- As an FPGA developer, I want to quickly generate common combinational snippets so that I can paste them into an existing design.
- As a student, I want to see the explanation and assumptions for generated RTL so that I can understand the design pattern.
- As a verification-minded engineer, I want the generated snippet to follow predictable coding rules so that I can trust and review it easily.
- As a user, I want to copy or download generated code so that I can move it into my project immediately.

### Future User Stories

- As an RTL engineer, I want to generate a complete reusable module from parameters so that I can start from a clean module shell instead of a blank file.
- As a verification engineer, I want SemiCraft to generate a testbench and assertions for a supported module so that I can begin validation faster.
- As a subsystem designer, I want to generate a register-mapped peripheral subsystem so that I can start from connected RTL, address maps, wrappers, and test scaffolds.
- As an integration engineer, I want to import existing IP metadata and generate wrappers or glue logic so that I can reduce manual integration errors.
- As an application developer, I want to generate a reference design scaffold for a known use case so that I can start from a working project structure.
- As a future AI-assisted user, I want AI to recommend SemiCraft options and templates so that I can configure deterministic flows faster.

## 8. Functional Requirements

### 8.1 Snippet Selection

The product shall allow users to select from a list of supported RTL snippet categories.

Each snippet category shall expose only the configuration options relevant to that snippet.

### 8.2 Option-Driven Generation

The product shall generate RTL based on structured user selections.

The generator shall produce deterministic output for a given configuration.

The generator shall avoid hidden behavior that is not reflected in the selected options or documented assumptions.

### 8.3 Code Preview

The product shall show generated RTL in a readable code preview area.

The code preview should support syntax highlighting.

The user shall be able to copy generated code.

The user shall be able to download generated code as a file.

### 8.4 Explanation and Assumptions

The product shall display a short explanation of the generated snippet.

The explanation shall describe:

- Purpose of the snippet
- Selected configuration
- Important signals
- Reset and enable behavior
- Known limitations

### 8.5 Early Validation

The MVP should include lightweight validation where feasible.

Validation shall include:

- Required option checks
- Naming checks
- Server-side lint of every generated snippet via `verilator --lint-only -Wall`, with a lint-clean indicator in the UI
- Internal generator regression tests

Full simulation is not required for the first MVP, but the generation architecture should allow simulation support in a later phase (Verilator-based, sandboxed).

## 9. UX Requirements

- The MVP should open directly into the generator experience.
- The interface should be simple, engineering-focused, and fast to operate.
- Configuration should use dropdowns, toggles, checkboxes, segmented controls, and numeric inputs.
- The code preview should remain visible while users adjust options.
- Generated output should update predictably when options change.
- The product should not present AI or natural language as the primary interaction in MVP.

## 10. Technical Requirements

### 10.1 Generator Architecture

The generation engine should separate:

- Template definitions
- User configuration schema
- Validation rules
- Code rendering
- Output metadata
- Tests for generated output

### 10.2 Template Requirements

Each generator template should define:

- Supported language
- Required options
- Optional settings
- Default values
- Generated files
- Explanation metadata
- Limitations
- Validation expectations

### 10.3 Validation Requirements

The codebase should include regression tests for supported generators.

For each supported snippet, tests should verify:

- Output is generated successfully
- Required signals are present
- Selected options affect output correctly
- No unsupported combination silently produces invalid code

### 10.4 Extensibility

The product architecture should make it straightforward to add new snippet categories, module generators, verification artifacts, IP templates, and subsystem flows without rewriting the core generator.

## 11. Release Criteria

### MVP Release Criteria

- The product supports at least 8 RTL snippet categories.
- Each supported snippet exposes structured configuration options.
- Each supported snippet can generate Verilog or SystemVerilog output, unless explicitly documented otherwise.
- Generated output can be copied and downloaded.
- Each supported snippet includes explanation and assumptions.
- Generator regression tests exist for each supported snippet category.
- Invalid option combinations are blocked or clearly reported.
- The MVP contains no natural language or AI-based generation flow.

### Post-MVP Release Criteria

- Module generation shall not be considered ready until generated modules have basic validation coverage.
- Verification artifact generation shall not be considered ready until generated testbenches can run against at least one supported module family.
- Subsystem generation shall not be considered ready until generated top-level wiring, address maps, and filelists are internally consistent.
- External IP integration shall not be considered ready until IP metadata, port mapping, parameter mapping, and generated wrappers can be reviewed by the user.
- AI assistance shall not be considered ready until it can operate through existing SemiCraft configuration schemas and produce reviewable suggestions.

## 12. Roadmap

### Phase 1: RTL Snippet Generator

Build the first deterministic option-based generator for common RTL snippets.

Key capabilities:

- Snippet selection
- Configurable options
- Verilog/SystemVerilog output
- Code preview
- Copy/download
- Explanation and assumptions
- Internal generator regression tests

### Phase 2: RTL Module Generator and Early Validation

Expand from snippets to complete reusable modules.

Key capabilities:

- Full module generation
- Parameterized modules
- Port/interface generation
- Coding style options
- Basic syntax checks
- Basic lint checks
- Simple generated testbenches for supported modules
- Generator regression suite

### Phase 3: Verification Artifact Generator

Make verification a first-class product capability.

Key capabilities:

- Directed testbench templates
- Assertion templates
- Checkers
- Monitors
- Simple scoreboards
- Test plan/checklist generation
- Simulation script generation
- Initial Icarus Verilog or Verilator integration

### Phase 4: IP Block Library and Reusable Design Blocks

Create a curated SemiCraft IP and reusable block library.

Key capabilities:

- FIFO
- RAM/ROM
- UART
- SPI
- I2C
- AXI-Lite register block
- Timer
- Basic interrupt controller
- Configuration-driven IP generation
- Example instantiations
- Documentation per IP
- Verification scaffold per IP

### Phase 5: Subsystem Generator

Generate connected groups of modules and IP blocks.

Key capabilities:

- Register-mapped peripheral subsystem
- UART/SPI/I2C subsystem
- Memory-mapped control subsystem
- Simple data-path subsystem
- Clock/reset wiring
- Address map generation
- Module instantiation
- Interconnect glue logic
- Top-level wrapper
- Subsystem-level testbench
- Subsystem documentation

### Phase 6: External IP Integration

Support integration of user-provided or third-party IP into generated subsystems.

Key capabilities:

- User-provided IP metadata capture
- Port mapping
- Parameter mapping
- Interface mapping
- Wrapper generation
- Adapter/glue logic generation
- Clock/reset declaration
- Address map integration
- Filelist/dependency generation
- Integration checklist
- Simulation scaffold

### Phase 7: Application and Reference Design Generator

Generate larger application-level starting points around real design use cases.

Key capabilities:

- Complete reference design scaffolds
- Peripheral controller application
- Sensor interface pipeline
- Memory-mapped accelerator shell
- Streaming datapath example
- Verification environment scaffold
- Documentation package
- Build and simulation scripts
- Reusable project structure

### Phase 8: AI-Assisted SemiCraft

Introduce AI as an assistant layer over the existing deterministic flows.

AI capabilities may include:

- Recommend snippets, modules, and IP blocks
- Convert rough requirements into SemiCraft option selections
- Explain generated RTL and verification files
- Suggest missing verification cases
- Review subsystem configuration
- Help map external IP ports
- Generate documentation from SemiCraft metadata
- Guide users through application generation

AI shall use existing SemiCraft templates, metadata, validation rules, and supported flows. AI-generated suggestions should be reviewable before they affect generated output.

## 13. Success Metrics

### MVP Success Metrics

- User can generate a supported RTL snippet in under 1 minute.
- Generated output is deterministic for the same configuration.
- Supported snippets include explanation and assumptions.
- At least 8 common snippet categories are supported.
- Generator tests cover all supported snippet categories.
- Users can copy or download generated RTL without manual formatting fixes.

### Product Success Metrics

- Reduction in time spent creating common RTL boilerplate.
- Increase in reusable generated artifacts.
- Percentage of generated modules with passing validation checks.
- Number of supported templates/IP blocks.
- Number of generated verification artifacts.
- User retention across repeated engineering workflows.

## 14. Risks and Mitigations

### Risk: Product becomes too broad too early

Mitigation: Keep MVP focused on RTL snippets and defer subsystem, IP, application, and AI capabilities to later phases.

### Risk: Generated RTL is not trusted

Mitigation: Use deterministic templates, clear assumptions, regression tests, and early validation.

### Risk: AI positioning distracts from core product value

Mitigation: Keep AI out of MVP and position it as a later assistant layer.

### Risk: Template complexity grows quickly

Mitigation: Define a consistent generator schema and test structure from the beginning.

### Risk: External IP integration becomes inconsistent

Mitigation: Require metadata capture, explicit port mapping, and generated integration checklists.

## 15. Decisions (formerly Open Questions)

- **HDL languages:** Both Verilog and SystemVerilog, rendered from a shared internal template IR. SystemVerilog is the default; the user can select Verilog.
- **MVP snippet categories:** Counter, Register, Shift register, Mux, Demux, Encoder, Decoder, Comparator, Simple FSM template (hero snippet: state list input, encoding choice binary/onehot/gray, Moore/Mealy), and a 2-flip-flop CDC Synchronizer (replaces "simple arithmetic block" — higher value, error-prone by hand).
- **Module wrappers:** Optional, enabled by default. A snippet-only mode supports pasting into existing designs.
- **Frontend:** React/Next.js web application with the Monaco editor for code preview and syntax highlighting.
- **Backend:** Python owns the generator engine (Jinja2 templates; cocotb planned for Phase 3 simulation).
- **User-facing validation in MVP:** Yes. Every generated snippet is checked server-side with `verilator --lint-only -Wall`, surfaced as a lint-clean indicator in the UI. Internal generator regression tests also required.
- **Default coding style:** lowercase_snake naming, `_n` suffix for active-low signals, `always_ff`/`always_comb` in SystemVerilog. Style is published as a document. Users can override style options (e.g., alternate naming conventions such as kebab-case where legal).
- **IP library format:** No custom format. Adopt an IP-XACT-aligned JSON subset from the start to avoid migration pain in Phase 6.
- **Simulator:** Verilator (strong SystemVerilog support, `--lint-only` for fast stateless MVP linting, sandboxed compile+run for Phase 3). Generated testbenches use Verilator-compatible, cycle-based style. Icarus Verilog not used.
- **Licensing:** Generated code is free for commercial use, provided as-is with no guarantee or warranty; use at the user's own risk. Each generated file carries a license/disclaimer stamp.
- **Monetization:** None at launch. A "buy me a coffee" style option may be added later.
- **Positioning:** Vendor-neutral and verification-first. Vendor-specific generation (e.g., Vivado, Quartus flows) planned as a later capability.
- **VHDL:** Explicit non-goal. Not planned.
