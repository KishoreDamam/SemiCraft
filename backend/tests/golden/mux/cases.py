"""Golden case matrix for the ``mux`` snippet (WP-08 layout).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos; at least
one language-pinned verilog case. Purely combinational: no reset matrix.

Mux options (semicraft_core/snippets/mux.py, MuxOptions): ``num_inputs``
(default 4), ``width`` (default 8), ``impl`` (case/ternary, default case).
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "num_inputs_8": {"num_inputs": 8},
    "width_16": {"width": 16},
    "impl_ternary": {"impl": "ternary"},
    # --- non-power-of-2 num_inputs (documented in assumptions) --------------
    "num_inputs_3_non_pow2": {"num_inputs": 3},
    "num_inputs_5_non_pow2": {"num_inputs": 5},
    # --- pairwise / small combos ---------------------------------------------
    "wide_ternary": {"width": 32, "impl": "ternary"},
    "many_inputs_ternary": {"num_inputs": 16, "impl": "ternary"},
    "num_inputs_3_ternary": {"num_inputs": 3, "impl": "ternary"},
    # --- language-pinned case -------------------------------------------------
    "verilog_ternary": {"impl": "ternary", "language": "verilog"},
}

__all__ = ["CASES"]
