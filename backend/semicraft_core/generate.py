"""End-to-end generation entry point (IMPLEMENTATION_PLAN.md §3 task 4, §4).

``generate(snippet_id, options)`` is the single function WP-04 (lint) and WP-06
(API) build on. It ties the pieces together:

    registry lookup  ->  validate options  ->  build IR  ->  render text

and stamps the file header with the license disclaimer and the config hash.

Error mapping (used by the API, IMPLEMENTATION_PLAN §4):

- unknown ``snippet_id``      -> :class:`~.snippets.registry.UnknownSnippetError`
                                 (KeyError subclass) -> HTTP 404;
- invalid ``options``         -> Pydantic ``ValidationError`` propagates
                                 -> HTTP 422;
- a generator bug producing   -> :class:`~.ir.validate.IRValidationError`
  invalid IR                    (raised inside ``render``) -> HTTP 500.

``config_hash`` (IMPLEMENTATION_PLAN §4): ``sha256`` of ``snippet_id`` plus the
canonical (sorted-keys) JSON of the **validated** options, truncated to 12 hex
chars. Hashing the validated ``model_dump`` (not the raw request dict) makes
the hash independent of omitted-vs-defaulted fields and of input key order, so
the same effective configuration always yields the same hash and byte-identical
code (ground rule §1: determinism).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel

from .license import DISCLAIMER
from .modules.contract import PortGroup
from .render import StyleOptions, render
from .snippets import registry
from .version import VERSION

__all__ = [
    "GenerateResult",
    "generate",
    "config_hash",
    "GeneratedFile",
    "GenerateFilesResult",
    "generate_files",
    "EMIT_TB",
]

# Smoke-TB emission is feature-flagged OFF until P2-13 lands the TB generator
# that consumes ``ModuleDef.tb_spec``. When P2-13 arrives it flips this to True
# and adds the ``tb`` file to ``generate_files`` (see the guard there).
EMIT_TB = False


@dataclass(frozen=True, slots=True)
class GenerateResult:
    """Result of :func:`generate`.

    - ``code`` — rendered HDL source text.
    - ``filename`` — ``<module>.sv|.v``, or ``<module>_fragment.<ext>`` in
      fragment mode.
    - ``explanation`` — the snippet's :class:`~.snippets.contract.ExplanationDoc`.
    - ``config_hash`` — 12-hex-char config hash (also stamped in the header).
    """

    code: str
    filename: str
    explanation: object
    config_hash: str


def config_hash(snippet_id: str, validated_options: dict) -> str:
    """Compute the 12-hex-char config hash (IMPLEMENTATION_PLAN §4).

    ``validated_options`` must be the dict from ``model_dump()`` on the
    validated options model. Keys are sorted and separators are fixed so the
    JSON is canonical regardless of field declaration or input order.
    """
    canonical = json.dumps(
        validated_options, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    digest = hashlib.sha256((snippet_id + canonical).encode("utf-8")).hexdigest()
    return digest[:12]


def _style_from_options(opts: BaseModel) -> StyleOptions:
    """Derive render-engine :class:`StyleOptions` from validated snippet options.

    Bridges the snippet-facing option names (``naming`` / ``comment_verbosity``)
    to the render engine's :class:`StyleOptions`. ``include_wrapper`` is passed
    to ``render`` separately, not via ``StyleOptions``.
    """
    naming = opts.naming  # NamingOptions (present on CommonOptions and subclasses)
    return StyleOptions(
        naming=naming.convention,
        prefix=naming.prefix,
        suffix=naming.suffix,
        comment_verbosity=opts.comment_verbosity,
    )


def _extension(language: str) -> str:
    return "sv" if language == "sv" else "v"


def generate(snippet_id: str, options: dict) -> GenerateResult:
    """Generate HDL for ``snippet_id`` configured by ``options``.

    Pure with respect to its inputs: identical ``(snippet_id, options)`` yields
    byte-identical ``code`` and an equal ``config_hash``.
    """
    snippet = registry.get(snippet_id)  # UnknownSnippetError -> 404

    # Validate options into the snippet's model. A Pydantic ValidationError here
    # is a user error and is allowed to propagate (API maps it to 422).
    opts = snippet.options_model.model_validate(options)

    # Hash the *validated* options (canonical, order-independent).
    dumped = opts.model_dump(mode="json")
    chash = config_hash(snippet_id, dumped)

    # Build IR, then stamp the header with the disclaimer + hash. The snippet's
    # generate() leaves those header fields blank precisely so this single point
    # owns the license/hash stamping (ground rule §1: license stamp).
    module = snippet.generate(opts)
    header = dataclasses.replace(
        module.header,
        license=DISCLAIMER,
        config_hash=chash,
        tool_version=VERSION,
    )
    module = dataclasses.replace(module, header=header)

    include_wrapper = getattr(opts, "include_wrapper", True)
    language = getattr(opts, "language", "sv")

    code = render(
        module,
        language=language,
        style=_style_from_options(opts),
        include_wrapper=include_wrapper,
    )

    ext = _extension(language)
    filename = (
        f"{module.name}.{ext}"
        if include_wrapper
        else f"{module.name}_fragment.{ext}"
    )

    return GenerateResult(
        code=code,
        filename=filename,
        explanation=snippet.explain(opts),
        config_hash=chash,
    )


# ---------------------------------------------------------------------------
# Multi-file generation (API v2, Appendix A.1 / A.3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GeneratedFile:
    """One file in a :class:`GenerateFilesResult` (Appendix A.1).

    - ``path`` — filename (e.g. ``edge_detector.sv``, ``edge_detector.md``).
    - ``kind`` — ``"rtl"`` (synthesizable HDL), ``"tb"`` (testbench), or
      ``"doc"`` (markdown datasheet).
    - ``text`` — file contents.
    """

    path: str
    kind: Literal["rtl", "tb", "doc"]
    text: str


@dataclass(frozen=True, slots=True)
class GenerateFilesResult:
    """Result of :func:`generate_files` — the multi-file API v2 shape.

    ``files`` is ordered rtl-first (then doc, then tb once P2-13 lands). The
    ``explanation``/``config_hash``/``language`` fields mirror the single-file
    :class:`GenerateResult`.
    """

    files: list[GeneratedFile] = field(default_factory=list)
    explanation: object = None
    config_hash: str = ""
    language: str = "sv"


def _stamp_header(module, chash: str):
    """Return ``module`` with its header stamped (disclaimer + hash + version).

    Header stamping stays owned by this entry-point layer (ground rule §1),
    shared by both the snippet and module paths.
    """
    header = dataclasses.replace(
        module.header,
        license=DISCLAIMER,
        config_hash=chash,
        tool_version=VERSION,
    )
    return dataclasses.replace(module, header=header)


def _render_rtl(item, opts, chash: str) -> tuple[str, str, str]:
    """Render an item's RTL. Returns ``(path, text, language)``.

    Shared by the snippet and module paths: builds IR, stamps the header, and
    renders in the chosen language with the item's style options.
    """
    module = _stamp_header(item.generate(opts), chash)
    include_wrapper = getattr(opts, "include_wrapper", True)
    language = getattr(opts, "language", "sv")
    code = render(
        module,
        language=language,
        style=_style_from_options(opts),
        include_wrapper=include_wrapper,
    )
    ext = _extension(language)
    path = f"{module.name}.{ext}" if include_wrapper else f"{module.name}_fragment.{ext}"
    return path, code, language


def _md_port_table(port_groups: list[PortGroup], explanation) -> list[str]:
    """Render the grouped port table for the doc file from ``port_groups``.

    Signal directions/descriptions come from the ExplanationDoc (keyed by name);
    grouping and per-group descriptions come from ``port_groups``.
    """
    by_name = {s.name: s for s in explanation.signals}
    lines: list[str] = []
    for group in port_groups:
        lines.append(f"### {group.name}")
        lines.append("")
        lines.append(f"{group.description}")
        lines.append("")
        lines.append("| Port | Direction | Description |")
        lines.append("| --- | --- | --- |")
        for port_name in group.ports:
            sig = by_name.get(port_name)
            direction = sig.direction if sig else "input"
            desc = sig.description if sig else ""
            lines.append(f"| `{port_name}` | {direction} | {desc} |")
        lines.append("")
    return lines


def _module_doc(item, opts, explanation, config_hash_value: str) -> str:
    """Markdown datasheet for a module (Appendix A.3): title, purpose, port
    table (grouped from ``port_groups``), configuration, assumptions/limitations."""
    port_groups = item.port_groups(opts)
    lines: list[str] = [
        f"# {item.name}",
        "",
        explanation.purpose,
        "",
        f"_Generated by SemiCraft {VERSION} — config hash `{config_hash_value}`._",
        "",
        "## Ports",
        "",
        *_md_port_table(port_groups, explanation),
        "## Configuration",
        "",
    ]
    lines.extend(f"- {item_line}" for item_line in explanation.configuration)
    lines.append("")
    lines.append("## Assumptions")
    lines.append("")
    lines.extend(f"- {a}" for a in explanation.assumptions)
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.extend(f"- {limit}" for limit in explanation.limitations)
    lines.append("")
    return "\n".join(lines)


def generate_files(item_id: str, options: dict) -> GenerateFilesResult:
    """Generate the full file set for a catalog item (API v2, Appendix A.1/A.3).

    Snippets produce a single ``rtl`` file via the existing render pipeline.
    Modules produce an ``rtl`` file plus a ``doc`` file (markdown datasheet from
    the ExplanationDoc + port groups). TB emission is feature-flagged off
    (:data:`EMIT_TB`) until P2-13; when enabled it appends a ``tb`` file built
    from ``ModuleDef.tb_spec``.

    Error mapping matches :func:`generate` (unknown id -> 404, invalid options
    -> 422, IR bug -> 500). Pure with respect to its inputs.
    """
    item = registry.get(item_id)  # UnknownSnippetError -> 404
    opts = item.options_model.model_validate(options)  # ValidationError -> 422
    chash = config_hash(item_id, opts.model_dump(mode="json"))

    rtl_path, rtl_text, language = _render_rtl(item, opts, chash)
    files: list[GeneratedFile] = [GeneratedFile(path=rtl_path, kind="rtl", text=rtl_text)]

    explanation = item.explain(opts)

    if registry.item_kind(item) == "module":
        doc_stem = rtl_path.rsplit(".", 1)[0]
        doc_text = _module_doc(item, opts, explanation, chash)
        files.append(GeneratedFile(path=f"{doc_stem}.md", kind="doc", text=doc_text))

        # Smoke-TB emission lands with P2-13 (consumes ModuleDef.tb_spec).
        if EMIT_TB:  # pragma: no cover - flag is False until P2-13
            from .modules.tb import render_tb  # noqa: PLC0415 - deferred import

            tb_path, tb_text = render_tb(item, opts, chash)
            files.append(GeneratedFile(path=tb_path, kind="tb", text=tb_text))

    return GenerateFilesResult(
        files=files,
        explanation=explanation,
        config_hash=chash,
        language=language,
    )
