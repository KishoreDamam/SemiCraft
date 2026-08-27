"""Verilator compile+run gate for the AXI4-Lite I2C master (P4-07).

I2C is the protocol where a testbench most easily agrees with broken hardware:
START and STOP are *edges relative to the clock line*, so getting them wrong
still produces something that looks like a bus transaction. Each mutation
below leaves a plausible waveform.

``sample_on_every_quarter`` is the one that found a real bug. Before the
``phase == 2`` guard existed, a read shifted in four samples per bit — and the
write transaction passed anyway, because its only sample is the ACK and the
slave holds SDA low across all four ACK quarters. Only reading a byte back
exposed it.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import axil_i2c
from semicraft_core.ir.nodes import Const, ConstBase, Ref
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "defaults": {},
    "divisor_1": {"default_divisor": 1},
    "divisor_5": {"default_divisor": 5},
    "divisor_9": {"default_divisor": 9},
    "sync_4_stages": {"input_sync_stages": 4},
    "async_reset": {"reset_style": "async"},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("axil-i2c", options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")
    return run_smoke(tb_path, [rtl_path])


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_i2c_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"I2C run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"The expected bus levels come from _expected_drive in axil_i2c.py, "
        f"written independently of the RTL drivers — if this fails the two "
        f"disagree.\n--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #

_ORIGINAL_SAMPLE = axil_i2c._sample_at_phase2
_ORIGINAL_SCL = axil_i2c.scl_drive_expr


def _sample_on_every_quarter() -> list:
    """Drop the phase guard: sample four times per bit instead of once."""
    inner = _ORIGINAL_SAMPLE()
    # The original wraps its body in `if (phase == 2)`; take the body out.
    return list(inner[0].then)


def _start_without_scl_high():
    """Pull SCL low for the whole START, so SDA never falls with SCL high —
    no real START condition, but a waveform that still looks busy."""
    return Const(1, width=Const(1), base=ConstBase.BIN)


def _never_drive_sda():
    """Release SDA always: every written bit reads as a one."""
    return Const(0, width=Const(1), base=ConstBase.BIN)


def _ignore_clock_stretching():
    """Advance regardless of whether SCL actually went high."""
    from semicraft_core.ir.nodes import BinOp, BinOpKind

    return BinOp(
        BinOpKind.EQ,
        Ref("q_cnt"),
        BinOp(BinOpKind.SUB, Ref("clkdiv_div"), Const(1, width=Const(16), base=ConstBase.BIN)),
    )


_MUTATIONS = {
    "sample_on_every_quarter": ("_sample_at_phase2", _sample_on_every_quarter),
    "start_without_scl_high": ("scl_drive_expr", _start_without_scl_high),
    "sda_never_driven": ("sda_drive_expr", _never_drive_sda),
    "clock_stretching_ignored": ("_advance_expr", _ignore_clock_stretching),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_i2c_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Generating once first forces the registry's lazy import, so the module
    binds the real helpers before they are patched — and the originals above
    are captured at import time, because a mutation that looks its own target
    up through the module recurses forever (P4-06's lesson)."""
    generate_files("axil-i2c", {})

    attr, replacement = _MUTATIONS[name]
    monkeypatch.setattr(axil_i2c, attr, replacement)

    result = _run(tmp_path, {})
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the I2C testbench does "
        f"not actually exercise this property.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )
