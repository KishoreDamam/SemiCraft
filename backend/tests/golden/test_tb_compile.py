"""Verilator compile gate over every committed golden TB (P2-14 task 2).

Discovers every ``*_tb.sv`` file actually committed under
``backend/tests/golden/<snippet-id>/`` and compiles it with
``verilator --timing --binary`` against its matching rtl golden. This is a
compile-only gate: a successful build (``verilator`` exits 0) is a pass; the
produced executable is never run (P3-09 upgrades to actually *running* every
TB — see docs/PLAN-semicraft-phases-2-8.md Phase 3 table).

Deliberately decoupled from ``semicraft_core.generate``/``generate_files``
internals: this module only looks at files on disk under ``tests/golden/``,
so it works identically whether those ``*_tb.sv`` files were produced by
P2-13's generator or hand-placed. As of this WP no ``*_tb.sv`` goldens are
committed yet (P2-13 lands the generator; a follow-up regenerates + commits
the doc/tb snapshots via ``--update-golden``, see test_snapshots.py), so
parametrization collects zero cases and this module is a no-op — that is the
intended, non-failing state, not a bug.

``--timing`` is required here (unlike lint/verilator.py, which deliberately
omits it for pure synthesizable RTL): smoke TBs use timing-control constructs
(``#delay``, clock-gen event controls) that Verilator's default (non-timed)
scheduling mode does not support.

Skips entirely (module-level ``skipif``) when the ``verilator`` binary is
absent — true on this Windows dev host, false in CI's lint-gate job which
installs it via ``apt-get``.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from .conftest import GOLDEN_ROOT

_HAS_VERILATOR = shutil.which("verilator") is not None
_COMPILE_TIMEOUT_SECONDS = 60


def discover_tb_goldens() -> list[Path]:
    """Every committed ``<case>.<sv|v>_tb.sv`` golden, across all snippet dirs.

    Sorted for stable test ordering/ids across OSes.
    """
    if not GOLDEN_ROOT.is_dir():
        return []
    return sorted(GOLDEN_ROOT.glob("*/*_tb.sv"))


def _matching_rtl(tb_path: Path) -> Path:
    """The rtl golden that pairs with ``tb_path``.

    Snapshot naming (tests/golden/conftest.py ``GoldenCase.tb_snapshot_path``):
    a tb golden ``<case>.<ext>_tb.sv`` pairs with the rtl golden
    ``<case>.<ext>`` in the same directory (``ext`` is ``sv`` or ``v``).
    """
    stem = tb_path.name[: -len("_tb.sv")]
    return tb_path.with_name(stem)


_TB_GOLDENS = discover_tb_goldens()
_TB_IDS = [str(p.relative_to(GOLDEN_ROOT)) for p in _TB_GOLDENS]


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("tb_path", _TB_GOLDENS, ids=_TB_IDS)
def test_golden_tb_compiles(tb_path: Path) -> None:
    rtl_path = _matching_rtl(tb_path)
    if not rtl_path.is_file():
        pytest.fail(
            f"{tb_path} has no matching rtl golden at {rtl_path} "
            "(tb/rtl goldens must be regenerated together)"
        )

    verilator_path = shutil.which("verilator")
    assert verilator_path is not None  # guarded by skipif above

    with tempfile.TemporaryDirectory(prefix="semicraft-tbcompile-") as tmpdir:
        cmd = [
            verilator_path,
            "--timing",
            "--binary",
            "--build-jobs",
            "1",
            "-Mdir",
            tmpdir,
            str(tb_path),
            str(rtl_path),
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=_COMPILE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            pytest.fail(
                f"verilator --timing --binary timed out after "
                f"{_COMPILE_TIMEOUT_SECONDS}s compiling {tb_path.name} + "
                f"{rtl_path.name}: {exc}"
            )

        assert proc.returncode == 0, (
            f"verilator --timing --binary failed to compile {tb_path.name} + "
            f"{rtl_path.name} (exit {proc.returncode}):\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
