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

## The synchronous FIFO (P4-03a)

`sync-fifo` is the second shipped IP, and it exists partly to exercise the two
`IpDef` branches the register block could not:

- **`register_map` returns `None`** — a datapath IP is not forced to invent
  software-visible registers, and its datasheet simply has no register-map
  section.
- **Two bundles share one clock** (`wr` and `rd`). That is the case the
  "clocks are referenced, not owned" rule exists for: a port belongs to at
  most one bundle, so a member clock would make a two-port IP illegal.

It is also the **first consumer of the IR `Memory` node**, which had been
spec'd (IR_SPEC §10.2) and unit-tested since IR v0.2 without any generator
emitting one.

**Pointer scheme.** Depth is a power of two and both pointers carry one extra
most-significant bit:

```
empty = wptr == rptr
full  = wptr[AW] != rptr[AW] && wptr[AW-1:0] == rptr[AW-1:0]
count = wptr - rptr                       // exact, 0..DEPTH
```

The wrap bit is what makes `count` correct across a wrap with no saturating
logic. A non-power-of-two depth is rejected at validation with the two nearest
legal values, because the comparison is only exact for a power of two.

**Reads are registered** — `rd_data` is valid the cycle after an accepted
`rd_en`. There is no first-word-fall-through option: FWFT is a different read
contract, not a flag, and offering both behind one boolean yields a datasheet
that describes neither exactly. Overflow and underflow are ignored silently.

**The testbench stays small at any depth.** The fill and drain phases hold
their enable for a single driven cycle and then idle, which `generate_tb`
coalesces into one `repeat (N)` — a 1024-deep FIFO's testbench is under 400
lines. A test pins that, because the clock divider once produced a 65k-line
testbench that timed out the compile gate.

The run gate has the same mutation half as the register block's: flow control
removed, read index wrong, `full` stuck low, `empty` stuck low. A FIFO test
that only pushes a few words and pops them back never touches the two things
that actually make a FIFO correct — boundary flow control and ordering.

## The synchronous RAM (P4-04)

`sync-ram` is single-port or simple dual-port, over the same `Memory` node.
Two decisions are worth knowing before you instantiate it:

**It has no reset at all.** Storage must not be cleared — clearing a deep
memory costs a great deal of logic for no observable behaviour — and resetting
*only* the output register is what most often blocks block-RAM inference in
FPGA synthesis. So the module has a bare clock, and its options extend
`CommonOptions` rather than `ClockedOptions`. The consequence is real and
documented: `dout` holds no defined value until the first completed read (X in
a four-state simulator, zero in Verilator), and the generated testbench never
checks it before one.

**Read-during-write returns OLD data.** Both accesses are non-blocking
assignments in one clocked process:

```systemverilog
if (we) mem[waddr] <= din;
if (re) dout <= mem[raddr];
```

so reading the address being written in the same cycle yields what was already
there — READ_FIRST. This is the one behaviour of a RAM that nothing in the
port list reveals, so the testbench pins it with a directed check, and the run
gate includes a **write-first mutation** that must fail. A generator that got
this wrong would compile, lint clean, and pass any testbench that keeps writes
and reads on separate cycles.

Bundle layout follows the port mode: single-port is *one* bundle, because
`addr` is shared and a port may belong to at most one bundle; simple dual-port
splits into `wr` and `rd`.

## Composing a peripheral onto the register block (P4-05a)

Every protocol IP is its own logic plus a register frontend. The mechanism is
a flag on the generator:

```python
core = build_axil_regblock(name, regmap, field_ports=False)
Module(ports=[*core.ports, *my_pins], items=[*core.items, *my_logic])
```

With `field_ports=False` the hardware face is emitted as **internal signals**
instead of ports, and only the clock, reset and AXI signals stay ports. The
peripheral appends its own pins and logic and gets **one flat module** — no
submodule instantiation, so no extra file and no port-mapping to keep in sync.

Two obligations come with it:

