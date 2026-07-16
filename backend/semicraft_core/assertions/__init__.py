"""Deterministic SVA assertion generator (P3-05).

A standalone package that turns a declarative
:class:`~semicraft_core.assertions.spec.AssertionSpec` into a tuple of
:class:`~semicraft_core.tb.nodes.AssertProperty` nodes across a fixed set of SVA
template families (reset behaviour, enable stability, valid/ready handshake,
one-hot / one-hot-or-zero, value-range, no-X propagation). Property bodies are
opaque SystemVerilog text per the TB_SPEC §5 approximation.

Not yet wired into ``generate_files`` — integration is a later WP. See
``docs/ASSERTIONS.md``.
"""

from .generate import generate_assertions
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

__all__ = [
    "generate_assertions",
    "AssertionSpec",
    "AssertionItem",
    "ResetContext",
    "ResetKnownValue",
    "Stability",
    "Handshake",
    "OneHot",
    "ValueRange",
    "NoUnknown",
]
