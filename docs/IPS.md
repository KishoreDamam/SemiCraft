# SemiCraft IP Contract (`IpDef`)

**Phase 4, P4-01.** Owner: `semicraft_core/ips/`. Frozen contract:
[PLAN-semicraft-phases-2-8.md](PLAN-semicraft-phases-2-8.md) Appendix B.

An **IP** is a [`ModuleDef`](../backend/semicraft_core/modules/contract.py)
plus the two things that make a block integratable rather than merely
generatable:

| Method | Returns | For |
|---|---|---|
| `register_map(opts)` | `RegisterMap \| None` | the software-visible address/field layout |
| `bundles(opts)` | `list[PortBundle]` | which flat ports form which protocol port |

Everything else — `generate`, `explain`, `port_groups`, `tb_spec` — is
identical to a module. That is the design: because `IpDef` is a strict
superset, an IP goes through the **unchanged** Phase-2/Phase-3 pipeline
(render, lint, datasheet, smoke TB, SVA, test plan, cocotb, goldens) with no
per-IP special-casing. `generate_files` treats `kind in ("module", "ip")`
identically and only appends two datasheet sections for an IP.

## Writing an IP

Drop a file into `semicraft_core/ips/` exporting a module-level instance with
`kind = "ip"`. The registry discovers it with no edit anywhere — the same
mechanism snippets and modules use. Helper modules in that package
(`contract`, `regmap`, `bundles`, `doc`) are skipped by name, per package.

A worked example that exercises every part of the contract lives in
`backend/tests/ips/reference_ip.py`.

## Register maps

```python
RegisterMap(
    name="CSR", data_width=32, addr_width=4,
    registers=[
        Register(name="CTRL", offset=0x0, description="Control register.", fields=[
            RegisterField(name="enable", lsb=0, width=1, access="rw", reset=1),
            RegisterField(name="mode",   lsb=1, width=2, access="rw", reset=0),
        ]),
    ],
)
```

**A register has no width of its own.** It is exactly `data_width` bits — the
bus word. Giving registers an independent width would create a second source
of truth for address arithmetic to reconcile. Bits no field covers are
reserved: they read as zero and ignore writes.

`access` is one of `rw` (read/write), `ro` (hardware-driven, writes ignored),
`wo` (reads return zero), `w1c` (hardware sets, software clears by writing 1).

Validation (rules R1–R6, enforced at construction — see `ips/regmap.py`):

- register names `UPPER_SNAKE_CASE`, field names `lower_snake_case`;
- names unique within their scope;
- fields listed in **ascending, non-overlapping** `lsb` order;
- a field's `reset` fits its `width`;
- `data_width ∈ {8, 16, 32, 64}`, and every field fits the word;
- offsets **strictly ascending**, aligned to `data_width // 8`, and inside
  `2**addr_width` bytes.

Ascending order is required rather than silently sorted: an out-of-order map
is far more likely a copy-paste slip than a deliberate choice, and sorting it
away would hide that. It also makes documentation order a property of the
source rather than of the renderer.

Derived values P4-02's generator consumes: `RegisterField.mask` / `.msb` /
`.bit_range`, `Register.reset_value()` / `.read_reset_value()` (the latter
zeroes `wo` fields, as software sees them) / `.reserved_mask(width)`,
`RegisterMap.stride_bytes` / `.span_bytes()` / `.register()` / `.at_offset()`.

## Port bundles

```python
PortBundle(
    name="s_csr", protocol="native-csr", role="target",
    clock="clk", reset="rst",
    ports=[BundlePort(signal="addr", role_name="addr"), ...],
)
```

**Bundles are metadata over flat ports — no SystemVerilog `interface` is
emitted.** The generated RTL declares `awvalid`, `awready`, … individually,
exactly as before; the bundle only declares which of them belong together and
what each one's protocol role is. This keeps the output Verilog-compatible,
leaves lint and golden behaviour untouched, and defers the
`interface`/`modport` question until something needs it.

Three rules worth knowing before you write one:

1. **`role_name` is protocol vocabulary, not an RTL identifier.** It is never
   restyled. Two IPs with different port prefixes must still agree that
   `awvalid` is `awvalid` — that matching is the whole point of bundles.
2. **`signal`, `clock` and `reset` are canonical names.** They are restyled
   through `render.style.build_name_map` before anything displays them
   (`restyle_bundles`), so an active-low reset declared `rst` is documented as
   the `rst_n` the RTL actually emits. This is the same correction
   `assertions/restyle.py` makes, and for the same reason.
3. **Clocks and resets are referenced, not owned.** They are not members of
   `ports`, so several bundles can share a clock domain while a port still
   belongs to at most one bundle.

