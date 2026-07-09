"""Golden case matrix for the ``clock-divider`` module (Phase-2 P2-07).

Same ``CASES`` contract as the snippet golden dirs (tests/golden/conftest.py):
each entry maps a case name to an options dict as POSTed to generate. The
golden runner (test_snapshots.py) calls ``semicraft_core.generate`` — which
works for modules too — and snapshots the RTL only. No snapshot files are
committed here; the orchestrator runs ``pytest --update-golden`` to
materialize them.

ClockDividerOptions: ``divide_by`` (even, 2..65536, default 2),
``output_enable_style`` (toggle/pulse, default toggle), plus the common
clocked fields ``reset_style``/``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "divide_by_10": {"divide_by": 10},
    "divide_by_256": {"divide_by": 256},
    "pulse_style": {"output_enable_style": "pulse"},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- verilog-pinned -----------------------------------------------------
    "verilog_pulse_wide": {"language": "verilog", "output_enable_style": "pulse", "divide_by": 100},
    # --- pairwise / small combos --------------------------------------------
    "pulse_async_high_wide": {
        "output_enable_style": "pulse",
        "reset_style": "async",
        "reset_polarity": "active_high",
        "divide_by": 1024,
    },
    "toggle_sync_low_max": {
        "output_enable_style": "toggle",
        "reset_style": "sync",
        "reset_polarity": "active_low",
        "divide_by": 65536,
    },
}

__all__ = ["CASES"]
