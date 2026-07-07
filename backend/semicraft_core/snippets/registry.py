"""Import-time catalog discovery (IMPLEMENTATION_PLAN.md §3, WP-03 task 2;
Phase-2 Appendix A.2/A.3 taxonomy + modules).

Every module in the :mod:`semicraft_core.snippets` package that exposes a
module-level :class:`~.contract.SnippetDef` instance is auto-registered, and —
since Phase 2 — every module in the :mod:`semicraft_core.modules` package that
exposes a :class:`~..modules.contract.ModuleDef` instance is registered into the
*same* catalog. Adding a snippet or module file therefore requires no edit here
(that is the whole point: parallel WP agents each drop in one file).

One catalog, two source packages
---------------------------------

Snippets and modules share one registry keyed by ``id``. A duplicate ``id`` is a
hard error *across both packages* (a module and a snippet may not share an id).
Each registered item carries a ``kind`` ("snippet"|"module"|later
ip/subsystem/app) and a ``maturity`` ("stable"|"beta"), read via
:func:`item_kind` / :func:`item_maturity` with getattr-defaulting so pre-taxonomy
snippet files (which declare neither) need no edits (Appendix A.2).

The registry is built lazily on first access and cached, so importing this
module has no import-time side effects beyond what Python already did.
"""

from __future__ import annotations

import importlib
import pkgutil

from pydantic import BaseModel

from .contract import SnippetDef

# The contract/registry modules themselves hold no items; skip them so a stray
# SnippetDef/ModuleDef-shaped helper there could never be mistaken for one.
_SKIP_MODULES = {"contract", "registry"}

# Taxonomy defaults (Appendix A.2). Read via getattr so pre-taxonomy snippet
# files that declare neither field are treated as stable snippets.
_DEFAULT_KIND = "snippet"
_DEFAULT_MATURITY = "stable"


class DuplicateSnippetError(Exception):
    """Two discovered catalog items declare the same ``id`` (a programming bug).

    Named for backcompat; raised for a duplicate id across *either* package
    (snippet-vs-snippet, module-vs-module, or snippet-vs-module).
    """


class UnknownSnippetError(KeyError):
    """No catalog item is registered under the requested ``id``.

    Subclasses :class:`KeyError` so callers can catch either; carries a clean
    message (the API maps this to HTTP 404, IMPLEMENTATION_PLAN §4).
    """


_REGISTRY: dict[str, SnippetDef] | None = None


def item_kind(item: object) -> str:
    """The catalog ``kind`` of a registered item (Appendix A.2).

    ``"snippet"`` when absent (pre-taxonomy snippet files); ``ModuleDef`` sets
    ``"module"`` explicitly.
    """
    return getattr(item, "kind", _DEFAULT_KIND)


def item_maturity(item: object) -> str:
    """The catalog ``maturity`` of a registered item; ``"stable"`` when absent."""
    return getattr(item, "maturity", _DEFAULT_MATURITY)


def _looks_like_def(obj: object) -> bool:
    """True if ``obj`` is a catalog *instance* (snippet or module def).

    Both ``SnippetDef`` and ``ModuleDef`` are structurally identical for the
    fields the registry needs (id/name/description/options_model + generate/
    explain), so the ``SnippetDef`` runtime-checkable protocol matches both.
    """
    if isinstance(obj, type):
        return False
    if not isinstance(obj, SnippetDef):
        return False
    model = getattr(obj, "options_model", None)
    return isinstance(model, type) and issubclass(model, BaseModel)


def _discover_package(pkg, found: dict[str, SnippetDef]) -> None:
    """Import every submodule of ``pkg`` and collect catalog defs into ``found``.

    A duplicate ``id`` — whether within this package or already contributed by
    another — raises :class:`DuplicateSnippetError`.
    """
    for mod_info in pkgutil.iter_modules(pkg.__path__):
        if mod_info.name in _SKIP_MODULES:
            continue
        module = importlib.import_module(f"{pkg.__name__}.{mod_info.name}")
        for value in vars(module).values():
            if not _looks_like_def(value):
                continue
            if value.id in found and found[value.id] is not value:
                raise DuplicateSnippetError(
                    f"duplicate catalog id {value.id!r}: defined by both "
                    f"{type(found[value.id]).__module__} and "
                    f"{type(value).__module__}"
                )
            found[value.id] = value


def _discover() -> dict[str, SnippetDef]:
    """Import both catalog packages and collect the def instances (Appendix A.3)."""
    import semicraft_core.modules as modules_pkg
    import semicraft_core.snippets as snippets_pkg

    found: dict[str, SnippetDef] = {}
    _discover_package(snippets_pkg, found)
    _discover_package(modules_pkg, found)
    return found


def _registry() -> dict[str, SnippetDef]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _discover()
    return _REGISTRY


def get(snippet_id: str) -> SnippetDef:
    """Return the catalog item registered under ``snippet_id``.

    Raises :class:`UnknownSnippetError` if none exists (API -> 404).
    """
    reg = _registry()
    try:
        return reg[snippet_id]
    except KeyError:
        raise UnknownSnippetError(
            f"unknown snippet id {snippet_id!r}; known ids: {sorted(reg)}"
        ) from None


def all() -> list[SnippetDef]:  # noqa: A001 - matches the frozen §3 contract name
    """All registered catalog items, sorted by ``id`` for deterministic ordering.

    Includes both snippets and modules (one catalog, Appendix A.2). Behaviour
    for pre-Phase-2 callers is unchanged only in the degenerate no-modules case;
    with modules present, they appear here too — use :func:`by_kind` to filter.
    """
    return [reg for _id, reg in sorted(_registry().items())]


def by_kind(kind: str) -> list[SnippetDef]:
    """All registered items whose taxonomy ``kind`` equals ``kind``, sorted by id.

    ``by_kind("snippet")`` reproduces the pre-Phase-2 snippet-only catalog;
    ``by_kind("module")`` returns just the Phase-2 modules (Appendix A.2).
    """
    return [item for item in all() if item_kind(item) == kind]


__all__ = [
    "get",
    "all",
    "by_kind",
    "item_kind",
    "item_maturity",
    "DuplicateSnippetError",
    "UnknownSnippetError",
]
