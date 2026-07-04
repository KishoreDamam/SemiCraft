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
from dataclasses import dataclass

from pydantic import BaseModel

from .license import DISCLAIMER
from .render import StyleOptions, render
from .snippets import registry
from .version import VERSION

__all__ = ["GenerateResult", "generate", "config_hash"]


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