There is deliberately no direction field: the IR module already declares one,
and a second source of truth could disagree with it. Consumers resolve
direction from the module.

## The cross-check

`check_bundles_against_module(module, bundles)` runs inside `generate_files`
for every IP, before anything is rendered from the bundles:

- **B1** bundle names unique within the IP;
- **B2** every member `signal` is a real port of the generated module;
- **B3** a port belongs to at most one bundle;
- **B4** every `clock`/`reset` referenced is a real port too.

A violation raises `IpContractError` (a generator bug → HTTP 500), naming the
bundle, the signal, and the ports that *do* exist. This exists because the
realistic failure mode is an option removing a port and leaving its bundle
entry behind — valid in one configuration, broken in another, and invisible to
a defaults-only test suite.

## Verification

An IP inherits `tb_spec`, so it gets a directed smoke TB and SVA exactly like
a module. The P3-06 checker/monitor/scoreboard scaffolds are **not** attached
yet: they need real handshakes and transactions to be worth anything, which is
what P4-09 wires up once the FIFO/UART/SPI/I2C IPs exist. The evidence for
that deferral is in [PROGRESS.md](PROGRESS.md).

## The AXI4-Lite register block (P4-02)

`axil-regblock` is the first shipped IP and the keystone the protocol IPs
reuse. The protocol logic lives in `semicraft_core/ips/regblock.py` as a plain
function over any register map:

```python
build_axil_regblock(name, regmap, sync_reset=True, description="") -> Module
```

A UART or SPI IP calls that with its own map rather than inheriting from the
catalog entry — which is why the engine is a function and not a subclass.

**Protocol shape.** A single-outstanding target. AW and W are captured
independently (AXI permits either first); `awready`/`wready` are
`!captured && !bvalid`, functions of registers only, so there is no
combinational valid→ready path — an AXI violation and a classic deadlock
source. Reads are registered: `arready = !rvalid`, and the addressed word is
captured on the AR handshake.

**Three decisions that differ from a textbook target**, each because this
project lints every generated file with `verilator --lint-only -Wall` and
treats any warning as a failure. A module that declares inputs it never reads
does not pass, and a lint pragma would blind the gate to real unused-signal
bugs — so the design uses every bit it declares:

1. **No `awprot`/`arprot`.** The block enforces no protection policy, so those
   inputs would be dead. An interconnect that drives them leaves them
   unconnected.
2. **The full byte address is decoded**, not just the word index. An access
   with non-zero low offset bits returns `SLVERR` instead of silently aliasing
   onto the containing word.
3. **Reserved bits must be written as zero.** A write trying to set a bit the
   addressed register does not implement is rejected with `SLVERR` and
   performs no update. This is standard "SBZ" doctrine made enforceable, and
   it is what lets every `wdata`/`wstrb` bit be genuinely used no matter how
   sparse the map is.

The check is layered to avoid a combinational loop: `wr_addr_<reg>` decodes the
address only, that selects the reserved mask, and `wr_sel_<reg>` — the field
write-enable — is `wr_addr_<reg> && !wr_reserved`.

**Access-type behaviour**, all exercised by the run gate:

| Access | Storage | Hardware port | Read returns |
|---|---|---|---|
| `rw` | yes | output | stored value |
| `ro` | no | input | the input |
| `wo` | yes | output | **zero** |
| `w1c` | yes | output + `<field>_set` input | stored value |

For `w1c`, a hardware set arriving in the same cycle as a software clear
**wins**, so an event is never silently lost.

**Byte strobes are exact**: `wstrb` expands to a bit mask and each writable
field updates as `(wdata & mask) | (field & ~mask)` over its own range, so a
partial write leaves untouched bytes of a multi-byte field alone.

**Why the options are counts.** The obvious design — let the user declare
registers and fields — is not reachable from the UI: the option form is
JSON-Schema-driven and has no widget for an array of objects. So the catalog
entry takes *how many* registers of each access type it should have and builds
the map itself. Arbitrary maps stay a first-class capability of the engine,
which is what the protocol IPs use.

**The run gate can fail.** `backend/tests/ips/test_axil_regblock_run.py` runs
the generated testbench across nine configurations, then deliberately breaks
the generator four ways — strobes ignored, write-only fields leaking on read,
the `w1c` set dropped, the reserved-bit check disabled — and asserts the suite
notices each one. A transaction sequence over a bus protocol is exactly the
kind of test that can look thorough while proving nothing.

## Current state

`by_kind("ip")` ships `axil-regblock`. P4-03..P4-08 add FIFO, RAM/ROM, UART,
SPI, I2C, timer and interrupt-controller IPs; the protocol ones use the
register block above as their bus frontend.
