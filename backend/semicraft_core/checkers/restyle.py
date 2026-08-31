"""Rename a checker/monitor/scoreboard spec's signals through a name map (P4-09).

The direct analogue of :mod:`semicraft_core.assertions.restyle`, and it exists
for the same reason. ``checkers.generate`` takes identifiers **verbatim** — its
docstring says the names it is handed are "already styled by the caller" — but
an IP's ``verification_spec(opts)`` never sees the render style, so it can only
speak canonical names. ``render.style.build_name_map`` appends ``_n`` to an
active-low reset, and AXI4-Lite fixes the reset active-low, so a spec naming its
reset ``areset`` would bind against a net actually rendered ``areset_n`` — wrong
at the *default* configuration, before any naming convention or prefix is
involved. That is the bug P3-05a already found once in the assertion path; this
module is what stops it recurring in the checker path.

Bare identifiers, and nothing else
----------------------------------

Several fields on these specs are documented as *opaque SystemVerilog text*
(``MonitorSpec.qualifier``, ``StabilityCheck.enable``, ``LatencyCheck.request``
/ ``.response``, ``ScoreboardWrapper.push_expr`` / ``.compare_expr``). Renaming
identifiers inside real expression text would mean parsing SystemVerilog, which
this layer does not do — the same limit ``assertions/restyle.py`` documents for
``when`` antecedents.

So the rule here is narrow and checkable: a field is renamed **only when its
whole value is a bare identifier** (:func:`_is_identifier`). ``"bvalid"`` is
renamed; ``"bvalid && bready"`` is left exactly as written. That covers every
spec SemiCraft's own IPs produce — they are written to use bare signal names
precisely so this holds — and it leaves a hand-written expression untouched
rather than corrupting it. An author who writes an expression owns its validity
under every naming style, and the IP-side guard
:func:`~semicraft_core.ips.verification.check_spec_is_restylable` refuses to
ship one, so the limitation cannot be reached by accident from the catalog.

Check *names* (``ResetValueCheck.name`` and friends), the monitor/checker module
names and the scoreboard class name are labels, not signals, and are never
renamed: they seed generated register names and ``$error`` message text, which
must stay stable across naming styles.
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable

from .spec import (
    CheckerItem,
    CheckerSpec,
    LatencyCheck,
    MonitorSpec,
    ResetValueCheck,
    ScoreboardSpec,
    ScoreboardWrapper,
    Signal,
    StabilityCheck,
)

__all__ = [
    "is_identifier",
    "restyle_monitor",
    "restyle_checker",
    "restyle_scoreboard",
]

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")

Rename = Callable[[str], str]


def is_identifier(text: str) -> bool:
    """True if ``text`` is a single bare SystemVerilog identifier.

    The whole test for "can this field be renamed safely": no operators, no
    whitespace, no indices, no concatenation — just a name.
    """
    return bool(_IDENTIFIER.match(text))


def _opaque(text: str, rename: Rename) -> str:
    """Rename ``text`` if it is a bare identifier; otherwise leave it alone."""
    return rename(text) if is_identifier(text) else text


def _fields(signals: tuple[Signal, ...], rename: Rename) -> tuple[Signal, ...]:
    return tuple(dataclasses.replace(s, name=rename(s.name)) for s in signals)


def restyle_monitor(spec: MonitorSpec, rename: Rename) -> MonitorSpec:
    """A copy of ``spec`` with its clock, fields and bare qualifier renamed."""
    return MonitorSpec(
        name=spec.name,
        clock=rename(spec.clock),
        fields=_fields(spec.fields, rename),
        qualifier=None if spec.qualifier is None else _opaque(spec.qualifier, rename),
    )


def _restyle_item(item: CheckerItem, rename: Rename) -> CheckerItem:
    if isinstance(item, ResetValueCheck):
        return dataclasses.replace(item, signal=rename(item.signal))
    if isinstance(item, StabilityCheck):
        return dataclasses.replace(
            item,
            signal=rename(item.signal),
            enable=_opaque(item.enable, rename),
        )
    if isinstance(item, LatencyCheck):
        return dataclasses.replace(
            item,
            request=_opaque(item.request, rename),
            response=_opaque(item.response, rename),
        )
    raise TypeError(f"unrestylable checker item: {item!r}")  # pragma: no cover


def restyle_checker(spec: CheckerSpec, rename: Rename) -> CheckerSpec:
    """A copy of ``spec`` with its clock, reset, ports and check signals renamed."""
    reset = spec.reset
    if reset is not None:
        reset = dataclasses.replace(reset, signal=rename(reset.signal))
    return CheckerSpec(
        name=spec.name,
        clock=rename(spec.clock),
        ports=_fields(spec.ports, rename),
        checks=tuple(_restyle_item(c, rename) for c in spec.checks),
        reset=reset,
    )


def restyle_scoreboard(spec: ScoreboardSpec, rename: Rename) -> ScoreboardSpec:
    """A copy of ``spec`` with its wrapper's signals renamed.

    The class name and ``item_type`` are untouched: one is a label, the other a
    type, and neither is a net.
    """
    wrapper = spec.wrapper
    if wrapper is not None:
        wrapper = ScoreboardWrapper(
            module_name=wrapper.module_name,
            clock=rename(wrapper.clock),
            push_signal=rename(wrapper.push_signal),
            push_expr=_opaque(wrapper.push_expr, rename),
            compare_signal=rename(wrapper.compare_signal),
            compare_expr=_opaque(wrapper.compare_expr, rename),
            ports=_fields(wrapper.ports, rename),
        )
    return ScoreboardSpec(name=spec.name, item_type=spec.item_type, wrapper=wrapper)
