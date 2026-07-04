"""Golden case matrix for the ``encoder`` snippet (WP-08 layout, WP-05e task).

``CASES`` maps a case name to an options dict exactly as it would be POSTed to
``/api/v1/generate``. Per IMPLEMENTATION_PLAN §5 WP-08 task 2: defaults case +
one case per option flipping it from default + 2-3 pairwise combos.

Encoder options (semicraft_core/snippets/encoder.py, EncoderOptions):
``kind`` (priority/onehot, default priority), ``num_inputs`` (4/8/16, default
8), ``valid_output`` (default True). Purely combinational: no reset_style x
reset_polarity matrix (not a clocked snippet).
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- single-option flips from default -----------------------------------
    "kind_onehot": {"kind": "onehot"},
    "num_inputs_4": {"num_inputs": 4},
    "num_inputs_16": {"num_inputs": 16},
    "valid_output_off": {"valid_output": False},
    # --- pairwise / small combos ---------------------------------------------
    "onehot_num_inputs_4": {"kind": "onehot", "num_inputs": 4},
    "onehot_valid_off": {"kind": "onehot", "valid_output": False},
    "priority_num_inputs_16_valid_off": {
        "kind": "priority",
        "num_inputs": 16,
        "valid_output": False,
    },
    # --- language-pinned verilog case ----------------------------------------
    "onehot_verilog": {"kind": "onehot", "num_inputs": 8, "language": "verilog"},
}

__all__ = ["CASES"]
