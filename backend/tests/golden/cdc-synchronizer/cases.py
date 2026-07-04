"""Golden case matrix for the ``cdc-synchronizer`` snippet (WP-08 layout).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos; every
reset style x polarity combination must appear at least once (clocked
snippet) -- here gated behind use_reset=True since that is when reset exists
at all.

CDC synchronizer options (semicraft_core/snippets/cdc_synchronizer.py,
CdcSynchronizerOptions): ``stages`` (2..4, default 2), ``width`` (1..8,
default 1), ``use_reset`` (default False) plus the inherited
``reset_style``/``reset_polarity`` (only meaningful when use_reset=True).
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "stages_3": {"stages": 3},
    "stages_4": {"stages": 4},
    "width_2": {"width": 2},
    "use_reset_on": {"use_reset": True},
    # --- reset style x polarity matrix (all four, gated on use_reset=True) --
    "reset_sync_active_low": {
        "use_reset": True,
        "reset_style": "sync",
        "reset_polarity": "active_low",
    },
    "reset_sync_active_high": {
        "use_reset": True,
        "reset_style": "sync",
        "reset_polarity": "active_high",
    },
    "reset_async_active_low": {
        "use_reset": True,
        "reset_style": "async",
        "reset_polarity": "active_low",
    },
    "reset_async_active_high": {
        "use_reset": True,
        "reset_style": "async",
        "reset_polarity": "active_high",
    },
    # --- pairwise / small combos ---------------------------------------------
    "wide_multi_stage_reset": {"stages": 4, "width": 2, "use_reset": True},
    "width2_no_reset": {"width": 2, "use_reset": False},
    # --- language-pinned case -------------------------------------------------
    "verilog_reset": {"language": "verilog", "use_reset": True, "stages": 3},
}

__all__ = ["CASES"]
