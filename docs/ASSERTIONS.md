# SemiCraft SVA Assertion Generator (P3-05)

**Owner:** verification core (`semicraft_core/assertions/`). Companion to
[TB_SPEC.md](TB_SPEC.md) (the TB IR family) and
[PLAN-semicraft-phases-2-8.md](PLAN-semicraft-phases-2-8.md) (Phase 3, P3-05).

A small, deterministic generator that turns a declarative **assertion spec**
into a tuple of `AssertProperty` nodes (from `semicraft_core.tb.nodes`). It is a
standalone package: it is **not** yet wired into `generate_files` — integration
is a later WP. Authoring-time callers construct an `AssertionSpec` (or a
`ModuleDef` may carry one) and call `generate_assertions`.

## Design rules

Mirrors [TB_SPEC §2](TB_SPEC.md) / [IR_SPEC §2](IR_SPEC.md): every spec type is a
**frozen + slotted** dataclass with full type annotations; sequence-valued
fields accept any `Sequence` and are stored as `tuple`. Generation is pure and
deterministic — the same spec yields the same ordered tuple of properties,
byte-for-byte, with no timestamps or randomness.

**Documented approximation (consistent with TB_SPEC §5).** Property bodies are
opaque SystemVerilog **text** carried on `AssertProperty`; this generator picks
the idiom per template family but does not build a property AST. Signal names
are taken verbatim (already styled by the caller) — the generator never rewrites
identifiers. Every generated tuple satisfies `validate_tb` rule T8 (unique
names, non-empty `property_text`, resolvable `clock`); a duplicate name raises
`ValueError` rather than emitting a T8-violating tree.

## Spec model (`semicraft_core.assertions.spec`)

```python
AssertionSpec(clock: str, items: Sequence[AssertionItem], reset: ResetContext | None = None)
ResetContext(signal: str, active_low: bool, sync: bool)
```

- `clock` becomes each property's sampling clock (`AssertProperty.clock`).
- `reset` supplies the `disable iff` guard for *guarded* items (below). When
  `None`, no property is guarded.
- `items` are the ordered template requests; output order follows item order.

### `disable iff` composition

The guard body is **polarity-determined only**:

| Reset | `disable iff` body |
|---|---|
| active-low (`rst_n`) | `!rst_n` |
| active-high (`rst`) | `rst` |

It is **identical for synchronous and asynchronous resets**, because SVA
`disable iff` is itself asynchronous — a synchronous reset is guarded exactly
like an asynchronous one. `ResetContext.sync` is carried for callers and future
refinements but does not change the emitted guard today. The stored
`disable_iff` field holds only the guard body (e.g. `!rst_n`); the TB renderer
(P3-02) wraps it as `disable iff (...)`.

## Template families

Each item is a frozen dataclass with a `name` (the assertion label). Guarded
families expose `guarded: bool = True` to opt out of the reset guard per item.

| Family | Item | Emitted `property_text` |
|---|---|---|
| Reset behaviour | `ResetKnownValue(name, signal, value, width)` | `$rose(rst_n) \| $fell(rst) \|-> signal == width'dvalue` |
| Enable stability | `Stability(name, signal, enable)` | `!enable \|=> $stable(signal)` |
| Handshake (valid/ready) | `Handshake(name, valid, ready, data=None)` | `valid && !ready \|=> valid` (+ `..\|=> $stable(data)` as `<name>_data`) |
| One-hot / one-hot0 | `OneHot(name, signal, allow_zero=False, when=None)` | `[when \|->] $onehot(signal)` / `$onehot0(signal)` |
| Value-range | `ValueRange(name, signal, max_value, width, min_value=0)` | `signal <= width'dmax` (or `signal >= width'dmin && signal <= width'dmax`) |
| No-X propagation | `NoUnknown(name, signal, when=None)` | `[when \|->] !$isunknown(signal)` |

Notes:

- **`ResetKnownValue` is never guarded** — it is the assertion *about* reset, so
  disabling it during reset would defeat its purpose. It uses the reset
  *deassertion* edge: `$rose(rst_n)` (active-low, net 0->1) or `$fell(rst)`
  (active-high, net 1->0). It raises `ValueError` if the spec has no `reset`.
- **`Handshake` with `data`** expands to **two** properties: `<name>` (valid
  held until ready) and `<name>_data` (payload stable while the transfer is
  pending). All other items map to exactly one property.
- **`when`** (on `OneHot` / `NoUnknown`) is an opaque antecedent expression
  string, e.g. `grant_valid` for `grant_valid |-> $onehot0(grant)`.

## Entry point

```python
from semicraft_core.assertions import AssertionSpec, generate_assertions, ...
props: tuple[AssertProperty, ...] = generate_assertions(spec)
```

`generate_assertions(spec)` returns the ordered property tuple, checking name
uniqueness across the whole result (raising `ValueError` on a collision, e.g. an
explicit item named `hs_data` colliding with a `Handshake('hs', data=...)`
expansion).
