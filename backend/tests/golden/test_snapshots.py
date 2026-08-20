"""Golden snapshot runner (IMPLEMENTATION_PLAN.md §5 WP-08 tasks 1 and 3;
extended P2-14 for module doc/tb files).

For every discovered ``cases.py`` (across all snippet dirs) and every
language the case resolves to, calls ``semicraft_core.generate`` and compares
the code byte-exact against ``tests/golden/<snippet-id>/<case>.<sv|v>``.

For module-kind items (Appendix A.2 ``kind == "module"``), ``generate_files()``
also snapshots the ``doc`` file (always) and the ``tb`` file (P2-13; a smoke
TB generator that appends a ``tb``-kind file to ``generate_files()`` when
``semicraft_core.generate.EMIT_TB`` is flipped on). Both interfaces are used
by *path*/``kind`` only — nothing here reaches into P2-13's internals.

Run with ``--update-golden`` to (re)write the snapshot files instead of
asserting: e.g. from the repo root ::

    uv run pytest backend/tests/golden/test_snapshots.py --update-golden

rtl snapshots keep the pre-P2-14 hard-fail-if-missing behavior (every rtl
golden is already committed). doc/tb snapshots are new file kinds with no
committed goldens yet as of this WP (regenerating/committing them is
explicitly out of this WP's DoD), so a missing doc/tb golden **skips** with
the same ``--update-golden`` instructions rather than failing the suite. A
missing *tb* file in the ``generate_files()`` result itself (P2-13 not landed,
or landed but ``EMIT_TB`` still False) also skips — that's an expected,
non-regression state, not a snapshot mismatch.
"""

from __future__ import annotations

import pytest
from semicraft_core import generate
from semicraft_core.generate import generate_files

from .conftest import GoldenCase, discover_golden_cases, golden_case_id

_CASES = discover_golden_cases()
_MODULE_CASES = [c for c in _CASES if c.kind == "module"]


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


@pytest.mark.parametrize(
    "case", _MODULE_CASES, ids=[golden_case_id(c) for c in _MODULE_CASES]
)
def test_snapshot_doc(case: GoldenCase, request: pytest.FixtureRequest) -> None:
    result = generate_files(case.snippet_id, case.resolved_options)
    doc_file = next((f for f in result.files if f.kind == "doc"), None)
    assert doc_file is not None, (
        f"module case {case.snippet_id}/{case.case_name} produced no doc file "
        "from generate_files() (Appendix A.3 requires one for every module)"
    )

    update = request.config.getoption("--update-golden")
    path = case.doc_snapshot_path

    if update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(doc_file.text.encode("utf-8"))
        return

    if not path.is_file():
        pytest.skip(
            f"no committed doc golden at {path} yet (P2-14 infra landed ahead of "
            "the doc snapshot regeneration/review pass). Run --update-golden "
            "locally, review the diff, and commit to turn this into a real gate."
        )

    expected = path.read_bytes()
    actual = doc_file.text.encode("utf-8")
    assert actual == expected, (
        f"generated doc for {case.snippet_id}/{case.case_name} [{case.language}] "
        f"no longer matches {path}. If intentional, regenerate with "
        "--update-golden and review the diff."
    )


@pytest.mark.parametrize(
    "case", _MODULE_CASES, ids=[golden_case_id(c) for c in _MODULE_CASES]
)
def test_snapshot_testplan(case: GoldenCase, request: pytest.FixtureRequest) -> None:
    """Snapshot the P3-07 test-plan document (the second ``doc``-kind file).

    Located by path suffix rather than "the doc file" (that lookup, used
    elsewhere, intentionally resolves to the *datasheet* — the first ``doc``
    entry — per the P3-07 ordering requirement: the test-plan doc is appended
    after it, never displacing it).
    """
    result = generate_files(case.snippet_id, case.resolved_options)
    testplan_file = next(
        (f for f in result.files if f.path.endswith("_testplan.md")), None
    )
    assert testplan_file is not None, (
        f"module case {case.snippet_id}/{case.case_name} produced no test-plan "
        "doc file from generate_files() (P3-07 requires one for every module)"
    )
    assert testplan_file.kind == "doc"

    update = request.config.getoption("--update-golden")
    path = case.testplan_snapshot_path

    if update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(testplan_file.text.encode("utf-8"))
        return

    if not path.is_file():
        pytest.skip(
            f"no committed testplan golden at {path} yet (P3-07 infra landed "
            "ahead of the testplan snapshot regeneration/review pass). Run "
            "--update-golden locally, review the diff, and commit to turn "
            "this into a real gate."
        )

    expected = path.read_bytes()
    actual = testplan_file.text.encode("utf-8")
    assert actual == expected, (
        f"generated testplan for {case.snippet_id}/{case.case_name} "
        f"[{case.language}] no longer matches {path}. If intentional, "
        "regenerate with --update-golden and review the diff."
    )


@pytest.mark.parametrize(
    "case", _MODULE_CASES, ids=[golden_case_id(c) for c in _MODULE_CASES]
)
def test_snapshot_cocotb(case: GoldenCase, request: pytest.FixtureRequest) -> None:
    """Snapshot the cocotb testbench (P3-08) — the second ``tb``-kind file.

    Located by suffix, not by "the tb file": that lookup resolves to the
    SystemVerilog testbench, which stays the default backend and the one the
    compile/run gates exercise.
    """
    result = generate_files(case.snippet_id, case.resolved_options)
    cocotb_file = next((f for f in result.files if f.path.endswith(".py")), None)
    if cocotb_file is None:
        pytest.skip(
            f"no cocotb tb for {case.snippet_id}/{case.case_name} — either the "
            "module has no clock, or semicraft_core.generate.EMIT_COCOTB_TB is "
            "False. Not a regression."
        )
    assert cocotb_file.kind == "tb"

    update = request.config.getoption("--update-golden")
    path = case.cocotb_snapshot_path

    if update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(cocotb_file.text.encode("utf-8"))
        return

    if not path.is_file():
        pytest.skip(
            f"no committed cocotb golden at {path} yet. Run --update-golden "
            "locally, review the diff, and commit to turn this into a gate."
        )

    expected = path.read_bytes()
    actual = cocotb_file.text.encode("utf-8")
    assert actual == expected, (
        f"generated cocotb tb for {case.snippet_id}/{case.case_name} "
        f"[{case.language}] no longer matches {path}. If intentional, "
        "regenerate with --update-golden and review the diff."
    )


@pytest.mark.parametrize(
    "case", _MODULE_CASES, ids=[golden_case_id(c) for c in _MODULE_CASES]
)
def test_snapshot_tb(case: GoldenCase, request: pytest.FixtureRequest) -> None:
    result = generate_files(case.snippet_id, case.resolved_options)
    tb_file = next((f for f in result.files if f.kind == "tb"), None)
    if tb_file is None:
        pytest.skip(
            "generate_files() returned no tb file for "
            f"{case.snippet_id}/{case.case_name} — P2-13's smoke-TB generator "
            "hasn't landed yet, or semicraft_core.generate.EMIT_TB is still "
            "False. Not a regression."
        )

    update = request.config.getoption("--update-golden")
    path = case.tb_snapshot_path

    if update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(tb_file.text.encode("utf-8"))
        return

    if not path.is_file():
        pytest.skip(
            f"no committed tb golden at {path} yet (P2-14 infra landed ahead of "
            "the tb snapshot regeneration/review pass). Run --update-golden "
            "locally, review the diff, and commit to turn this into a real gate "
            "(test_tb_compile.py then picks it up automatically)."
        )

    expected = path.read_bytes()
    actual = tb_file.text.encode("utf-8")
    assert actual == expected, (
        f"generated tb for {case.snippet_id}/{case.case_name} [{case.language}] "
        f"no longer matches {path}. If intentional, regenerate with "
        "--update-golden and review the diff."
    )
