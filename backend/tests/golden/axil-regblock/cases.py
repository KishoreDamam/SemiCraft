"""Golden case matrix for the ``axil-regblock`` IP (Phase-4 P4-02).

Same ``CASES`` contract as every other golden dir (tests/golden/conftest.py).
An IP takes the identical ``generate_files`` path a module does, so each case
snapshots rtl + datasheet + SV testbench + cocotb testbench + test plan.

The axes worth pinning are the ones that change the *shape* of the emitted
decode, not just a width:

- ``split_fields`` — sub-fields with reserved gaps vs one whole-word field.
  With it off there are no reserved bits, so the SLVERR-on-reserved path
  disappears from the RTL entirely.
- ``data_width`` — 64 doubles the strobe count and the mask expansion.
- register counts — including the degenerate "scratch only" map, which is the
  smallest legal configuration.
- ``include_scratch`` off — removes the only full-width writable register,
  which is the case where ``wdata``/``wstrb`` coverage is sparsest and the
  reserved-bit check is what keeps the module lint-clean.
- ``reset_style`` — sync vs async skeleton. There is deliberately no polarity
  axis: AXI4-Lite fixes the reset active-low, so the option does not exist.
"""

from __future__ import annotations

CASES: dict[str, dict] = {
    "defaults": {},
    # --- field layout --------------------------------------------------------
    "whole_word_fields": {"split_fields": False},
    # --- bus width -----------------------------------------------------------
    "data_width_64": {"data_width": 64},
    # --- map shape -----------------------------------------------------------
    "no_scratch": {"include_scratch": False},
    "scratch_only": {
        "control_regs": 0,
        "status_regs": 0,
        "irq_regs": 0,
        "command_regs": 0,
    },
    "many_registers": {
        "control_regs": 2,
        "status_regs": 2,
        "irq_regs": 2,
        "command_regs": 2,
    },
    # --- reset skeleton ------------------------------------------------------
    "async_reset": {"reset_style": "async"},
    # --- verilog-pinned combination -----------------------------------------
    "verilog_wide_whole_word": {
        "language": "verilog",
        "data_width": 64,
        "split_fields": False,
    },
}

__all__ = ["CASES"]
