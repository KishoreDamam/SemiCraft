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

## Current state

`by_kind("ip")` is empty. P4-01 ships the contract; P4-02's AXI4-Lite register
block is the first real IP, and the register-map model above is what drives it.
