"""Golden case matrix for the ``gray-counter`` module (Phase-2 P2-12).

Same ``CASES`` contract as the snippet golden dirs (tests/golden/conftest.py):
each entry maps a case name to an options dict as POSTed to generate. The
golden runner (test_snapshots.py) calls ``semicraft_core.generate`` — which
works for modules too — and snapshots the RTL only. No snapshot files are
committed here; the orchestrator runs ``pytest --update-golden`` to
materialize them.

GrayCounterOptions: ``width`` (2..32, default 8), ``enable`` (default True),
plus the common clocked fields ``reset_style``/``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "width_2": {"width": 2},
    "width_32": {"width": 32},
    "enable_off": {"enable": False},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- verilog-pinned -----------------------------------------------------
    "verilog_no_enable_wide": {
        "language": "verilog",
        "enable": False,
        "width": 16,
    },
    # --- pairwise / small combos --------------------------------------------
    "narrow_async_high": {
        "width": 3,
        "reset_style": "async",
        "reset_polarity": "active_high",
    },
    "wide_no_enable_sync_low": {
        "width": 24,
        "enable": False,
        "reset_style": "sync",
        "reset_polarity": "active_low",
    },
}

__all__ = ["CASES"]
