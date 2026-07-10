"""Determinism checks over the golden matrix (IMPLEMENTATION_PLAN.md §5 WP-08 task 6;
extended P2-14 task 4 to cover all ``generate_files()`` outputs, not just rtl).

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
from semicraft_core.generate import generate_files

from .conftest import GoldenCase, discover_golden_cases, golden_case_id

_CASES = discover_golden_cases()


@pytest.mark.parametrize("case", _CASES, ids=[golden_case_id(c) for c in _CASES])
def test_generate_twice_in_process_is_identical(case: GoldenCase) -> None:
    a = generate(case.snippet_id, dict(case.resolved_options))
    b = generate(case.snippet_id, dict(case.resolved_options))
    assert a.code == b.code
    assert a.config_hash == b.config_hash
    assert a.filename == b.filename


@pytest.mark.parametrize("case", _CASES, ids=[golden_case_id(c) for c in _CASES])
def test_generate_files_twice_in_process_is_identical(case: GoldenCase) -> None:
    """Same as above but over every ``generate_files()`` output (rtl/doc/tb).

    Snippet-kind cases only ever produce the rtl file; module-kind cases
    additionally get doc (always) and tb (once P2-13 lands and
    ``EMIT_TB`` is on). Whatever the current file set is, both calls must
    agree on it exactly — same paths, same kinds, same bytes, in the same
    order. No special-casing needed for a missing tb file: both calls simply
    omit it identically.
    """
    a = generate_files(case.snippet_id, dict(case.resolved_options))
    b = generate_files(case.snippet_id, dict(case.resolved_options))

    a_files = [(f.path, f.kind, f.text) for f in a.files]
    b_files = [(f.path, f.kind, f.text) for f in b.files]
    assert a_files == b_files
    assert a.config_hash == b.config_hash
    assert a.language == b.language


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
