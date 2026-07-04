"""Golden case matrix for the ``demux`` snippet (WP-08 layout).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos; at least
one language-pinned verilog case. Purely combinational: no reset matrix.

Demux options (semicraft_core/snippets/demux.py, DemuxOptions): ``num_outputs``
(default 4), ``width`` (default 8).
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "num_outputs_8": {"num_outputs": 8},
    "width_16": {"width": 16},
    # --- non-power-of-2 num_outputs (documented in assumptions) -------------
    "num_outputs_3_non_pow2": {"num_outputs": 3},
    "num_outputs_5_non_pow2": {"num_outputs": 5},
    # --- pairwise / small combos ---------------------------------------------
    "wide_many_outputs": {"width": 32, "num_outputs": 16},
    "num_outputs_3_wide": {"num_outputs": 3, "width": 32},
    # --- language-pinned case -------------------------------------------------
    "verilog_num_outputs_8": {"num_outputs": 8, "language": "verilog"},
}

__all__ = ["CASES"]
