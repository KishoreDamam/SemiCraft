"""Golden case matrix for the ``decoder`` snippet (WP-08 layout, WP-05f task).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos.

Decoder options (semicraft_core/snippets/decoder.py, DecoderOptions):
``num_outputs`` (2/4/8/16, default 8), ``enable`` (default True),
``output_polarity`` (active_high/active_low, default active_high). Purely
combinational: no reset_style x reset_polarity matrix (not a clocked snippet).
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "num_outputs_2": {"num_outputs": 2},
    "num_outputs_4": {"num_outputs": 4},
    "num_outputs_16": {"num_outputs": 16},
    "enable_off": {"enable": False},
    "active_low": {"output_polarity": "active_low"},
    # --- pairwise / small combos ---------------------------------------------
    "num_outputs_16_active_low": {"num_outputs": 16, "output_polarity": "active_low"},
    "enable_off_active_low": {"enable": False, "output_polarity": "active_low"},
    "num_outputs_2_enable_off_active_low": {
        "num_outputs": 2,
        "enable": False,
        "output_polarity": "active_low",
    },
    # --- language-pinned verilog case ----------------------------------------
    "active_low_verilog": {"output_polarity": "active_low", "language": "verilog"},
}

__all__ = ["CASES"]