- **Use every field you declare.** An unused signal is a `-Wall` failure, and
  the lint gate requires zero warnings.
- **Drive the read-only fields.** The register block reads them; nothing else
  will.

`AxilSequencer` and `RegisterModel` live in `regblock.py` alongside the
generator whose timing they encode, so a composed IP's testbench describes the
AXI handshake in exactly one place and cannot drift from the standalone
block's.

`axil-gpio` is the first IP built this way — deliberately the simplest
peripheral that exercises the mechanism, so the splice was proved before a
baud-rate generator was sitting on top of it.

## The AXI4-Lite GPIO (P4-05a)

Three registers — `DIR`, `OUT`, `IN` — driving `gpio_oe`, `gpio_out` and
reading `gpio_in`. Bits above `num_pins` are reserved, so writing one returns
SLVERR: the register block's policy, inherited unchanged.

**Inputs are synchronised, not sampled.** `gpio_in` comes from a pin and is
asynchronous to `aclk`, so it passes through two (configurable) flops before
reaching `IN`. That costs `input_sync_stages` clocks of latency, which the
datasheet states.

Verifying that is subtler than it looks, and worth knowing if you write a
similar testbench. A read of `IN` after the pins settle passes whether or not
the synchroniser exists — so the testbench also reads `IN` while the new value
is still in flight and requires the **old** one. The offset matters: a read
issued in the same cycle as the pin change captures one edge later and reads
old even with no synchroniser at all. Delaying the read by one cycle is what
makes it discriminate, and two mutations pin it — bypassing the synchroniser,
and dropping it to a single stage. A missing metastability guard never shows
up in simulation, so the check has to be timed deliberately rather than
written by feel.

**No bidirectional port.** The IR has no `inout`, so the pad direction is a
separate `gpio_oe` output and the integrator instantiates the tri-state
buffer — which is also what lets the same RTL target FPGA and ASIC flows.

## The AXI4-Lite UART (P4-05b)

`axil-uart` is 8N1 — 8 data bits, no parity, one stop bit — with a
programmable baud divisor, built on the same splice. Two design points are
worth reading before you use it.

**Status flags are write-1-to-clear, not read-to-clear.** The natural UART
idiom is "reading RXDATA clears rx_valid", but the register block's read path
is a mux with no per-register read strobe. Adding one would mean a new access
type and a new signal on every register, for a single user. W1C is something
the block already implements exactly, and it is a real UART interface in its
own right: read RXDATA, then write a 1 to the flag.

**The transmit trigger is the register's write strobe.** A write-only field's
storage holds the byte but cannot say *when* it was written.
`regblock.write_strobe_name("TXDATA")` names the signal that can — high for
exactly one cycle per accepted write. The transmitter delays it by one cycle,
because `txdata_data` only takes the new byte on the same edge the strobe is
sampled; using it immediately would transmit the *previous* byte. That is a
composition-wide lesson, not a UART one: a strobe and the value it refers to
are not available in the same cycle.

**Bit timing** is derived from the FSM and stated in the source: a write at
cycle `c` starts the frame at `c+3`, and bit *k* occupies
`[S + k*div, S + (k+1)*div - 1]`. The testbench checks the line one cycle into
each bit period — away from both edges, so a half-period error shows up
instead of landing on a boundary.

### The mutations that matter here

Every one of these leaves a **well-formed frame** behind, which is why a
"drive a byte in, read a byte out" test is not enough:

- *transmits MSB first* — still ten bits with a start and a stop.
- *samples on bit edges* — the classic UART bug that works in a clean
  testbench and fails on real wire.
- *bit period off by one* — every bit one clock too long.
- *rx_valid never set* — the byte arrives, nothing says so.

The first of those is also why the test bytes are `0x4B` and `0x2D`. The
obvious choices, `0xA5` and `0x3C`, are both **bit-palindromes**: an MSB-first
transmitter would emit an identical frame and the checks would pass against
reversed hardware. A test pins that the chosen byte is not a palindrome.

## The AXI4-Lite SPI master (P4-06)

