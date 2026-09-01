"""The ``IpDef`` contract (Phase-4 P4-01, plan Appendix B).

``IpDef`` is a strict superset of :class:`~..modules.contract.ModuleDef`: an
IP is a module that additionally declares a register map and its bus-side
port bundles. Everything a module provides — options model, IR generation,
explanation, port groups, smoke-TB recipe — an IP provides identically, so
the whole Phase-2/Phase-3 pipeline (render, lint, datasheet, TB, assertions,
test plan, golden matrix) applies to IPs with no per-IP special-casing.

Structural, like SnippetDef and ModuleDef
-----------------------------------------

Same runtime-checkable :class:`~typing.Protocol` style. The registry's
structural check already accepts any object with the four core attributes and
``generate``/``explain``, so an :class:`IpDef` instance dropped into
:mod:`semicraft_core.ips` is discovered with no registry edit; ``kind = "ip"``
routes it to :func:`~..snippets.registry.by_kind` ``"ip"``.

The one enforcement this module adds
------------------------------------

:func:`check_bundles_against_module` cross-checks the declared bundles
against the *actual* generated IR module. Declaring metadata that no one
verifies is how a bundle comes to name a port the RTL does not have — the
defect class this project has repeatedly found — so ``generate_files`` runs
this check on every IP it generates, and a mismatch is a hard error rather
than a silently wrong integration later.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel

from ..modules.contract import ExplanationDoc, PortGroup, TbSpec
from .bundles import PortBundle
from .regmap import RegisterMap

if TYPE_CHECKING:
    from ..ir.nodes import Module

__all__ = ["IpDef", "IpContractError", "check_bundles_against_module"]


class IpContractError(Exception):
    """An IP's declared metadata contradicts the module it generates.

    Raised by :func:`check_bundles_against_module`. This is a *generator* bug,
    not user input, so the API maps it to HTTP 500 like
    :class:`~..ir.validate.IRValidationError`.
    """


def check_bundles_against_module(module: Module, bundles: list[PortBundle]) -> None:
    """Verify every declared bundle against the module's real port list.

    Checks, in order:

    B1. Bundle names are unique within the IP.
    B2. Every member ``signal`` is an actual port of ``module``.
    B3. A port belongs to at most one bundle. (Clocks and resets are exempt by
        construction: they are named via ``clock``/``reset``, which are not
        member ports — see :mod:`.bundles`.)
    B4. Every ``clock``/``reset`` a bundle references is an actual port too.

    Raises :class:`IpContractError` on the first violation, naming the bundle,
    the signal, and the ports that *do* exist, so the message is enough to fix
    the declaration without opening the generator.
    """
    port_names = {p.name for p in module.ports}
    known = ", ".join(sorted(port_names)) or "(none)"

    seen_bundles: set[str] = set()
    owner: dict[str, str] = {}
    for bundle in bundles:
        if bundle.name in seen_bundles:  # B1
            raise IpContractError(
                f"module {module.name!r}: duplicate bundle name {bundle.name!r}"
            )
        seen_bundles.add(bundle.name)

        for member in bundle.ports:
            if member.signal not in port_names:  # B2
                raise IpContractError(
                    f"module {module.name!r}: bundle {bundle.name!r} declares port "
                    f"{member.signal!r} (role {member.role_name!r}), which the generated "
                    f"module does not have; its ports are: {known}"
                )
            if member.signal in owner:  # B3
                raise IpContractError(
                    f"module {module.name!r}: port {member.signal!r} is claimed by both "
                    f"bundle {owner[member.signal]!r} and bundle {bundle.name!r}; a port "
                    f"may belong to at most one bundle (shared clocks/resets go in the "
                    f"bundle's `clock`/`reset` fields, not its `ports`)"
                )
            owner[member.signal] = bundle.name

        for role, name in (("clock", bundle.clock), ("reset", bundle.reset)):  # B4
            if name is not None and name not in port_names:
                raise IpContractError(
                    f"module {module.name!r}: bundle {bundle.name!r} references {role} "
                    f"{name!r}, which the generated module does not have; its ports "
                    f"are: {known}"
                )


@runtime_checkable
class IpDef(Protocol):
    """The interface every IP file exports as a module-level instance.

    Structurally a superset of :class:`~..modules.contract.ModuleDef`:

    - ``id`` / ``name`` / ``description`` — catalog strings; ``id`` is unique
      across the *whole* catalog (snippets, modules and IPs share one id
      namespace).
    - ``kind`` — always ``"ip"``.
    - ``maturity`` — ``"stable"`` or ``"beta"``.
    - ``options_model`` — Pydantic model whose JSON Schema drives the form.
    - ``generate`` / ``explain`` / ``port_groups`` / ``tb_spec`` — exactly the
      ``ModuleDef`` semantics; an IP is generated, documented, and smoke-tested
      by the same pipeline.
    - ``register_map(opts) -> RegisterMap | None`` — the software-visible
      layout, or ``None`` for an IP with no register interface (a bare FIFO,
      say). Consumed by the datasheet generator now and by P4-02's register
      block generator later.
    - ``bundles(opts) -> list[PortBundle]`` — bus-side port bundles; may be
      empty for an IP with no protocol interface. Cross-checked against the
      generated module by :func:`check_bundles_against_module`.

    Both new methods are pure functions of already-validated options, like
    every other method on the contract.
    """

    id: str
    name: str
    description: str
    kind: str
    maturity: str
    options_model: type[BaseModel]

    def generate(self, opts: BaseModel) -> Module:  # pragma: no cover - protocol
        ...

    def explain(self, opts: BaseModel) -> ExplanationDoc:  # pragma: no cover
        ...

    def port_groups(self, opts: BaseModel) -> list[PortGroup]:  # pragma: no cover
        ...

    def tb_spec(self, opts: BaseModel) -> TbSpec:  # pragma: no cover - protocol
        ...

    def register_map(self, opts: BaseModel) -> RegisterMap | None:  # pragma: no cover
        ...

    def bundles(self, opts: BaseModel) -> list[PortBundle]:  # pragma: no cover
        ...
