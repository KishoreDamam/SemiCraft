"""Golden case matrix for the ``fsm`` snippet (WP-08 layout).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos; every
reset_style x reset_polarity combination appears at least once (clocked
snippet). At least one case pins ``language: verilog`` (localparam encoding
path); the rest default to SystemVerilog.

FSM options (semicraft_core/snippets/fsm.py, FsmOptions): ``states`` (default
["idle","run","done"]), ``encoding`` (binary/onehot/gray, default binary),
``machine`` (moore/mealy, default moore), ``reset_state`` (default first
state), ``outputs`` (default []), plus common clocked reset fields.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "encoding_onehot": {"encoding": "onehot"},
    "encoding_gray": {"encoding": "gray"},
    "machine_mealy": {"machine": "mealy"},
    "with_outputs": {"outputs": ["busy", "done_o"]},
    "reset_state_run": {"reset_state": "run"},
    "five_states": {"states": ["idle", "load", "run", "flush", "done"]},
    # --- reset style x polarity matrix (all four must appear) ---------------
    "reset_sync_active_low": {"reset_style": "sync", "reset_polarity": "active_low"},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_low": {"reset_style": "async", "reset_polarity": "active_low"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    # --- language-pinned verilog case (localparam encoding path) ------------
    "verilog_onehot_outputs": {
        "language": "verilog",
        "encoding": "onehot",
        "outputs": ["busy", "ready"],
    },
    # --- pairwise / small combos ---------------------------------------------
    "mealy_outputs_gray": {
        "machine": "mealy",
        "encoding": "gray",
        "outputs": ["valid"],
    },
    "onehot_five_states_async_high": {
        "encoding": "onehot",
        "states": ["s0", "s1", "s2", "s3", "s4"],
        "reset_style": "async",
        "reset_polarity": "active_high",
    },
}

__all__ = ["CASES"]
