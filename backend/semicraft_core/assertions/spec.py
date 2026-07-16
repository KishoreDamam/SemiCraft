"""Declarative assertion-spec model for the SVA generator (P3-05).

A tiny frozen-dataclass model describing *which* SystemVerilog assertions to
emit for a module, independent of how the property text is spelled. A
:class:`ModuleDef` may carry an :class:`AssertionSpec` (or a caller can build
one directly); :func:`semicraft_core.assertions.generate.generate_assertions`
turns it into a tuple of :class:`~semicraft_core.tb.nodes.AssertProperty` nodes.

Design (mirrors ``semicraft_core/tb/nodes.py`` and IR_SPEC §2): every type is a
**frozen + slotted** dataclass with full type annotations; sequence-valued
fields accept any ``Sequence`` and are stored as ``tuple`` (immutability +
hashability). Generation is pure and deterministic — the same spec yields the
same ordered tuple of properties, byte-for-byte, with no timestamps or
randomness.

Documented approximation (consistent with TB_SPEC §5): the generated property
bodies are opaque SystemVerilog *text* carried on ``AssertProperty`` — this
generator picks the idiom per template family but does not build a property AST.
Signal names are taken verbatim (already styled by the caller), so the model
never rewrites identifiers.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

__all__ = [
    "ResetContext",
    "ResetKnownValue",
    "Stability",
    "Handshake",
    "OneHot",
    "ValueRange",
    "NoUnknown",
    "AssertionItem",
    "AssertionSpec",
]


# ---------------------------------------------------------------------------
# Shared reset context
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResetContext:
    """Reset metadata used to compose ``disable iff`` guards and reset checks.

    - ``signal`` — the already-styled reset net name (``"rst_n"`` for an
      active-low reset, ``"rst"`` for active-high). Taken verbatim.
    - ``active_low`` — asserted level. Drives the guard polarity: the
      reset-asserted expression is ``!rst_n`` (active-low) or ``rst``
      (active-high).
    - ``sync`` — ``True`` for a synchronous reset, ``False`` for asynchronous.

    The ``disable iff`` guard is **polarity-determined only**: it is identical
    for synchronous and asynchronous resets, because SVA ``disable iff`` is
    itself asynchronous, so a synchronous reset is guarded exactly like an
    asynchronous one. ``sync`` is carried for callers/documentation and for
    future template refinements; it does not change the emitted guard today.
    """

    signal: str
    active_low: bool
    sync: bool


# ---------------------------------------------------------------------------
# Per-family assertion items
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResetKnownValue:
    """A signal takes a known value on reset deassertion.

    Emits ``<deassert-edge> |-> <signal> == <width>'d<value>`` where the edge is
    ``$rose(rst_n)`` (active-low) or ``$fell(rst)`` (active-high). This item is
    *never* guarded by ``disable iff`` — it is the assertion *about* reset, so
    disabling it during reset would defeat its purpose.
    """

    name: str
    signal: str
    value: int
    width: int


@dataclass(frozen=True, slots=True)
class Stability:
    """A signal holds stable while an enable is deasserted.

    Emits ``!<enable> |=> $stable(<signal>)``: on any cycle the enable is low,
    the signal must be unchanged on the next cycle. ``guarded`` (default
    ``True``) includes the spec's reset ``disable iff`` guard.
    """

    name: str
    signal: str
    enable: str
    guarded: bool = True


@dataclass(frozen=True, slots=True)
class Handshake:
    """Valid/ready handshake stability.

    Emits ``<valid> && !<ready> |=> <valid>`` (valid is held until accepted),
    and — when ``data`` is given — a second property
    ``<valid> && !<ready> |=> $stable(<data>)`` (payload does not change while
    the transfer is pending). The two properties are named ``<name>`` and
    ``<name>_data`` respectively. ``guarded`` includes the reset guard.
    """

    name: str
    valid: str
    ready: str
    data: str | None = None
    guarded: bool = True


@dataclass(frozen=True, slots=True)
class OneHot:
    """A vector is one-hot (or one-hot-or-zero).

    Emits ``$onehot(<signal>)`` — or ``$onehot0(<signal>)`` when
    ``allow_zero`` — optionally implied by an antecedent ``when`` text
    (``<when> |-> $onehot(<signal>)``). ``allow_zero`` selects the ``onehot0``
    family (zero or one bit set), e.g. a one-hot grant that may be all-zero when
    idle. ``guarded`` includes the reset guard.
    """

    name: str
    signal: str
    allow_zero: bool = False
    when: str | None = None
    guarded: bool = True


@dataclass(frozen=True, slots=True)
class ValueRange:
    """A signal stays within an inclusive integer range.

    Emits ``<signal> <= <width>'d<max_value>`` when ``min_value == 0``, else
    ``<signal> >= <width>'d<min_value> && <signal> <= <width>'d<max_value>``.
    ``guarded`` includes the reset guard.
    """

    name: str
    signal: str
    max_value: int
    width: int
    min_value: int = 0
    guarded: bool = True


@dataclass(frozen=True, slots=True)
class NoUnknown:
    """A signal is never X/Z (optionally only when a condition holds).

    Emits ``!$isunknown(<signal>)`` — or ``<when> |-> !$isunknown(<signal>)``
    when a ``when`` antecedent is given (the classic "no X on data while valid"
    check). ``guarded`` includes the reset guard.
    """

    name: str
    signal: str
    when: str | None = None
    guarded: bool = True


# The item union accepted by :class:`AssertionSpec`. Each member maps to one or
# more :class:`~semicraft_core.tb.nodes.AssertProperty` nodes (only
# :class:`Handshake` may expand to two).
AssertionItem = (
    ResetKnownValue | Stability | Handshake | OneHot | ValueRange | NoUnknown
)


# ---------------------------------------------------------------------------
# Top-level spec
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AssertionSpec:
    """A module's assertion recipe: clock, optional reset, and ordered items.

    - ``clock`` — the sampling clock net name (bare, e.g. ``"clk"``); becomes
      the :attr:`~semicraft_core.tb.nodes.AssertProperty.clock` of every
      generated property.
    - ``items`` — the ordered template requests; property output follows this
      order deterministically.
    - ``reset`` — optional :class:`ResetContext`. When present, guarded items
      receive a ``disable iff`` guard; when ``None``, no property is guarded
      (and reset-known-value items are meaningless — see ``generate``).

    Sequence-in / tuple-stored per the shared idiom.
    """

    clock: str
    items: tuple[AssertionItem, ...]
    reset: ResetContext | None = None

    def __init__(
        self,
        clock: str,
        items: Sequence[AssertionItem],
        reset: ResetContext | None = None,
    ) -> None:
        object.__setattr__(self, "clock", clock)
        object.__setattr__(self, "items", tuple(items))
        object.__setattr__(self, "reset", reset)
