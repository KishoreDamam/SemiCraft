"""Run gate for the cocotb backend (P3-08, beta).

Generates each module's RTL and cocotb testbench, then **executes** the Python
against the RTL under Verilator via cocotb's own runner, asserting the test
passes. This is the check that matters: a generated testbench that parses and
reads correctly but does not run is the "artifact that exists but verifies
nothing" pattern this project has repeatedly had to dig out.

Skips (never fails) when the toolchain is absent — no ``verilator`` binary, or
no importable ``cocotb`` — mirroring ``tests/golden/test_tb_run.py``.

Scope: the ``defaults`` case per module, not the full option matrix. The SV
backend is the one under exhaustive golden/matrix coverage; this gate exists to
prove the alternative backend genuinely runs, and each case costs a full
Verilator build.

Toolchain pin: cocotb **1.x**. cocotb 2.x renamed the runner to
``cocotb_tools.runner`` and, more importantly, its Verilator VPI shim calls
``VerilatedVpi::doInertialPuts()``/``evalNeeded()``, absent from Verilator
5.020 — the newest available from apt on Ubuntu noble and the version this
project's sandbox and CI use, so cocotb 2.0.1 fails to build against it.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest
from semicraft_core.generate import _render_rtl, config_hash
from semicraft_core.snippets import registry
from semicraft_core.tb.cocotb_tb import cocotb_tb_filename, generate_cocotb_tb

_HAS_VERILATOR = shutil.which("verilator") is not None
try:  # pragma: no cover - import probe
    import cocotb  # noqa: F401

    _HAS_COCOTB = True
except ImportError:  # pragma: no cover
    _HAS_COCOTB = False

_TIMEOUT_SECONDS = 300
# Modules *and* IPs: both emit a cocotb testbench from the same TbSpec, so
# covering only modules would leave every IP's generated Python committed
# as a golden and never executed.
MODULE_IDS = [d.id for d in registry.by_kind("module")] + [
    d.id for d in registry.by_kind("ip")
]

pytestmark = [
    pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed"),
    pytest.mark.skipif(not _HAS_COCOTB, reason="cocotb not installed"),
]


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_generated_cocotb_tb_runs(item_id: str) -> None:
    item = registry.get(item_id)
    opts = item.options_model.model_validate({})
    chash = config_hash(item_id, opts.model_dump(mode="json"))
    rtl_path, rtl_text, _lang, rtl_module = _render_rtl(item, opts, chash)

    tb_text = generate_cocotb_tb(item, opts, rtl_module)
    if not tb_text:
        pytest.skip(f"{item_id} has no clock, so no cocotb TB is generated")

    top = rtl_module.name
    tb_name = cocotb_tb_filename(top)

    with tempfile.TemporaryDirectory(prefix="semicraft-cocotb-") as tmp:
        work = Path(tmp)
        (work / rtl_path).write_text(rtl_text, encoding="utf-8")
        (work / tb_name).write_text(tb_text, encoding="utf-8")
        (work / "run.py").write_text(
            textwrap.dedent(
                f"""
                from pathlib import Path
                from cocotb.runner import get_runner

                runner = get_runner("verilator")
                runner.build(
                    verilog_sources=[Path({rtl_path!r})],
                    hdl_toplevel={top!r},
                    build_dir="sim_build",
                    build_args=["--timing"],
                    always=True,
                )
                runner.test(
                    hdl_toplevel={top!r},
                    test_module={tb_name[:-3]!r},
                    build_dir="sim_build",
                )
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [sys.executable, "run.py"],
            cwd=work,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )

    tail = "\n".join((result.stdout + result.stderr).splitlines()[-40:])
    assert result.returncode == 0, (
        f"cocotb run for {item_id} exited {result.returncode}\n--- output tail ---\n{tail}"
    )
    # cocotb's runner exits 0 even when a test fails unless results are checked,
    # so assert on the regression summary and the module's own pass marker
    # rather than trusting the exit code alone.
    assert "FAIL=0" in result.stdout + result.stderr, (
        f"cocotb reported failures for {item_id}\n--- output tail ---\n{tail}"
    )
    assert f"SMOKE PASS: {top}" in result.stdout + result.stderr, (
        f"cocotb run for {item_id} never printed its pass marker\n"
        f"--- output tail ---\n{tail}"
    )
