"""Verilator compile+run gate for the AXI4-Lite SPI master (P4-06).

SPI is where a testbench most easily lies to you: exchange a byte, get a byte,
and the mode can be wrong, the bit order can be wrong, and the clock can be
wrong, all while producing something that looks like a transfer. Each mutation
below leaves a *plausible* waveform behind.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import axil_spi
from semicraft_core.ir.nodes import (
    Assign,
    Bit,
    Concat,
    Const,
    ConstBase,
    Ref,
    Slice,
)
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "mode_00": {},
    "mode_01": {"cpha": 1},
    "mode_10": {"cpol": 1},
    "mode_11": {"cpol": 1, "cpha": 1},
    "divisor_1": {"default_divisor": 1},
    "divisor_7": {"default_divisor": 7},
    "sync_4_stages": {"input_sync_stages": 4},
    "async_reset": {"reset_style": "async"},
    "verilog_mode_11": {"language": "verilog", "cpol": 1, "cpha": 1},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("axil-spi", options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")
    return run_smoke(tb_path, [rtl_path])


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_spi_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"SPI run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"The mosi bit positions and sample cycles are derived from the FSM in "
        f"axil_spi.py — if this fails, the derivation and the hardware "
        f"disagree.\n--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #


def _lsb_first(name: str):
    """Shift the transmit register the other way — still eight clean bits."""
    return Concat(
        [
            Const(0, width=Const(1), base=ConstBase.BIN),
            Slice(Ref(name), Const(7), Const(1)),
        ]
    )


def _wrong_phase(opts):
    """Sample on the other edge — mode N0 behaving as N1, and vice versa."""
    from semicraft_core.ir.nodes import BinOp, BinOpKind

    return BinOp(
        BinOpKind.EQ,
        Bit(Ref("edge_cnt"), Const(0)),
        Const(1 - opts.cpha, width=Const(1)),
    )


#: Captured before any patching. Reaching for ``axil_spi._transfer_body``
#: inside the mutation would find the mutation itself, which recurses until
#: the interpreter gives up — a trap worth naming, because the traceback blames
#: the generator rather than the test.
_ORIGINAL_TRANSFER_BODY = axil_spi._transfer_body


def _clock_never_toggles(opts, sampled):
    """Do everything except move sclk."""
    body = _ORIGINAL_TRANSFER_BODY(opts, sampled)
    return [stmt for stmt in body if not _is_sclk_toggle(stmt)]


def _is_sclk_toggle(stmt) -> bool:
    return (
        isinstance(stmt, Assign)
        and isinstance(stmt.lhs, Ref)
        and stmt.lhs.name == "sclk_int"
    )


def _cs_ignores_control(opts):  # noqa: ARG001
    """Leave chip select asserted forever."""
    return Const(0, width=Const(1), base=ConstBase.BIN)


_MUTATIONS = {
    "transmits_lsb_first": ("_shift_left", _lsb_first, {}),
    "samples_on_the_wrong_edge": ("_is_sample_edge", _wrong_phase, {}),
    "clock_never_toggles": ("_transfer_body", _clock_never_toggles, {}),
    "wrong_phase_mode_11": ("_is_sample_edge", _wrong_phase, {"cpol": 1, "cpha": 1}),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_spi_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Generating once first forces the registry's lazy import, so the module
    binds the real helpers before they are patched."""
    generate_files("axil-spi", {})

    attr, replacement, options = _MUTATIONS[name]
    monkeypatch.setattr(axil_spi, attr, replacement)

    result = _run(tmp_path, options)
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the SPI testbench does "
        f"not actually exercise this property.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )
