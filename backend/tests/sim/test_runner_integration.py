"""Real-verilator integration test for semicraft_core.sim.runner (P3-03a).

Runs only when a verilator binary is actually on PATH (CI's lint-gate job
installs it via apt; this host has none, so it's skipped locally — same
convention as ``backend/tests/lint/test_verilator_integration.py``).

Uses ``edge-detector`` (a module with a real smoke ``TbSpec``, unlike
``counter`` which is a plain snippet with no TB) as the one real end-to-end
check that :func:`run_smoke` correctly compiles-and-runs a freshly generated
TB against its freshly generated RTL and reads the ``SMOKE PASS`` marker.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.sim import run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
def test_edge_detector_smoke_tb_compiles_and_passes(tmp_path: Path) -> None:
    result = generate_files("edge-detector", {})
    rtl_file = next(f for f in result.files if f.kind == "rtl")
    tb_file = next(f for f in result.files if f.kind == "tb")

    rtl_path = tmp_path / rtl_file.path
    tb_path = tmp_path / tb_file.path
    rtl_path.write_text(rtl_file.text, encoding="utf-8")
    tb_path.write_text(tb_file.text, encoding="utf-8")

    sim_result = run_smoke(tb_path, [rtl_path])

    assert sim_result.status == "pass", (
        f"expected 'pass', got '{sim_result.status}' "
        f"(exit_code={sim_result.exit_code}, duration={sim_result.duration_s:.2f}s):\n"
        f"--- stdout tail ---\n{sim_result.stdout_tail}\n"
        f"--- stderr tail ---\n{sim_result.stderr_tail}"
    )
