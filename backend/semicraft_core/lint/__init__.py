"""Verilator lint integration (WP-04).

Public surface: :func:`lint`, :class:`LintReport`, :class:`LintMessage`.
See :mod:`.verilator` for the full contract (fragment-mode note, graceful
degradation, ``--timing`` decision).
"""

from __future__ import annotations

from .verilator import LintMessage, LintReport, lint

__all__ = ["lint", "LintReport", "LintMessage"]
