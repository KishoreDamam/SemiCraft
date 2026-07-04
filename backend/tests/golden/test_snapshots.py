"""Golden snapshot runner (IMPLEMENTATION_PLAN.md §5 WP-08 tasks 1 and 3).

For every discovered ``cases.py`` (across all snippet dirs) and every
language the case resolves to, calls ``semicraft_core.generate`` and compares
the code byte-exact against ``tests/golden/<snippet-id>/<case>.<sv|v>``.

Run with ``--update-golden`` to (re)write the snapshot files instead of
asserting: e.g. from the repo root ::

    uv run pytest backend/tests/golden/test_snapshots.py --update-golden

Missing snapshots fail with an explicit instruction to run that flag.
"""

from __future__ import annotations

import pytest
from semicraft_core import generate

from .conftest import GoldenCase, discover_golden_cases, golden_case_id

_CASES = discover_golden_cases()


@pytest.mark.parametrize("case", _CASES, ids=[golden_case_id(c) for c in _CASES])
def test_snapshot(case: GoldenCase, request: pytest.FixtureRequest) -> None:
    result = generate(case.snippet_id, case.resolved_options)
    code = result.code

    update = request.config.getoption("--update-golden")
    path = case.snapshot_path

    if update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(code.encode("utf-8"))
        return

    if not path.is_file():
        pytest.fail(
            f"missing golden snapshot {path}\n"
            "Run with --update-golden to generate it, e.g.:\n"
            "  uv run pytest backend/tests/golden/test_snapshots.py --update-golden"
        )

    expected = path.read_bytes()
    actual = code.encode("utf-8")
    assert actual == expected, (
        f"generated output for {case.snippet_id}/{case.case_name} "
        f"[{case.language}] no longer matches {path}. If this change is "
        "intentional, regenerate with --update-golden and review the diff."
    )
