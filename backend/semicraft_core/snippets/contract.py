"""Frozen snippet contract (IMPLEMENTATION_PLAN.md §3).

Every snippet is one module in :mod:`semicraft_core.snippets` exporting a
:class:`SnippetDef` instance. The types here are the contract nine later
snippet WPs (WP-05a..i) build against — do not change field shapes without
surfacing the conflict (ground rule §1: interfaces are frozen by spec).

Design of the options hierarchy
-------------------------------

Reset/clock fields only make sense for *clocked* snippets. Rather than putting
them on every snippet and documenting "ignored for combinational snippets",
they live on :class:`ClockedOptions`, a mixin that adds the reset fields on top
of :class:`CommonOptions`:

- purely combinational snippets (mux, decoder, comparator, ...) extend
  :class:`CommonOptions`;
- clocked snippets (counter, register, shift-register, ...) extend
  :class:`ClockedOptions`.

Every field carries a default, a constraint where meaningful, and a
``Field(description=...)``. The API exposes these models via
``model_json_schema()``; the frontend renders forms from that schema and shows
the descriptions as tooltips (IMPLEMENTATION_PLAN §4, risk §8 "JSON Schema
fidelity"). Keep descriptions user-facing and complete.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ..ir.nodes import Module


# ---------------------------------------------------------------------------
# Option models (shared across snippets — defined once, mixed in)
# ---------------------------------------------------------------------------


class NamingOptions(BaseModel):
    """Identifier naming style applied to ports/signals at render time.

    Mirrors the render-engine :class:`~semicraft_core.render.style.StyleOptions`
    naming knobs; :func:`semicraft_core.generate.generate` translates these into
    that type. ``convention`` selects the identifier case; ``prefix``/``suffix``
    wrap every rendered name (e.g. ``prefix="i_"`` for input-port style).
    """

    model_config = ConfigDict(extra="forbid")

    convention: Literal["snake", "camel"] = Field(
        default="snake",
        description=(
            "Identifier case convention for ports and internal signals. "
            "'snake' keeps canonical lower_snake_case names; 'camel' converts "
            "to lowerCamelCase."
        ),
    )
    prefix: str = Field(
        default="",
        description=(
            "Literal string prepended to every rendered signal/port name "
            "(for example 'i_'/'o_' port-prefix styles). Empty for no prefix."
        ),
    )
    suffix: str = Field(
        default="",
        description=(
            "Literal string appended to every rendered signal/port name. "
            "Empty for no suffix. The active-low '_n' suffix is applied "
            "automatically and is independent of this option."
        ),
    )


class CommonOptions(BaseModel):
    """Options every snippet supports (IMPLEMENTATION_PLAN §3).

    Combinational snippets extend this directly. Clocked snippets extend
    :class:`ClockedOptions`, which adds reset fields on top.
    """

    model_config = ConfigDict(extra="forbid")

    language: Literal["sv", "verilog"] = Field(
        default="sv",
        description=(
            "Output HDL. 'sv' emits SystemVerilog (logic, always_ff/comb); "
            "'verilog' emits Verilog-2001 (inferred reg/wire, always @)."
        ),
    )
    include_wrapper: bool = Field(
        default=True,
        description=(
            "When true, emit a complete module with port list. When false, "
            "emit fragment mode: just the processes/assigns plus a comment "
            "block listing the declarations the enclosing module must provide."
        ),
    )
    comment_verbosity: Literal["none", "normal", "verbose"] = Field(
        default="normal",
        description=(
            "Explanatory comment level in the generated code. 'none' strips "
            "all comments (including port docs); 'normal' keeps standard "
            "comments; 'verbose' adds extra intent commentary."
        ),
    )
    naming: NamingOptions = Field(
        default_factory=NamingOptions,
        description="Identifier naming style (convention, optional prefix/suffix).",
    )


class ClockedOptions(CommonOptions):
    """Common options plus reset configuration, for clocked snippets.

    Reset style and polarity feed the single ``ResetSpec`` in each clocked
    snippet's ``AlwaysFF``; the renderer composes the sensitivity list and
    reset skeleton from it (IR_SPEC §4). Combinational snippets must NOT extend
    this — they have no clock or reset.
    """

    reset_style: Literal["sync", "async"] = Field(
        default="sync",
        description=(
            "Reset timing. 'sync' samples reset on the clock edge; 'async' "
            "adds the reset edge to the sensitivity list for immediate reset."
        ),
    )
    reset_polarity: Literal["active_high", "active_low"] = Field(
        default="active_low",
        description=(
            "Reset assertion level. 'active_low' resets when the reset input "
            "is 0 (named rst_n); 'active_high' resets when it is 1 (named rst)."
        ),
    )


# ---------------------------------------------------------------------------
# Explanation document (IMPLEMENTATION_PLAN §3)
# ---------------------------------------------------------------------------


class SignalDoc(BaseModel):
    """One port/signal row in an :class:`ExplanationDoc`."""

    name: str = Field(description="Signal name as it appears in the generated code.")
    direction: Literal["input", "output", "internal"] = Field(
        description="Port direction, or 'internal' for a module-internal signal."
    )
    description: str = Field(description="Plain-language role of this signal.")


class ExplanationDoc(BaseModel):
    """Human-readable explanation of a generated snippet (IMPLEMENTATION_PLAN §3).

    Rendered by the frontend explanation panel. ``explain()`` must populate
    every field meaningfully for the actual chosen options — this is a
    selling point of SemiCraft, not boilerplate.
    """

    purpose: str = Field(description="What the snippet does, in one or two sentences.")
    configuration: list[str] = Field(
        description="Human-readable summary of the chosen options, one item each."
    )
    signals: list[SignalDoc] = Field(
        description="Every port and notable internal signal with direction and role."
    )
    reset_behavior: str = Field(
        description="How reset behaves, matching the chosen style and polarity."
    )
    enable_behavior: str | None = Field(
        default=None,
        description="How the enable input behaves, or null when there is no enable.",
    )
    assumptions: list[str] = Field(
        description="Design assumptions the user should be aware of."
    )
    limitations: list[str] = Field(
        description="Known limitations (wrap behavior, no CDC handling, etc.)."
    )


# ---------------------------------------------------------------------------
# SnippetDef (IMPLEMENTATION_PLAN §3)
# ---------------------------------------------------------------------------


@runtime_checkable
class SnippetDef(Protocol):
    """The interface every snippet module exports as a module-level instance.

    This is a :class:`~typing.Protocol`: a snippet class need only provide the
    attributes and methods below (structural typing), so authors are free to
    implement it as a dataclass, a plain class, or otherwise. The registry
    discovers instances that satisfy this protocol.

    Contract:

    - ``id`` — kebab-case catalog id, unique across the package (e.g. "counter",
      "shift-register").
    - ``name`` — display name for the catalog.
    - ``description`` — one sentence shown in the catalog.
    - ``options_model`` — the Pydantic model whose JSON Schema drives the form.
    - ``generate(opts)`` — pure: validated options -> IR ``Module``.
    - ``explain(opts)`` — pure: validated options -> :class:`ExplanationDoc`.

    ``generate``/``explain`` receive an already-validated ``options_model``
    instance (validation happens in :func:`semicraft_core.generate.generate`).

    Catalog taxonomy (Phase-2 Appendix A.2)
    ---------------------------------------

    The catalog surface gained two taxonomy fields, ``kind`` and ``maturity``.
    Existing snippet files (the ten WP-05 modules) do NOT declare them, so they
    are read from the def with ``getattr`` defaulting at the *registry* layer
    (:func:`.registry.item_kind` / :func:`.registry.item_maturity`): a snippet
    that omits ``kind`` is treated as ``"snippet"`` and one that omits
    ``maturity`` as ``"stable"``. This keeps the Protocol structural (a plain
    dataclass with only the four original attributes still satisfies it) and
    requires zero edits to the shipped snippet files. ``kind``/``maturity`` are
    intentionally NOT declared as Protocol members (see the note below the
    method annotations) so that ``isinstance(obj, SnippetDef)`` stays true for
    the existing defs. ``ModuleDef`` (Phase-2 P2-04) sets ``kind = "module"``
    explicitly; future ``ip``/``subsystem``/``app`` kinds follow the same rule.
    """

    id: str
    name: str
    description: str
    options_model: type[BaseModel]
    # NOTE on taxonomy (kind/maturity): these are deliberately NOT declared as
    # Protocol members. Under ``@runtime_checkable``, every annotated non-method
    # member becomes a required attribute for ``isinstance``; adding ``kind``
    # here would make ``isinstance(existing_snippet, SnippetDef)`` False for the
    # ten shipped snippet files, which do not set it. Instead the registry reads
    # them with getattr-defaulting (``kind`` -> "snippet", ``maturity`` ->
    # "stable"); see :func:`.registry.item_kind` / :func:`.registry.item_maturity`
    # and the class docstring above.

    def generate(self, opts: BaseModel) -> Module:  # pragma: no cover - protocol
        ...

    def explain(self, opts: BaseModel) -> ExplanationDoc:  # pragma: no cover - protocol
        ...


__all__ = [
    "NamingOptions",
    "CommonOptions",
    "ClockedOptions",
    "SignalDoc",
    "ExplanationDoc",
    "SnippetDef",
]
