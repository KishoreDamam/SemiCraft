"""Golden case matrix for the ``rr-arbiter`` module (Phase-2 P2-10).

Same ``CASES`` contract as the snippet golden dirs (tests/golden/conftest.py):
each entry maps a case name to an options dict as POSTed to generate. The
golden runner (test_snapshots.py) calls ``semicraft_core.generate`` — which
works for modules too — and snapshots the RTL only. No snapshot files are
committed here; the orchestrator runs ``pytest --update-golden`` to
materialize them.

RrArbiterOptions: ``num_requesters`` (2..16, default 4), ``grant_style``
(registered/combinational, default registered), ``hold_grant`` (bool, default
False), plus the common clocked fields ``reset_style``/``reset_polarity``.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "num_requesters_2": {"num_requesters": 2},
    "num_requesters_8": {"num_requesters": 8},
    "num_requesters_16": {"num_requesters": 16},
    "combinational": {"grant_style": "combinational"},
    "hold_grant": {"hold_grant": True},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- verilog-pinned -----------------------------------------------------
    "verilog_comb_hold": {
        "language": "verilog",
        "grant_style": "combinational",
        "hold_grant": True,
        "num_requesters": 8,
    },
    # --- pairwise / small combos --------------------------------------------
    "hold_async_high_wide": {
        "hold_grant": True,
        "reset_style": "async",
        "reset_polarity": "active_high",
        "num_requesters": 16,
    },
    "comb_sync_low_narrow": {
        "grant_style": "combinational",
        "reset_style": "sync",
        "reset_polarity": "active_low",
        "num_requesters": 2,
    },
}

__all__ = ["CASES"]
