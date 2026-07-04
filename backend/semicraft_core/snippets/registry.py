"""Import-time snippet discovery (IMPLEMENTATION_PLAN.md §3, WP-03 task 2).

Every module in the :mod:`semicraft_core.snippets` package that exposes a
module-level :class:`~.contract.SnippetDef` instance is auto-registered. Adding
a snippet file therefore requires no edit here (that is the whole point: nine
parallel WP-05 agents each drop in one file).

Discovery walks the package's submodules, imports each, and collects every
module-level object that structurally satisfies :class:`SnippetDef`. Two
snippets sharing an ``id`` is a hard error raised at discovery time — a
programming bug, caught loudly rather than silently shadowing one snippet.

The registry is built lazily on first access and cached, so importing this
module has no import-time side effects beyond what Python already did.
"""

from __future__ import annotations

import importlib
import pkgutil

from pydantic import BaseModel

from .contract import SnippetDef

# The contract/registry modules themselves hold no snippets; skip them so a
# stray SnippetDef-shaped helper there could never be mistaken for a snippet.
_SKIP_MODULES = {"contract", "registry"}


class DuplicateSnippetError(Exception):
    """Two discovered snippets declare the same ``id`` (a programming bug)."""


class UnknownSnippetError(KeyError):
    """No snippet is registered under the requested ``id``.

    Subclasses :class:`KeyError` so callers can catch either; carries a clean
    message (the API maps this to HTTP 404, IMPLEMENTATION_PLAN §4).
    """


_REGISTRY: dict[str, SnippetDef] | None = None


def _looks_like_snippet(obj: object) -> bool:
    """True if ``obj`` is a snippet *instance* (not the class or protocol)."""
    if isinstance(obj, type):
        return False
    # Structural check via the runtime-checkable protocol, plus a concrete
    # options_model sanity check so arbitrary objects don't slip through.
    if not isinstance(obj, SnippetDef):
        return False
    model = getattr(obj, "options_model", None)
    return isinstance(model, type) and issubclass(model, BaseModel)


def _discover() -> dict[str, SnippetDef]:
    """Import every snippet submodule and collect the ``SnippetDef`` instances."""
    import semicraft_core.snippets as pkg

    found: dict[str, SnippetDef] = {}
    for mod_info in pkgutil.iter_modules(pkg.__path__):
        if mod_info.name in _SKIP_MODULES:
            continue
        module = importlib.import_module(f"{pkg.__name__}.{mod_info.name}")
        for value in vars(module).values():
            if not _looks_like_snippet(value):
                continue
            if value.id in found and found[value.id] is not value:
                raise DuplicateSnippetError(
                    f"duplicate snippet id {value.id!r}: defined by both "
                    f"{type(found[value.id]).__module__} and "
                    f"{type(value).__module__}"
                )
            found[value.id] = value
    return found


def _registry() -> dict[str, SnippetDef]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _discover()
    return _REGISTRY


def get(snippet_id: str) -> SnippetDef:
    """Return the snippet registered under ``snippet_id``.

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
    """All registered snippets, sorted by ``id`` for deterministic ordering."""
    return [reg for _id, reg in sorted(_registry().items())]


__all__ = [
    "get",
    "all",
    "DuplicateSnippetError",
    "UnknownSnippetError",
]
