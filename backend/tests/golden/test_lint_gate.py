"""Lint gate over every golden snapshot (IMPLEMENTATION_PLAN.md §5 WP-08 task 4).

Runs ``semicraft_core.lint.verilator.lint()`` (WP-04, landing in parallel with
this WP) over every committed golden snapshot file and asserts status
``"clean"``. Two independent skip conditions, checked separately so the test
degrades gracefully regardless of arrival order / host capability:

- WP-04's module isn't present yet -> import lazily, ``pytest.skip`` if it's
  missing entirely (``ModuleNotFoundError``).
- the ``verilator`` binary itself is absent (true on this Windows dev host;
  present in CI) -> ``pytest.skip`` rather than asserting "unavailable" is
  "clean" (the module already degrades gracefully per its own contract; a
  missing binary is an environment fact, not a regression).

Snapshot files are read directly from disk (not regenerated), matching the
task's framing: "lint every golden file."
"""

from __future__ import annotations

import re
import shutil

import pytest

from .conftest import GoldenCase, discover_golden_cases, golden_case_id

_CASES = discover_golden_cases()

_MODULE_NAME_RE = re.compile(r"^\s*module\s+(\w+)", re.MULTILINE)


def _lint_module():
    try:
        from semicraft_core.lint import verilator
    except ModuleNotFoundError:
        pytest.skip("semicraft_core.lint.verilator not available yet (WP-04 pending)")
    return verilator


def _top_module_name(code: str, fallback: str) -> str:
    """Extract the actual top module name from ``module <name>`` in the code.

    Falls back to the snippet id (dashes -> underscores) for fragment-mode
    snapshots, which have no ``module`` line to parse.
    """
    m = _MODULE_NAME_RE.search(code)
    return m.group(1) if m else fallback.replace("-", "_")


@pytest.mark.parametrize("case", _CASES, ids=[golden_case_id(c) for c in _CASES])
def test_golden_snapshot_lints_clean(case: GoldenCase) -> None:
    if shutil.which("verilator") is None:
        pytest.skip("verilator binary not installed on this host")

    verilator = _lint_module()

    path = case.snapshot_path
    if not path.is_file():
        pytest.fail(
            f"missing golden snapshot {path}; run test_snapshots.py --update-golden first"
        )

    code = path.read_text(encoding="utf-8")
    if "module " not in code:
        pytest.skip(
            f"{path} is fragment-mode output (no module/endmodule); "
            "verilator.lint() requires a full module (see lint/verilator.py docstring)"
        )

    top = _top_module_name(code, case.snippet_id)
    report = verilator.lint(code, language=case.language, top=top)
    assert report.status == "clean", (
        f"{path} did not lint clean: "
        f"{[(m.severity, m.code, m.line, m.text) for m in report.messages]}"
    )
