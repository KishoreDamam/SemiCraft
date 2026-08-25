"""Verilator compile+run gate for the synchronous FIFO (P4-03a).

Same two-part shape as the AXI register block's gate: configurations that must
pass, and deliberately broken generators that must fail. A FIFO testbench is
easy to write so that it only ever exercises the happy path — push a few
words, pop them back — and never touches the two things that actually make a
FIFO correct: flow control at the boundaries, and ordering.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import sync_fifo
from semicraft_core.ir.nodes import Const, ConstBase, Ref, Slice
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "defaults": {},
    "depth_2_width_1": {"depth": 2, "width": 1},
    "no_count_output": {"depth": 4, "count_output": False},
    "wide": {"depth": 64, "width": 32},
    "deep": {"depth": 1024, "width": 16},
    "async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("sync-fifo", options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")
    return run_smoke(tb_path, [rtl_path])


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_sync_fifo_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"sync FIFO run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"Expected values come from _FifoModel, derived from the accept/ignore "
        f"rules — if this fails the model and the RTL disagree. Fix whichever "
        f"is wrong; do not copy what the simulator printed.\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
def test_deep_fifo_testbench_stays_small(tmp_path: Path) -> None:
    """Filling a deep FIFO must not emit one driven cycle per entry.

    The clock divider once produced a 65k-line testbench that timed out the
    compile gate. Here the fill and drain hold their enable for a single driven
    cycle and then idle, which ``generate_tb`` coalesces into one ``repeat``.
    """
    res = generate_files("sync-fifo", {"depth": 1024, "width": 16})
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    assert len(tb.text.splitlines()) < 400
    assert "repeat (1024)" in tb.text


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #


def _always_true(_expr):
    """Neuter the `!full` / `!empty` guards, allowing overflow and underflow."""
    return Const(1, width=Const(1), base=ConstBase.BIN)


def _read_from_the_write_pointer(pointer: str, addr_bits: int):
    """Index the memory with wptr on both ports, destroying FIFO ordering."""
    return Slice(Ref("wptr"), Const(addr_bits - 1), Const(0))


def _never_full(_addr_bits: int):
    return Const(0, width=Const(1), base=ConstBase.BIN)


def _never_empty():
    return Const(0, width=Const(1), base=ConstBase.BIN)


_MUTATIONS = {
    "flow_control_removed": ("_not", _always_true),
    "read_index_wrong": ("_index", _read_from_the_write_pointer),
    "full_stuck_low": ("_full_expr", _never_full),
    "empty_stuck_low": ("_empty_expr", _never_empty),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_fifo_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Each mutation breaks one defining FIFO property; the gate must notice.

    Generating once first forces the registry's lazy import, so ``sync_fifo``
    binds the real helpers before they are patched and only the *hardware*
    becomes wrong — the reference model must stay correct or the mutation
    hides itself by agreeing with the broken RTL.
    """
    generate_files("sync-fifo", {})

    attr, replacement = _MUTATIONS[name]
    monkeypatch.setattr(sync_fifo, attr, replacement)

    result = _run(tmp_path, {})
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the FIFO testbench does "
        f"not actually exercise this property, so a real regression would ship "
        f"silently.\n--- stdout tail ---\n{result.stdout_tail}"
    )
