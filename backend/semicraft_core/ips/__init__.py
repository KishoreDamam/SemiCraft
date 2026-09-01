"""IP-block contract and metadata models (Phase-4 P4-01).

An **IP** is a :class:`~..modules.contract.ModuleDef` plus the two pieces of
metadata that distinguish a curated, integratable block from a standalone
module:

- a **register map** (:class:`~.regmap.RegisterMap`) — the software-visible
  address/field layout, and
- **bus-side port bundles** (:class:`~.bundles.PortBundle`) — named groupings
  of *flat* ports that declare "these signals together form one AXI4-Lite
  target port", so Phase-5's subsystem composer can wire IPs to each other
  without pattern-matching on signal names.

This package holds the contract only. The IP *implementations* land in
P4-02..P4-08 (AXI-Lite register block first, as the keystone the others
reuse); until then the package exports types and no catalog items, so
``registry.by_kind("ip")`` is legitimately empty.

Interfaces are metadata, not SystemVerilog ``interface`` constructs
-------------------------------------------------------------------

A deliberate scope decision recorded in
``docs/PLAN-semicraft-phases-2-8.md`` Appendix B: a :class:`PortBundle` never
changes the generated RTL. The ports stay flat (``awvalid``, ``awready``,
...) exactly as they are today; the bundle only *describes* which flat ports
belong together and what each one's protocol role is. That keeps the RTL
Verilog-compatible, keeps lint/golden behaviour unchanged, and defers the
SV-``interface``/``modport`` question until something actually needs it.
"""

from __future__ import annotations

from .bundles import BundlePort, BundleRole, PortBundle, restyle_bundles
from .contract import IpContractError, IpDef, check_bundles_against_module
from .regmap import Access, Register, RegisterField, RegisterMap

__all__ = [
    "Access",
    "RegisterField",
    "Register",
    "RegisterMap",
    "BundleRole",
    "BundlePort",
    "PortBundle",
    "restyle_bundles",
    "IpDef",
    "IpContractError",
    "check_bundles_against_module",
]
