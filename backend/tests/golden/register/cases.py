"""Golden case matrix for the ``register`` snippet (WP-08 layout, WP-05a task).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos; every
reset_style x reset_polarity combination must appear at least once.

This module declares cases only — no snapshot files or runner (WP-08 owns
that infrastructure, landing in parallel).
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default ---------------------------------
    "width_16": {"width": 16},
    "enable_off": {"enable": False},
    "reset_value_5": {"width": 8, "reset_value": 5},
    "clear_input_on": {"clear_input": True},
    # --- reset style x polarity matrix (all four must appear) -------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- pairwise / small combos -------------------------------------------
    "clear_and_enable": {"clear_input": True, "enable": True},
    "clear_no_enable": {"clear_input": True, "enable": False},
    "wide_clear_reset_value": {"width": 32, "clear_input": True, "reset_value": 42},
}

__all__ = ["CASES"]
