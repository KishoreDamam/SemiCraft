"""Deterministic SVA assertion generator (P3-05).

Turns an :class:`~semicraft_core.assertions.spec.AssertionSpec` into an ordered
tuple of :class:`~semicraft_core.tb.nodes.AssertProperty` nodes — the "SVA
template families" of plan P3-05: reset behaviour, enable stability, valid/ready
handshake, one-hot / one-hot-or-zero, value-range, and no-X (no-unknown)
propagation.

Property bodies are emitted as opaque SystemVerilog **text** carried on
``AssertProperty`` (TB_SPEC §5 documented approximation — the TB family has no
property AST). This module chooses the idiom per family; it never rewrites the
signal names it is handed (they are already styled by the caller).

Determinism: the output tuple follows spec item order exactly, with no
timestamps or randomness. Property names are checked for uniqueness so the
result always satisfies ``validate_tb`` rule T8; a duplicate name raises
:class:`ValueError` rather than producing a T8-violating tree.
"""

from __future__ import annotations

from ..tb.nodes import AssertProperty
from .spec import (
    AssertionSpec,
    Handshake,
    NoUnknown,
    OneHot,
    ResetContext,
    ResetKnownValue,
    Stability,
    ValueRange,
)

__all__ = ["generate_assertions"]


# ---------------------------------------------------------------------------
# Small text helpers (single source of truth for each idiom fragment)
# ---------------------------------------------------------------------------


def _lit(value: int, width: int) -> str:
    """Sized decimal literal ``<width>'d<value>`` (mirrors ``DriveSignal``)."""
    return f"{width}'d{value}"


def _reset_asserted_expr(reset: ResetContext) -> str:
    """The boolean expression true while reset is asserted (guard body).

    Polarity-determined only: ``!rst_n`` for active-low, ``rst`` for
    active-high. Identical for sync and async resets (see :class:`ResetContext`).
    """
    return f"!{reset.signal}" if reset.active_low else reset.signal


def _reset_deassert_edge(reset: ResetContext) -> str:
    """Edge expression marking reset *deassertion*.

    ``$rose(rst_n)`` for an active-low reset (net goes 0->1 on release),
    ``$fell(rst)`` for an active-high reset (net goes 1->0 on release).
    """
    return f"$rose({reset.signal})" if reset.active_low else f"$fell({reset.signal})"


def _guard(reset: ResetContext | None, guarded: bool) -> str | None:
    """The ``disable iff`` body for a guarded item, or ``None``.

    ``None`` when the spec has no reset or the item opted out of guarding.
    """
    if reset is None or not guarded:
        return None
    return _reset_asserted_expr(reset)


# ---------------------------------------------------------------------------
# Per-family property builders — each yields (name, property_text, disable_iff)
# ---------------------------------------------------------------------------


def _reset_known_value(
    item: ResetKnownValue, reset: ResetContext | None
) -> list[tuple[str, str, str | None]]:
    if reset is None:
        raise ValueError(
            f"ResetKnownValue {item.name!r} requires a reset context on the spec"
        )
    edge = _reset_deassert_edge(reset)
    text = f"{edge} |-> {item.signal} == {_lit(item.value, item.width)}"
    # Never guarded: this is the assertion *about* reset itself.
    return [(item.name, text, None)]


def _stability(
    item: Stability, reset: ResetContext | None
) -> list[tuple[str, str, str | None]]:
    text = f"!{item.enable} |=> $stable({item.signal})"
    return [(item.name, text, _guard(reset, item.guarded))]


def _handshake(
    item: Handshake, reset: ResetContext | None
) -> list[tuple[str, str, str | None]]:
    guard = _guard(reset, item.guarded)
    pending = f"{item.valid} && !{item.ready}"
    out: list[tuple[str, str, str | None]] = [
        (item.name, f"{pending} |=> {item.valid}", guard),
    ]
    if item.data is not None:
        out.append(
            (f"{item.name}_data", f"{pending} |=> $stable({item.data})", guard)
        )
    return out


def _onehot(
    item: OneHot, reset: ResetContext | None
) -> list[tuple[str, str, str | None]]:
    fn = "$onehot0" if item.allow_zero else "$onehot"
    core = f"{fn}({item.signal})"
    text = core if item.when is None else f"{item.when} |-> {core}"
    return [(item.name, text, _guard(reset, item.guarded))]


def _value_range(
    item: ValueRange, reset: ResetContext | None
) -> list[tuple[str, str, str | None]]:
    hi = f"{item.signal} <= {_lit(item.max_value, item.width)}"
    if item.min_value == 0:
        text = hi
    else:
        lo = f"{item.signal} >= {_lit(item.min_value, item.width)}"
        text = f"{lo} && {hi}"
    return [(item.name, text, _guard(reset, item.guarded))]


def _no_unknown(
    item: NoUnknown, reset: ResetContext | None
) -> list[tuple[str, str, str | None]]:
    core = f"!$isunknown({item.signal})"
    text = core if item.when is None else f"{item.when} |-> {core}"
    return [(item.name, text, _guard(reset, item.guarded))]


_BUILDERS = {
    ResetKnownValue: _reset_known_value,
    Stability: _stability,
    Handshake: _handshake,
    OneHot: _onehot,
    ValueRange: _value_range,
    NoUnknown: _no_unknown,
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def generate_assertions(spec: AssertionSpec) -> tuple[AssertProperty, ...]:
    """Build the ordered tuple of :class:`AssertProperty` for ``spec`` (pure).

    One item usually maps to one property; a :class:`Handshake` with ``data``
    maps to two (``<name>`` and ``<name>_data``). Property order follows spec
    item order. Names are checked for uniqueness across the whole result so the
    tuple always satisfies ``validate_tb`` rule T8; a duplicate raises
    :class:`ValueError`.
    """
    out: list[AssertProperty] = []
    seen: set[str] = set()
    for item in spec.items:
        builder = _BUILDERS[type(item)]
        for name, text, disable_iff in builder(item, spec.reset):
            if name in seen:
                raise ValueError(f"duplicate assertion name: {name!r}")
            seen.add(name)
            out.append(
                AssertProperty(
                    name=name,
                    property_text=text,
                    clock=spec.clock,
                    disable_iff=disable_iff,
                )
            )
    return tuple(out)
