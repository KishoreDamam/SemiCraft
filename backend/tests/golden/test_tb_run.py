"""Verilator run gate over every committed golden TB (P3-03a).

Upgrades ``test_tb_compile.py``'s compile-only check into an actual run:
every discovered ``*_tb.sv`` golden is compiled *and executed* via
``semicraft_core.sim.run_smoke``, and the gate asserts ``status == "pass"``
(exit 0 **and** the ``SMOKE PASS`` marker — see ``sim/runner.py`` docstring).

This is the first time these TBs are ever actually run (P2-14 only compiled
them). Some may genuinely fail: a check's expected value could be wrong (the
module author predicted it by hand), or a check could sample before reset
deassertion — bugs that compilation can't catch. Because this environment has
no verilator (Windows dev host) these failures are only visible from CI logs,
so every assertion here embeds the full ``SimResult`` stdout/stderr tail: a
CI failure must be diagnosable from the log alone, without rerunning locally.

Advisory in CI for now (``continue-on-error: true`` in ci.yml) until any
real check-value bugs this first run surfaces are fixed; the compile gate in
test_tb_compile.py remains a hard gate throughout.

CI-time control (Key risks: "sim wall-clock in CI", plan Phase 3): running
the full matrix (~28 tb/rtl pairs) doubles compile+run cost per TB across
every case of every module. Default CI (and local runs) only exercise the
``defaults`` case per module (one compile+run per module); set
``SEMICRAFT_TB_RUN_ALL=1`` to run the full matrix (e.g. before flipping this
gate to enforcing).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from semicraft_core.sim import run_smoke

from .conftest import GOLDEN_ROOT
from .test_tb_compile import _matching_rtl, discover_tb_goldens

_HAS_VERILATOR = shutil.which("verilator") is not None
_RUN_ALL = os.environ.get("SEMICRAFT_TB_RUN_ALL") == "1"


def _select_tb_goldens() -> list[Path]:
    """All discovered tb goldens, or just the ``defaults`` case per module.

    ``SEMICRAFT_TB_RUN_ALL=1`` opts into the full matrix; unset (the CI and
    local default) restricts to snapshot names starting with ``defaults.``
    to keep this gate's wall-clock cost down (one compile+run per module
    rather than one per case).
    """
    all_goldens = discover_tb_goldens()
    if _RUN_ALL:
        return all_goldens
    return [p for p in all_goldens if p.name.startswith("defaults.")]


_TB_GOLDENS = _select_tb_goldens()
_TB_IDS = [str(p.relative_to(GOLDEN_ROOT)) for p in _TB_GOLDENS]


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("tb_path", _TB_GOLDENS, ids=_TB_IDS)
def test_golden_tb_runs(tb_path: Path) -> None:
    rtl_path = _matching_rtl(tb_path)
    if not rtl_path.is_file():
        pytest.fail(
            f"{tb_path} has no matching rtl golden at {rtl_path} "
            "(tb/rtl goldens must be regenerated together)"
        )

    result = run_smoke(tb_path, [rtl_path])

    assert result.status == "pass", (
        f"golden TB run gate: {tb_path.relative_to(GOLDEN_ROOT)} did not pass "
        f"(status={result.status!r}, exit_code={result.exit_code}, "
        f"duration={result.duration_s:.2f}s). This TB was previously only "
        f"compile-checked (P2-14) and is now being run for the first time — "
        f"if this is a genuine check-value bug, fix the module's TbSpec "
        f"expected values (see docs/TB_SPEC.md), not this test.\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )
