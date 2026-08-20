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

from .ir.nodes import Module
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
    "EMIT_COCOTB_TB",
]

# Smoke-TB emission is feature-flagged OFF until P2-13 lands the TB generator
# that consumes ``ModuleDef.tb_spec``. When P2-13 arrives it flips this to True
# and adds the ``tb`` file to ``generate_files`` (see the guard there).
EMIT_TB = True

# cocotb testbench emission (P3-08, beta). Enabled: the backend is exercised by
# a real run gate (backend/tests/tb/test_cocotb_run.py executes the generated
# Python against the generated RTL under Verilator), so shipping it dormant
# would hide working code rather than protect users. "Beta" here means the SV
# testbench remains the supported default and the one every golden gate runs;
# the emitted Python says so in its own banner. Set False to omit the file.
EMIT_COCOTB_TB = True


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

    ``files`` is ordered rtl-first, then doc (datasheet), then tb, then a
    second doc (test plan, P3-07) for module items; snippets emit only the
    rtl entry. The ``explanation``/``config_hash``/``language`` fields mirror
    the single-file :class:`GenerateResult`.
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


def _render_rtl(item, opts, chash: str) -> tuple[str, str, str, Module]:
    """Render an item's RTL. Returns ``(path, text, language, stamped_module)``.

    Shared by the snippet and module paths: builds IR, stamps the header, and
    renders in the chosen language with the item's style options. The stamped
    IR module is returned so the smoke-TB generator can resolve the exact
    rendered port names/widths (semicraft_core.tb.generate_tb).
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
    return path, code, language, module


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


def _module_doc(
    item,
    opts,
    explanation,
    config_hash_value: str,
    interface_sections: list[str] | None = None,
) -> str:
    """Markdown datasheet for a module (Appendix A.3): title, purpose, port
    table (grouped from ``port_groups``), configuration, assumptions/limitations.

    ``interface_sections`` are extra markdown lines inserted between the port
    table and the configuration list. Empty for a module; an IP (Appendix B)
    passes its register map and bus-interface sections there, so the whole
    interface surface — ports, registers, bundles — stays together.
    """
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
        *(interface_sections or []),
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


def _ip_interface_sections(item, opts, rtl_module) -> list[str]:
    """Register-map + bus-interface datasheet sections for an IP (P4-01).

    Also the enforcement point for :func:`~.ips.contract.check_bundles_against_module`:
    the bundles are validated against the *generated* module before anything is
    rendered from them, so a bundle naming a port the RTL does not have fails
    generation loudly instead of producing a datasheet that documents a signal
    nobody emits.
    """
    from .ips.bundles import restyle_bundles
    from .ips.contract import check_bundles_against_module
    from .ips.doc import bundles_md, register_map_md
    from .render.style import build_name_map

    bundles = list(item.bundles(opts))
    # Validate the *canonical* declaration against the canonical IR module —
    # both sides are pre-style, so this compares like with like.
    check_bundles_against_module(rtl_module, bundles)

    sections: list[str] = []
    regmap = item.register_map(opts)
    if regmap is not None:
        sections.extend(register_map_md(regmap))

    # ...then restyle for display, so the datasheet names the ports the RTL
    # actually declares. See ips/bundles.restyle_bundles for why this step is
    # not optional.
    rename = build_name_map(rtl_module, _style_from_options(opts))
    directions = {rename.get(p.name, p.name): str(p.dir) for p in rtl_module.ports}
    sections.extend(bundles_md(restyle_bundles(bundles, rename), directions))
    return sections


def generate_files(item_id: str, options: dict) -> GenerateFilesResult:
    """Generate the full file set for a catalog item (API v2, Appendix A.1/A.3).

    Snippets produce a single ``rtl`` file via the existing render pipeline.
    Modules — and IPs, which take the identical path (Appendix B) — produce an
    ``rtl`` file plus a ``doc`` file (markdown datasheet from
    the ExplanationDoc + port groups, plus register-map and bus-interface
    sections for an IP), a ``tb`` file (feature-flagged by
    :data:`EMIT_TB`, built from ``ModuleDef.tb_spec``), and a second ``doc``
    file — a test-plan/verification-checklist document (P3-07,
    :func:`semicraft_core.testplan.generate_testplan`) appended *after* the
    datasheet so the datasheet stays the first ``doc`` entry in ``files``.

    Error mapping matches :func:`generate` (unknown id -> 404, invalid options
    -> 422, IR bug -> 500). Pure with respect to its inputs.
    """
    item = registry.get(item_id)  # UnknownSnippetError -> 404
    opts = item.options_model.model_validate(options)  # ValidationError -> 422
    chash = config_hash(item_id, opts.model_dump(mode="json"))

    rtl_path, rtl_text, language, rtl_module = _render_rtl(item, opts, chash)
    files: list[GeneratedFile] = [GeneratedFile(path=rtl_path, kind="rtl", text=rtl_text)]

    explanation = item.explain(opts)

    kind = registry.item_kind(item)
    if kind in ("module", "ip"):
        doc_stem = rtl_path.rsplit(".", 1)[0]
        # An IP (Appendix B) is a module plus register-map/bundle metadata, so
        # it takes the identical path and only adds two datasheet sections.
        interface_sections = _ip_interface_sections(item, opts, rtl_module) if kind == "ip" else []
        doc_text = _module_doc(item, opts, explanation, chash, interface_sections)
        files.append(GeneratedFile(path=f"{doc_stem}.md", kind="doc", text=doc_text))

        # Smoke TB (P2-13): SV testbench built from ModuleDef.tb_spec against
        # the stamped IR module, so names/widths match the rendered RTL.
        if EMIT_TB and hasattr(item, "tb_spec"):
            from .tb import generate_tb  # deferred: keeps tb/ optional at import

            tb_text = generate_tb(item, opts, rtl_module)
            if tb_text:
                files.append(
                    GeneratedFile(path=f"{rtl_module.name}_tb.sv", kind="tb", text=tb_text)
                )

            # cocotb alternative backend (P3-08, beta). Same TbSpec recipe as
            # the SV TB, emitted as Python. `kind="tb"` rather than a widened
            # GeneratedFile.kind Literal: the Literal is a frozen contract
            # (plan Appendix A.1) and the frontend's KIND_DOT is an exhaustive
            # Record<FileKind, string>, so a new kind would break its build.
            # The path distinguishes it, exactly as the datasheet/test-plan
            # split does for two `doc` files.
            if EMIT_COCOTB_TB:
                from .tb.cocotb_tb import cocotb_tb_filename, generate_cocotb_tb

                cocotb_text = generate_cocotb_tb(item, opts, rtl_module)
                if cocotb_text:
                    files.append(
                        GeneratedFile(
                            path=cocotb_tb_filename(rtl_module.name),
                            kind="tb",
                            text=cocotb_text,
                        )
                    )

        # Test-plan document (P3-07): a second `doc`-kind file appended after
        # the datasheet, derived entirely from ExplanationDoc/port_groups/
        # tb_spec — no new ModuleDef metadata. Kept last in `files` so the
        # datasheet stays the *first* `doc` entry (existing tests/tooling that
        # pick "the" doc file via `next(f for f in files if f.kind == "doc")`
        # keep resolving to the datasheet).
        if hasattr(item, "tb_spec"):
            from .testplan import generate_testplan

            testplan_text = generate_testplan(item, opts, rtl_module, explanation, chash)
            files.append(
                GeneratedFile(
                    path=f"{doc_stem}_testplan.md", kind="doc", text=testplan_text
                )
            )

    return GenerateFilesResult(
        files=files,
        explanation=explanation,
        config_hash=chash,
        language=language,
    )
