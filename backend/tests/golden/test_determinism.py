"""Determinism checks over the golden matrix (IMPLEMENTATION_PLAN.md §5 WP-08 task 6).

Ground rule (plan §1): same config -> byte-identical output. For every
discovered golden case, generate twice in-process and compare bytes/hash.
Additionally, one cross-process check for counter defaults (subprocess
running a tiny script) guards against any accidental process-local state
(e.g. dict/set iteration order, id()-based hashing) that an in-process
comparison alone couldn't catch.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from semicraft_core import generate

from .conftest import GoldenCase, discover_golden_cases, golden_case_id

_CASES = discover_golden_cases()


@pytest.mark.parametrize("case", _CASES, ids=[golden_case_id(c) for c in _CASES])
def test_generate_twice_in_process_is_identical(case: GoldenCase) -> None:
    a = generate(case.snippet_id, dict(case.resolved_options))
    b = generate(case.snippet_id, dict(case.resolved_options))
    assert a.code == b.code
    assert a.config_hash == b.config_hash
    assert a.filename == b.filename


def test_counter_defaults_deterministic_across_processes() -> None:
    script = (
        "import semicraft_core as sc; "
        "r = sc.generate('counter', {}); "
        "print(r.config_hash); "
        "print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2
