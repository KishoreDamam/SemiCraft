"""Real-verilator integration test (WP-04).

Runs only when a verilator binary is actually on PATH (CI's lint-gate job
installs it via apt; this host has none, per docs/PROGRESS.md environment
facts, so this test is skipped locally).
"""

from __future__ import annotations

import shutil

import pytest
from semicraft_core import generate
from semicraft_core.lint import lint

_HAS_VERILATOR = shutil.which("verilator") is not None


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_counter_default_config_lints_clean(language: str):
    result = generate("counter", {"language": language, "include_wrapper": True})
    report = lint(result.code, language, top="counter")

    assert report.status == "clean", report.messages
