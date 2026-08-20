"""Verilator compile+run gate for the reference IP's generated testbench (P4-01).

Why this exists: P4-01's claim is that an IP goes through the *whole*
pipeline, not just the parts a unit test can reach. Text assertions cannot
tell a correct register decode from a plausible-looking one — only running it
can. Every configuration is exercised, not just the defaults, because a
defaults-only gate is precisely what let seventeen testbench failures and an
8-bit-vs-1-bit assertion width bug through earlier in this project.

Skips when Verilator is absent (the Windows dev host), so this is a no-op
locally and real work in CI.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.sim import run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

# Every option that changes the emitted RTL or testbench. `status_register`
# changes the read decode *and* the port list; the reset options change the
# always_ff skeleton and the SVA guard; the naming style renames every net in
# both the RTL and the TB, which is the case the name map has to get right.
_CASES = {
    "defaults": {},
    "no_status": {"status_register": False},
    "reset_sync_active_high": {"reset_style": "sync", "reset_polarity": "active_high"},
    "reset_async_active_high": {"reset_style": "async", "reset_polarity": "active_high"},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_reference_ip_tb_runs(case: str, registered_ip, tmp_path: Path) -> None:
    res = generate_files(registered_ip.id, _CASES[case])
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))

    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")

    result = run_smoke(tb_path, [rtl_path])

    assert result.status == "pass", (
        f"reference IP TB run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"Expected values in the reference IP's tb_spec are derived from the "
        f"register decode — if this fails, one of the two is wrong; do not "
        f"'fix' it by copying what the simulator printed.\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )
