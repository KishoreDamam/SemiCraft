"""Snippet framework and snippet implementations (WP-03, WP-05a..i).

Public surface:

- the frozen contract types (:mod:`.contract`): ``SnippetDef``,
  ``ExplanationDoc``, ``SignalDoc``, ``CommonOptions``, ``ClockedOptions``,
  ``NamingOptions``;
- the registry (:mod:`.registry`): ``get(id)``, ``all()``.

Individual snippet modules (``counter``, and the WP-05 additions) are
discovered automatically by the registry; they need not be imported here.
"""

from __future__ import annotations

from . import registry
from .contract import (
    ClockedOptions,
    CommonOptions,
    ExplanationDoc,
    NamingOptions,
    SignalDoc,
    SnippetDef,
)

__all__ = [
    "registry",
    "SnippetDef",
    "ExplanationDoc",
    "SignalDoc",
    "CommonOptions",
    "ClockedOptions",
    "NamingOptions",
]
