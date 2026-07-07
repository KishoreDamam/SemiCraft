"""Module contract (Phase-2 P2-04, Appendix A.3).

A :class:`ModuleDef` extends the snippet contract with the metadata a *full
module* needs on top of a fragment: catalog taxonomy (``kind = "module"``),
port-group metadata for documentation, and a smoke-testbench recipe
(:class:`TbSpec`). It reuses the snippet-side option models
(:class:`~..snippets.contract.CommonOptions` / ``ClockedOptions``) and the
:class:`~..snippets.contract.ExplanationDoc` unchanged — modules and snippets
share the explanation and options surface deliberately.

Structural, like SnippetDef
---------------------------

:class:`ModuleDef` is a :class:`~typing.Protocol` (structural typing) so a
module author can implement it as a frozen dataclass, mirroring
``semicraft_core.snippets.counter._CounterSnippet``. The registry discovers
``ModuleDef`` instances by the same structural check it uses for snippets (they
share the four core attributes and ``generate``/``explain``), then reads
``kind``/``maturity`` via getattr — so ``kind = "module"`` on the def routes it
to :func:`~..snippets.registry.by_kind` "module".

The extra surface over SnippetDef:

- ``kind = "module"``, ``maturity`` — taxonomy (Appendix A.2).
- ``port_groups(opts) -> list[PortGroup]`` — documentation metadata grouping
  ports into logical bundles (clocking, data, ...). Consumed by the doc-file
  generator in :func:`semicraft_core.generate.generate_files`.
- ``tb_spec(opts) -> TbSpec`` — a smoke-TB recipe (clock/reset/vectors/checks).
  The TB *generator* (P2-13) consumes this; until it lands, TB emission is
  feature-flagged off (``generate.EMIT_TB``), so ``tb_spec`` is exercised by
  tests but its output is not yet rendered to a file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

# Re-export the shared explanation type so module files import it from here,
# keeping the modules package self-contained at the import surface.
from ..snippets.contract import ExplanationDoc

if TYPE_CHECKING:
    from ..ir.nodes import Module

__all__ = [
    "PortGroup",
    "Check",
    "TbSpec",
    "ModuleDef",
    "ExplanationDoc",
]


# ---------------------------------------------------------------------------
# Documentation metadata
# ---------------------------------------------------------------------------


class PortGroup(BaseModel):
    """A named bundle of ports for the generated datasheet (Appendix A.3).

    ``ports`` are *canonical* IR port names (before naming-style transforms);
    the doc generator lists them under ``name`` with the group ``description``.
    Grouping is documentation-only — it does not affect the generated RTL.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Group label, e.g. 'Clocking' or 'Data'.")
    ports: list[str] = Field(
        description="Canonical port names in this group, in declaration order."
    )
    description: str = Field(
        description="One-line description of what this group of ports is for."
    )


# ---------------------------------------------------------------------------
# Smoke-TB recipe (consumed by P2-13; not yet rendered — see generate.EMIT_TB)
# ---------------------------------------------------------------------------


class Check(BaseModel):
    """One expected-value assertion for the smoke TB (Appendix A.3).

    "At cycle ``cycle``, signal ``signal`` is expected to equal ``expected``."
    Checks are *declarative*; the P2-13 TB generator turns them into directed
    self-checking assertions. They are honest recipes, not yet executed.
    """

    model_config = ConfigDict(extra="forbid")

    cycle: int = Field(ge=0, description="Zero-based cycle index the check applies at.")
    signal: str = Field(description="Canonical signal/port name to sample.")
    expected: int = Field(description="Expected integer value of the signal at that cycle.")


class TbSpec(BaseModel):
    """Smoke-testbench recipe derived from a module's metadata (Appendix A.3).

    ``vectors`` are per-cycle input assignments (``{signal: value}``); ``checks``
    are expected-value assertions. ``clock``/``reset`` name the clock and reset
    ports (``None`` for a combinational or unreset module); ``reset_cycles`` is
    how many cycles the TB holds reset asserted before driving vectors.
    """

    model_config = ConfigDict(extra="forbid")

    clock: str | None = Field(
        default=None, description="Clock port name, or null for a combinational module."
    )
    reset: str | None = Field(
        default=None, description="Reset port name, or null if the module has no reset."
    )
    reset_cycles: int = Field(
        default=2,
        ge=0,
        description="Cycles to hold reset asserted before applying the first vector.",
    )
    vectors: list[dict[str, int]] = Field(
        default_factory=list,
        description="Per-cycle input assignments, one dict of {signal: value} per cycle.",
    )
    checks: list[Check] = Field(
        default_factory=list,
        description="Expected-value assertions the smoke TB will check.",
    )


# ---------------------------------------------------------------------------
# ModuleDef (Appendix A.3)
# ---------------------------------------------------------------------------


@runtime_checkable
class ModuleDef(Protocol):
    """The interface every module file exports as a module-level instance.

    Structurally a superset of :class:`~..snippets.contract.SnippetDef`: the
    registry's structural check (which only requires the four core attributes +
    ``generate``/``explain``) accepts both, and reads ``kind``/``maturity`` via
    getattr. Concrete modules set ``kind = "module"`` so they route to
    ``registry.by_kind("module")``.

    Contract:

    - ``id`` — kebab-case catalog id, unique across the whole catalog
      (snippets and modules share one id namespace).
    - ``name`` / ``description`` — catalog display strings.
    - ``kind`` — always ``"module"`` for a module.
    - ``maturity`` — ``"stable"`` or ``"beta"``.
    - ``options_model`` — Pydantic model whose JSON Schema drives the form.
    - ``generate(opts) -> Module`` — pure: validated options -> IR ``Module``
      (the RTL), same as a snippet.
    - ``explain(opts) -> ExplanationDoc`` — pure explanation.
    - ``port_groups(opts) -> list[PortGroup]`` — doc grouping metadata.
    - ``tb_spec(opts) -> TbSpec`` — smoke-TB recipe.

    All methods receive an already-validated ``options_model`` instance.
    """

    id: str
    name: str
    description: str
    kind: str
    maturity: str
    options_model: type[BaseModel]

    def generate(self, opts: BaseModel) -> Module:  # pragma: no cover - protocol
        ...

    def explain(self, opts: BaseModel) -> ExplanationDoc:  # pragma: no cover - protocol
        ...

    def port_groups(self, opts: BaseModel) -> list[PortGroup]:  # pragma: no cover
        ...

    def tb_spec(self, opts: BaseModel) -> TbSpec:  # pragma: no cover - protocol
        ...
