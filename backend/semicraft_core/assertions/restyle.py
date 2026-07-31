"""Rename an :class:`~.spec.AssertionSpec`'s signals through a name map (P3-05a).

``generate_assertions`` never rewrites identifiers — its docstring states the
signal names it is handed are "already styled by the caller". Nothing did that
styling: ``generate_tb`` passed a module's ``TbSpec.assertion_spec`` through
untouched, so a spec authored with *canonical* names (the only names a
``ModuleDef`` knows — ``tb_spec(opts)`` never sees the render style) produced
property text referencing identifiers that do not exist in the rendered RTL.

This is not an exotic-configuration problem. ``render.style.build_name_map``
appends ``_n`` to an active-low reset, and active-low is the **default**, so a
spec naming its reset ``rst`` would emit ``disable iff (!rst)`` against a net
actually rendered ``rst_n`` — broken at the default configuration, before any
naming convention, prefix, or suffix is involved.

:func:`restyle_spec` closes that gap: it maps every *structured* signal field
through the caller's rename function, so module authors write canonical names
and the TB generator resolves them exactly like every other net.

Scope (documented approximation, consistent with TB_SPEC §5)
------------------------------------------------------------

Only structured fields are renamed — the ones the model stores as identifiers:

- :class:`~.spec.ResetContext.signal`
- :class:`~.spec.ResetKnownValue.signal`
- :class:`~.spec.Stability.signal` / ``.enable``
- :class:`~.spec.Handshake.valid` / ``.ready`` / ``.data``
- :class:`~.spec.OneHot.signal`, :class:`~.spec.ValueRange.signal`,
  :class:`~.spec.NoUnknown.signal`
- :attr:`~.spec.AssertionSpec.clock`

The **opaque text** fields — ``OneHot.when`` and ``NoUnknown.when`` — are raw
SystemVerilog expression strings and are deliberately left alone. Renaming
identifiers inside free text would mean parsing SV, which this layer does not
do (the same reason ``validate_tb`` cannot resolve names inside
``AssertProperty.property_text``). A module attaching a ``when`` antecedent is
therefore responsible for it being valid under every naming style, which in
practice means: prefer specs without ``when``, or restrict ``when`` to
expressions over literals. This is a real limitation, not an oversight.

Assertion **names** (``ResetKnownValue.name`` and friends) are labels, not
signals, and are never renamed — they must stay stable so ``$fatal`` messages
and validator rule T8 uniqueness are independent of naming style.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

from .spec import (
    AssertionItem,
    AssertionSpec,
    Handshake,
    NoUnknown,
    OneHot,
    ResetContext,
    ResetKnownValue,
    Stability,
    ValueRange,
)

__all__ = ["restyle_spec"]

Rename = Callable[[str], str]


def _restyle_item(item: AssertionItem, rename: Rename) -> AssertionItem:
    """Return ``item`` with its structured signal fields renamed."""
    if isinstance(item, ResetKnownValue):
        return dataclasses.replace(item, signal=rename(item.signal))
    if isinstance(item, Stability):
        return dataclasses.replace(
            item, signal=rename(item.signal), enable=rename(item.enable)
        )
    if isinstance(item, Handshake):
        return dataclasses.replace(
            item,
            valid=rename(item.valid),
            ready=rename(item.ready),
            data=None if item.data is None else rename(item.data),
        )
    if isinstance(item, OneHot):
        # `when` is opaque text — deliberately not renamed (see module docstring).
        return dataclasses.replace(item, signal=rename(item.signal))
    if isinstance(item, ValueRange):
        return dataclasses.replace(item, signal=rename(item.signal))
    if isinstance(item, NoUnknown):
        # `when` is opaque text — deliberately not renamed.
        return dataclasses.replace(item, signal=rename(item.signal))
    raise TypeError(f"unknown assertion item type: {type(item).__name__}")


def restyle_spec(spec: AssertionSpec, rename: Rename) -> AssertionSpec:
    """Return a copy of ``spec`` with every structured signal name renamed.

    ``rename`` maps a canonical name to its rendered name — in practice
    ``lambda n: name_map.get(n, n)`` over ``render.style.build_name_map``'s
    output, which is exactly how ``generate_tb`` resolves every other net.

    Pure: ``spec`` is untouched (every node is a frozen dataclass and is
    rebuilt), and the same inputs always yield an equal result. Item order is
    preserved, so generated property order — and therefore the rendered text —
    stays deterministic.
    """
    reset = spec.reset
    if reset is not None:
        reset = ResetContext(
            signal=rename(reset.signal),
            active_low=reset.active_low,
            sync=reset.sync,
        )
    return AssertionSpec(
        clock=rename(spec.clock),
        items=[_restyle_item(item, rename) for item in spec.items],
        reset=reset,
    )
