"""Every Verilator-gated test is named by a CI workflow (P4 follow-up).

Why this exists: ``backend/tests/sim/test_runner_integration.py`` had **never
run in CI**. It skips itself when Verilator is absent, so the plain ``pytest``
job (which installs no Verilator) reported it as a skip, and the Verilator job
runs an explicit, hand-maintained list of paths that did not include it. A test
that skips everywhere is indistinguishable from a test that passes everywhere,
which is the failure mode this whole project keeps finding — and it was the
integration test for ``run_smoke``, the function every per-IP run gate depends
on.

Adding the missing line would have fixed one instance. This closes the gap that
let it through: the CI job's path list is enumerated by hand, so the *next*
Verilator-gated test file is one forgotten line away from the same fate.

What this checks, and the approximation it makes
------------------------------------------------

A file is covered when a workflow's ``pytest`` invocation names it explicitly,
or names a parent directory. A directory only counts from an invocation with no
``-k`` filter — ``pytest backend/tests/golden -k lint`` runs a *subset* of that
directory, so treating it as covering the whole tree would be exactly the kind
of too-lenient check this file is here to prevent.

A bare ``pytest`` with no path argument never counts. That is the whole point:
the job that runs it does not install Verilator, so everything gated on the
binary skips there.

Deliberate approximation: this reads the workflow text rather than parsing YAML
(no PyYAML in the dependency set, and adding one for a guard is a poor trade).
It therefore checks that a path is *named* by some workflow, not that the job
naming it installs Verilator. :func:`test_a_workflow_installs_verilator` pins
the other half so the scheme cannot become vacuous.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_WORKFLOWS = _REPO / ".github" / "workflows"
_TESTS = _REPO / "backend" / "tests"

#: How a test file declares that it needs the Verilator binary.
_GATE = re.compile(r"_HAS_VERILATOR|shutil\.which\(\"verilator\"\)")


#: This file states the gate pattern literally in order to search for it, so it
#: matches its own detector while needing no Verilator itself. Excluded by path
#: rather than by making the pattern self-avoiding, which would be unreadable.
_SELF = Path(__file__).resolve()


def _verilator_gated_files() -> list[Path]:
    return sorted(
        p
        for p in _TESTS.rglob("test_*.py")
        if p.resolve() != _SELF and _GATE.search(p.read_text(encoding="utf-8"))
    )


def _workflow_text() -> list[tuple[Path, str]]:
    return [(p, p.read_text(encoding="utf-8")) for p in sorted(_WORKFLOWS.glob("*.yml"))]


def _named_paths() -> tuple[set[str], set[str]]:
    """``(files, directories)`` named by path-explicit pytest invocations.

    Directories are collected only from invocations carrying no ``-k``, because
    a filtered run covers an unknown subset of the tree.
    """
    files: set[str] = set()
    directories: set[str] = set()
    for _path, text in _workflow_text():
        for line in text.splitlines():
            if "pytest" not in line:
                continue
            tokens = line.split()
            targets = [t for t in tokens if t.startswith("backend/")]
            if not targets:
                continue  # bare `pytest`: the job it runs in has no Verilator
            filtered = "-k" in tokens
            for target in targets:
                if target.endswith(".py"):
                    files.add(target)
                elif not filtered:
                    directories.add(target.rstrip("/"))
    return files, directories


def test_the_scan_finds_something() -> None:
    """A glob that silently matches nothing would make this file a no-op."""
    assert _verilator_gated_files(), "no Verilator-gated test files found"
    files, directories = _named_paths()
    assert files or directories, "no pytest path arguments found in any workflow"


def test_a_workflow_installs_verilator() -> None:
    """The other half of the approximation above: if no job installed Verilator,
    every check in this file would be satisfied by paths that never run it."""
    assert any(
        "Install Verilator" in text for _path, text in _workflow_text()
    ), "no workflow installs Verilator; the coverage claim here would be empty"


@pytest.mark.parametrize(
    "test_file",
    _verilator_gated_files(),
    ids=lambda p: str(p.relative_to(_REPO)),
)
def test_verilator_gated_file_is_named_by_a_workflow(test_file: Path) -> None:
    relative = test_file.relative_to(_REPO).as_posix()
    files, directories = _named_paths()
    if relative in files:
        return
    parents = {p.as_posix() for p in Path(relative).parents}
    assert parents & directories, (
        f"{relative} needs Verilator, so it skips in the plain `pytest` job — "
        f"and no workflow names it or an unfiltered parent directory, so it "
        f"never runs anywhere. Add a step to the Verilator job in "
        f".github/workflows/ci.yml."
    )
