"""Golden case matrix for the ``comparator`` snippet (WP-08 layout).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos.

Comparator options (semicraft_core/snippets/comparator.py, ComparatorOptions):
``width`` (default 8), ``signed_compare`` (default False), ``outputs``
(subset of eq/ne/lt/le/gt/ge, default ["eq", "lt", "gt"]). Purely
combinational: no reset_style/reset_polarity matrix required.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "width_16": {"width": 16},
    "signed_compare_on": {"signed_compare": True},
    "outputs_eq_only": {"outputs": ["eq"]},
    "outputs_all": {"outputs": ["eq", "ne", "lt", "le", "gt", "ge"]},
    # --- pairwise / small combos ---------------------------------------------
    "signed_wide": {"width": 32, "signed_compare": True},
    "signed_all_outputs": {"signed_compare": True, "outputs": ["eq", "ne", "lt", "le", "gt", "ge"]},
    "outputs_order_independence": {"width": 8, "outputs": ["gt", "eq", "lt"]},
    # --- language-pinned case -------------------------------------------------
    "verilog_signed": {"language": "verilog", "signed_compare": True, "width": 12},
}

__all__ = ["CASES"]
