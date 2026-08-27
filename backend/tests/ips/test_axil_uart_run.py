"""Verilator compile+run gate for the AXI4-Lite UART (P4-05b).

A UART testbench is unusually easy to write so that it passes against broken
hardware: drive a byte in, read a byte out, and a great deal can be wrong in
between. The mutations below each break one property the framing depends on,
and every one of them leaves a *well-formed* frame behind — which is exactly
why the checks have to be on the bit pattern and the bit timing, not on
"something came out".

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import axil_uart
from semicraft_core.ir.nodes import Assign, BinOp, BinOpKind, Bit, Concat, Const, Ref, Slice
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "defaults": {},
    "divisor_2": {"default_divisor": 2},
    "divisor_8": {"default_divisor": 8},
    "divisor_13": {"default_divisor": 13},
    "sync_4_stages": {"input_sync_stages": 4},
    "async_reset": {"reset_style": "async"},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("axil-uart", options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")
    return run_smoke(tb_path, [rtl_path])


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_uart_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"UART run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"The transmit bit positions are derived from the FSM in "
        f"axil_uart.py, not observed from a run — if this fails, the "
        f"derivation and the hardware disagree.\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #


def _shift_msb_first() -> list:
    """Transmit the byte backwards. Still a valid-looking 8N1 frame."""
    return [
        Assign(Ref("uart_tx"), Bit(Ref("tx_shift"), Const(7))),
        Assign(
            Ref("tx_shift"),
            Concat([Slice(Ref("tx_shift"), Const(6), Const(0)), Const(0, width=Const(1))]),
        ),
    ]


def _no_half_period(counter: str):
    """Sample on bit boundaries instead of mid-bit.

    The receiver still frames and still delivers a byte — it just samples
    where the line is changing, which is the classic UART bug that works in a
    clean testbench and fails on real wire.
    """
    return BinOp(
        BinOpKind.EQ,
        Ref(counter),
        BinOp(BinOpKind.SUB, Ref("bauddiv_div"), Const(1, width=Const(16))),
    )


def _bit_period_off_by_one(counter: str):
    """Hold every bit one clock too long."""
    return BinOp(BinOpKind.EQ, Ref(counter), Ref("bauddiv_div"))


def _never_flag_received(sampled) -> list:
    """Deliver the byte but never raise rx_valid."""
    return [
        Assign(Ref("rx_state"), Const(0, width=Const(2))),
        Assign(Ref("rxdata_data"), Ref("rx_shift")),
    ]


_MUTATIONS = {
    "transmits_msb_first": ("_tx_shift_out", _shift_msb_first),
    "samples_on_bit_edges": ("_half_tick", _no_half_period),
    "bit_period_off_by_one": ("_tick", _bit_period_off_by_one),
    "rx_valid_never_set": ("_rx_complete", _never_flag_received),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_uart_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Generating once first forces the registry's lazy import, so the module
    binds the real helpers before they are patched — otherwise the expected
    bit pattern would be derived from the mutated generator and agree with it."""
    generate_files("axil-uart", {})

    attr, replacement = _MUTATIONS[name]
    monkeypatch.setattr(axil_uart, attr, replacement)

    result = _run(tmp_path, {})
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the UART testbench "
        f"does not actually exercise this property, so a real regression here "
        f"would ship silently.\n--- stdout tail ---\n{result.stdout_tail}"
    )