`axil-spi` is a full-duplex 8-bit MSB-first master. Writing `TXDATA` performs
one exchange — a byte out on `mosi` while a byte comes in on `miso`, because
that is what SPI is; there is no separate read transfer.

**Clock mode is a generate-time option**, not a register bit. A
runtime-selectable mode carries both edge behaviours in hardware forever so a
register can pick one at boot; SemiCraft generates the module a design needs.
CPOL is a single inversion on the way out, so the FSM only ever knows one
polarity — `sclk_int` idles low and leads with a rising edge in every mode.

**Chip select is manual.** `CTRL.cs_assert` drives `cs_n` directly rather than
the transfer pulsing it: multi-byte transactions need it held across several
exchanges, and a master that deasserted between bytes could talk to neither a
flash nor a sensor.

**CPHA changes the receive register's width.** With CPHA=0 the last sample
lands on edge 14 and the byte is complete before the final edge, so all eight
bits live in the register. With CPHA=1 the last sample *is* the final edge and
goes straight into RXDATA — only seven earlier bits are ever re-read, and an
eighth would be written and never used. The `-Wall` gate refuses that, which
is how the asymmetry got noticed rather than shipped as dead flops.

### Two timing lessons from the testbench

Both cost a failing run to learn, and both generalise:

1. **A flag set by peripheral logic is readable one cycle later than the event
   that set it.** The completing edge raises the W1C *set request*; the
   register block latches it in its **own** always block, so the flag crosses a
   clock edge on the way. Collapsing "transfer done" and "status readable" into
   one cycle reads the flag still clear.
2. **Check a level at the first cycle of a half period, not one cycle into
   it.** With a divisor of 1 a half period is a single cycle, so "one cycle in"
   lands in the *next* one — a check that passes at every other divisor and
   fails only at the fastest.

When a per-bit `miso` pattern cannot settle through the synchroniser inside one
half period — a fast clock against a deep synchroniser — the testbench holds
the line at a constant and expects the byte that produces, rather than claiming
a resolution the configuration does not have. A test pins both branches.

## The AXI4-Lite I2C master (P4-07)

`axil-i2c` runs the bus one **primitive at a time** through `CMD` —
optionally a START, then one byte written or read, then optionally a STOP.
That is how a real transaction is assembled, and it keeps the FSM small enough
to reason about.

**Open drain without `inout`.** I2C lines are never driven high: a device pulls
low or releases. The module exposes only `scl_oe`/`sda_oe` (pull low) and
`scl_in`/`sda_in` (sensed level), so a pad is `line = oe ? 1'b0 : 1'bz` and the
wired-AND happens where it really happens — on the wire.

**The bus drivers are continuous functions of registered state**, not
assignments inside the FSM. An I2C bit is four quarter-phases, and writing
"on entering phase 2, release SCL" as sequential code means every transition
carries a bundle of side effects — which is where these state machines go
wrong. As pure functions of registers they still change only just after a
clock edge, and each line's behaviour reads in one place.

**Clock stretching** is real: after releasing SCL the phase counter does not
advance until `scl_in` actually reads high. The testbench stretches
deliberately, and a mutation that ignores stretching must fail.

### Two bugs worth recording

**The quarter counter has to *hold* while stretched, not keep counting.** A
free-running counter wraps all the way round before `q_cnt == div-1` comes true
again, so the master would hang for 2¹⁶ cycles. Only reachable *with*
stretching — which is why the testbench stretches rather than assuming a
cooperative bus.

**A guard named in a function's name is not a guard.** `_sample_at_phase2`
sampled on *every* quarter, so a read shifted in four samples per bit. The
write transaction passed anyway: its only sample is the ACK, and the slave
holds SDA low across all four ACK quarters, so sampling four times gave the
same answer. Only reading a byte back exposed it — and the read transaction
existed at that point only because a lint error (`rxdata` assigned but never
used) pointed out that the docstring promised a read the testbench never did.

## The AXI4-Lite timer (P4-08)

`axil-timer` is a prescaled **down-counter**: `PRESCALE` divides the clock,
`RELOAD` sets the period, `CTRL` runs it one-shot or periodically, and
`STATUS.expired` (W1C) raises a maskable `irq`.

**Why down, not up.** An up-counter compared against `RELOAD` needs a
full-width comparator every clock; a down-counter needs only a zero test,
which is a NOR of the counter bits. The software interface is identical, so
the only visible cost is one documented off-by-one: the period is `RELOAD + 1`
ticks, because the counter visits zero before expiring.

**Disabling reloads, it does not pause.** While `CTRL.enable` is low the
counter is continuously reloaded, so enabling always starts a full period, and
`COUNT` means the same thing regardless of history. Pause-and-resume is a
different device.

**One-shot stops via `running`, not via `enable`.** `CTRL.enable` is an `rw`
field the register block owns and software alone writes — hardware cannot
clear it. A separate `running` flop is what makes a one-shot expiry stay
expired.

**The interrupt is two clocks behind the counter**, and that is composition
cost, not sloppiness: one clock for the register block to sample the W1C set
request, one for the flag to be readable. The testbench derives that latency
from the RTL and the datasheet states it.

### Checking an expiry from both sides

A check for "`irq` high at cycle N" passes for any timer that fired *at or
before* N — so a prescaler that is ignored entirely, or a reload value read one
bit short, sails through. Every expiry here is therefore checked twice: `irq`
low on the cycle before the derived rise, high on it. That pair is what gives
the `prescaler_ignored` and `terminal_off_by_one` mutations something to fail
against.

`always_reload` is the odd one out — it fires at exactly the right moment and
only diverges afterwards, so it is caught by the three idle periods that follow
the one-shot expiry rather than by the expiry itself.

## The AXI4-Lite interrupt controller (P4-08)

`axil-intc` aggregates `num_irq` request lines into one masked output:
`PENDING` (W1C) latches requests, `ENABLE` masks them, `STATUS` is
`PENDING & ENABLE`, and `irq_out` is the OR of `STATUS`.

**The mask gates the output, not the latch.** A request latches whether or not
it is enabled. Masking before the latch would lose a request that arrived while
masked — which is exactly the request software wants to find when it enables
the source later.

**Edge or level is a generate-time choice.** `trigger="level"` latches the
level, so a write-1-to-clear has no lasting effect while the source is still
asserted: the flag re-arms on the same clock the write clears it. That is
correct level behaviour — a level source is deasserted by servicing the device,
which the controller cannot do — and the testbench checks it rather than
trusting the comment.

**The edge history flop sits after the synchroniser.** It is tempting to take
the previous value from the second-to-last synchroniser stage, which already
holds one. That stage is one flop deep from an asynchronous input and can still
be metastable, so feeding it into the comparison puts the hazard straight back
into the latch the synchroniser exists to protect. `irq_hist` is a separate
flop fed from the *last* stage.

### Making a latency bug fail

Taking the request one flop early does not change any *value* in simulation —
simulation has no metastability — only the *latency*. So the sequence issues a
read of `PENDING` on the exact cycle the last synchroniser stage goes high and
requires it to read zero, and a second read two cycles later that requires the
request. `synchroniser_bypassed` and `one_stage_short` both fail on the first
read; without it, dropping the metastability guard on an asynchronous input
would be invisible.

The two trigger modes are caught differently again: every pulse earlier in the
sequence latches identically under edge and level, so `level_instead_of_edge`
and its inverse are caught only by the final section, which holds a source
asserted across a write-1-to-clear.

## Verification scaffolds, bound to the DUT (P4-09)

Every AXI IP now emits a third `tb`-kind file, `<module>_checks.sv`: two
passive monitors and a procedural checker, attached to the DUT with
SystemVerilog `bind`. The generators came from P3-06 and had been sitting
compile-gated and unattached ever since — an artifact that existed, passed its
own tests, and verified nothing.

