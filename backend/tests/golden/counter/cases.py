"""Golden case matrix for the ``counter`` snippet (WP-08 layout).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos; every
reset_style x reset_polarity combination must appear at least once (clocked
snippet).

Counter options (semicraft_core/snippets/counter.py, CounterOptions):
``width`` (default 8), ``direction`` (up/down/updown, default up), ``enable``
(default True), ``wrap`` (overflow/saturate, default overflow), ``reset_value``
(default 0), plus the common clocked fields ``reset_style``/``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "width_16": {"width": 16},
    "direction_down": {"direction": "down"},
    "direction_updown": {"direction": "updown"},
    "enable_off": {"enable": False},
    "wrap_saturate": {"wrap": "saturate"},
    "reset_value_5": {"width": 8, "reset_value": 5},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- pairwise / small combos ---------------------------------------------
    "updown_saturate": {"direction": "updown", "wrap": "saturate"},
    "down_saturate_no_enable": {"direction": "down", "wrap": "saturate", "enable": False},
    "wide_updown_reset_value": {"width": 32, "direction": "updown", "reset_value": 42},
}

__all__ = ["CASES"]
