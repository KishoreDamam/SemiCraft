"""Golden case matrix for the ``debouncer`` module (Phase-2 P2-06).

Same ``CASES`` contract as the snippet golden dirs (tests/golden/conftest.py):
each entry maps a case name to an options dict as POSTed to generate. The
golden runner (test_snapshots.py) calls ``semicraft_core.generate`` — which
works for modules too — and snapshots the RTL only. No snapshot files are
committed here; the orchestrator runs ``pytest --update-golden`` to
materialize them.

DebouncerOptions: ``counter_width`` (4..24, default 16), ``active_level``
(high/low, default high), plus the common clocked fields
``reset_style``/``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "counter_width_4": {"counter_width": 4},
    "counter_width_24": {"counter_width": 24},
    "active_level_low": {"active_level": "low"},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- verilog-pinned -----------------------------------------------------
    "verilog_low_narrow": {"language": "verilog", "active_level": "low", "counter_width": 8},
    # --- pairwise / small combos --------------------------------------------
    "low_async_high_narrow": {
        "active_level": "low",
        "reset_style": "async",
        "reset_polarity": "active_high",
        "counter_width": 8,
    },
    "high_sync_low_wide": {
        "active_level": "high",
        "reset_style": "sync",
        "reset_polarity": "active_low",
        "counter_width": 20,
    },
}

__all__ = ["CASES"]