**`bind`, not a testbench change.** The obvious route is to instantiate each
scaffold from the generated testbench, which means teaching `TbSpec`,
`TbModule` and `render_tb` about a new kind of child instance — a frozen
contract (TB_SPEC) and every consumer of it — so a checker can see nets the DUT
already exposes. `bind` needs none of it: the statement lives in the scaffold's
own file, names the DUT module, and connects to identifiers resolved in the
DUT's scope. The generated testbench is byte-identical with or without a
scaffold, and the file is self-contained enough to drop into someone else's
bench. The cost is that `bind` is SV-only, so a Verilog-2001 build gets no
scaffold — the checks are simulation artifacts, so nothing usable is lost.

**The memory IPs get a scaffold of their own.** `sync-fifo` and `sync-ram`
have no bus, so they get one monitor and one check: read data must not move
while the read enable is low. Both register their read behind an enable
(`if (rd_en && !empty) rd_data <= ...`, `if (re) dout <= ...`), so it is a real
property — and it is what the datasheet already promises ("dout holds when
low"). A RAM built with `read_enable=False` has no gate and therefore no hold
property, so it returns an empty spec and gets **no file**: a scaffold that
checked nothing would be worse than none.

**What it checks, and what it deliberately does not.** Not reset values or
field semantics: the directed testbench and its SVA already cover those, and a
scaffold that re-checks them is bulk, not coverage. It checks the two things a
directed vector sequence structurally cannot:

- **Liveness** — every `awvalid` is followed by `bvalid`, every `arvalid` by
  `rvalid`, within a bounded number of cycles.
- **Read-data stability** — `rdata`/`rresp` do not move on cycles when no read
  was accepted. A directed read samples one cycle and never looks again, so a
  target that spuriously rewrote its read register between transactions is
  invisible to it.

### Proving a checker can fail

Verilator turns `$error` into an implicit `$stop` and aborts non-zero, so a
firing check makes the run gate report `fail`. That is the mechanism; the
mutations are the evidence.

`rdata_churns` is the headline. It corrupts `rdata` on exactly the cycles no
directed read is looking — the read still returns the right word at the cycle
the testbench samples it, and inverts every cycle after. The same broken DUT is
run **twice**, with and without the scaffold: the testbench passes, the
scaffold fails. That pair is the whole argument. A mutation that fails both
ways would only prove the testbench works, which was never in doubt.

**Where the checks do not add power, said plainly.** Two of them do not, and
both are worth recording rather than quietly dropping.

The AXI *liveness* check: SemiCraft's own sequences check the response cycle of
every transaction, so a lost response is caught by the testbench first and the
latency counter never reaches its bound.

The memory *read-hold* check: two separate attempts to find a mutation the
RAM's directed testbench could not see both failed. Deleting the `if (re)` gate
outright is caught because the next cycle's address overwrites the word about
to be sampled. Narrowing it — invert `dout` only while `re` is low, so every
read still returns the right word at the cycle it is sampled — is *also*
caught, because the testbench reads `dout` on a cycle whose previous cycle had
`re` low. That is a hold check, and the testbench deserves the credit.

For both, the value is the file a user reuses in their own, more sparsely
checked bench, and both are proven functional the same way: the gate silences
the testbench's own `$fatal` calls first — turning it into a pure stimulus
generator — so the scaffold is the only thing left that can stop the run.

### The restyling trap, again

An IP's `verification_spec(opts)` never sees the render style, so it speaks
canonical names and they are mapped through the same name map the RTL and
testbench use. This is not an exotic-configuration concern: AXI4-Lite fixes the
reset active-low and `build_name_map` appends `_n`, so `areset` → `areset_n`
happens at the **default** configuration. A scaffold that skipped restyling
would bind to undefined nets out of the box — the same bug P3-05a already found
once in the assertion path, which is why the run gate carries a naming-style
axis rather than trusting that it was remembered.

Only bare identifiers are renamed; `"bvalid && bready"` is left alone, because
renaming inside expression text would mean parsing SystemVerilog.
`check_spec_is_restylable` refuses to ship a catalog spec containing one, so
the limitation is unreachable by accident rather than merely written down.

## Timing diagrams that cannot drift (P4-10)

Every IP datasheet now carries a `## Timing` section: a WaveDrom diagram of
the directed sequence, inline as a ```wavedrom fenced block.

**It is rendered, not drawn.** A timing diagram in a datasheet is the classic
place for documentation to drift away from behaviour — it looks authoritative,
it is authored by hand, and nothing checks it. This project has already fixed
that class of bug twice: a datasheet claiming reserved bits "ignore writes"
while the RTL answered SLVERR, and a generic renderer asserting timing the
model did not own.

So the generator draws nothing of its own. Every waveform comes from the same
`TbSpec` that becomes the smoke testbench — the one Verilator executes against
the real RTL, on every option case of every IP, in CI. The chain closes:

```
diagram  <-  TbSpec.vectors / TbSpec.checks  <-  verified by the run gate
```

If the RTL stops behaving this way the run gate goes red. If the `tb_spec`
recipe changes the diagram changes with it. A diagram cannot be quietly wrong
while the tests are green, which is the only property that makes one worth
printing.

**`x` is information, not a shortcut.** Inputs are fully determined — the
testbench drives them, and a signal absent from a cycle's vector holds its
previous value. Outputs are different: the testbench pins them only on the
cycles it checks. Those cycles are drawn `x` because that is what the testbench
actually knows. The side effect is that the diagram doubles as a picture of
directed coverage: a long `x` run on an output is a stretch of behaviour nobody
is checking, which is better seen in a datasheet than smoothed over with a
plausible-looking line.

**Inline JSON, because the file kind is frozen.** `GeneratedFile.kind` is a
frozen `Literal["rtl", "tb", "doc"]` and a `.json` data file is none of the
three — the same blocker recorded against the ROM's `$readmemh` route. Rather
than widen a frozen contract for a diagram, the JSON goes inline in the
markdown, which is how WaveDrom is embedded in markdown anyway.

**What is *not* verified.** Nothing here renders the diagram to check it looks
right — that needs a JavaScript runtime. What is checked structurally, on every
IP: every wave is the same length (one character short silently misaligns every
cycle after it), every row names a real port, `data` labels match their `=`
slots positionally, only legal wave characters are emitted, and — the one that
matters — every value drawn for an output equals the `Check.expected` at that
cycle. That last test was confirmed to fail against a deliberate one-cycle
misalignment before being kept.

The window is the first 40 directed cycles, which covers reset release and the
first few bus transactions. The serial IPs run for thousands of cycles at their
default divisors; the datasheet says so when it truncates.

## Example instantiations, compiled (P4-11)

Every IP emits `<module>_example.sv` / `.v`: a wrapper that exposes the IP's
ports and instantiates it, with the connections grouped and commented from the
IP's own `port_groups()` and annotated from its `bundles()`.

**A real file, not a fenced block in the datasheet.** A copy-pasteable snippet
with a wrong port name or a stale width is worse than no snippet, because a
reader trusts it — and nothing about generating one into markdown would ever
catch that. The golden gate lints each example `-Wall` clean *against the IP it
instantiates*, at the same zero-warning bar the RTL itself has to clear. Rename
a port and the example stops linting.

It is deliberately **not** an integration example: the wrapper passes every port
straight through, because that is the only shape both derivable from metadata
and lint-clean for every IP. What the file guarantees is that the
instantiation — names, widths, directions, grouping — is correct for that
configuration and compiles today.

The value is the grouping: it says which nineteen signals form one AXI4-Lite
target port and which three are pads, which is what a reader has to work out
before wiring anything.

**A recorded stopgap.** The synthesizable IR has no module-instance node, so
this emits HDL text directly, the way the checker generator does. Phase 5's
subsystem generator needs real instantiation in the IR — wiring groups of IPs
into a top wrapper *is* instantiation as a first-class construct. When that node
lands (an IR_SPEC change, so a recorded decision), this emitter should be
rewritten on top of it rather than left to drift as a second way of writing the
same construct.

## The naming-style bug behind three shipped defects

P4-11's example generator had to resolve every connection to a real net, which
is how it surfaced this: **the datasheet's port table never applied the render
name map.** Under any naming convention, prefix or suffix, every module and
every IP listed ports that do not exist in the generated RTL — shipped since
v0.2.0.

It is the third bug of exactly this shape:

1. **P3-05a** — assertion specs named canonical resets, so `disable iff (!rst)`
   referenced a net rendered `rst_n`.
2. **P4-07** — the testbench clock net was hardcoded `clk`.
3. **P4-11** — datasheet port tables printed declared names verbatim.

The common cause is not carelessness three times over. It is that **no golden
case anywhere set a naming style**, so the entire style axis was invisible to
the goldens: a generator that forgot to restyle produced byte-identical output
at the default configuration, which is all the goldens ever exercised.

The fix is therefore two-part. The datasheet now resolves each declared name
through the map — reusing the reset-suffix convention P3-07's test-plan
generator already documented, where `port_groups()` lists canonical names except
for an active-low reset it suffixes with `_n`. And a **`styled_names` case now
exists on every catalog item**, so the axis is covered by goldens permanently.
Every existing golden was byte-identical after the fix, which is exactly why the
bug survived four releases.

## Current state

`by_kind("ip")` ships `axil-regblock`, `sync-fifo`, `sync-ram`, `axil-gpio`,
`axil-uart`, `axil-spi`, `axil-i2c`, `axil-timer` and `axil-intc` — nine IPs,
which clears the Phase-4 exit bar of eight. All nine carry a bound verification
scaffold (P4-09) — the seven AXI IPs a bus monitor and liveness/stability
checker, `sync-fifo` and `sync-ram` a read-hold checker.

**Still unused: the scoreboard**, one of P3-06's three families. It needs a
model of what the *next* value should be, and for a register block that model
(`RegisterModel`) lives in Python driving the testbench — there is nothing in
the DUT's scope to compare against. The FIFO is where it belongs, since
ordering is the property there, and that is the next place to use it. Saying so
is more useful than shipping a scoreboard that cannot fail.

**Deferred: ROM with defined contents.** P4-04 pairs the RAM with a ROM. A
ROM is only useful if its contents are specified, and there is no way to
express that today: the synthesizable IR has no memory-initialisation
construct (`initial`/`$readmemh` live in the testbench node family, which the
synthesizable validator rejects by design — TB_SPEC §1). The options form also
has no widget for an array of integers, so contents cannot come from options
either. A case-statement lookup works only for tiny depths.

Two viable routes, both needing a recorded IR decision first: an additive
`init_values` on `Memory` rendered as an `initial` block (FPGA-friendly, not
ASIC-portable), or a generated `.hex` file plus `$readmemh` (portable, but
`GeneratedFile.kind` is a frozen Literal and a data file is neither `rtl`,
`tb`, nor `doc`). Picking between them is the first task of that work package,
not something to settle in passing.

**Deferred: the asynchronous (CDC) FIFO.** P4-03 pairs the sync FIFO with a
gray-pointer async FIFO, which is not shipped here. The testbench framework
drives a single clock (`TbSpec.clock`, one `ClockGen` in `TbModule`), so an
async FIFO's defining property — safe transfer between two independent clocks
— is not expressible in a generated testbench. Tying both clocks together
would produce a testbench that exercises the FIFO logic and *nothing* about
the CDC, while the datasheet claimed CDC safety. That is the
"artifact that exists but does not run" pattern this project keeps finding,
and CDC bugs are exactly what cannot be caught by reading.

Unblocking it is a TB-IR work package: a second clock on `TbSpec`, a clock
selector on `WaitCycles`, and per-clock cycle anchoring for vectors and
checks — a change to a frozen contract (TB_SPEC), so it needs a recorded
decision first.
