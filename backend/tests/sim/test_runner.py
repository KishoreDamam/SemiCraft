"""Unit tests for semicraft_core.sim.runner (P3-03a).

All tests here run WITHOUT verilator installed — ``shutil.which`` and
``subprocess.run`` are mocked, matching the convention in
``backend/tests/lint/test_verilator.py``. The real-binary integration test
lives in ``test_runner_integration.py`` and is skipped unless verilator is on
PATH; the golden run-gate lives in ``backend/tests/golden/test_tb_run.py``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from semicraft_core.sim import SimResult, run_smoke

_VERILATOR_PATH = "/usr/bin/verilator"


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _make_executable(mdir: Path, name: str = "Vtop_tb") -> Path:
    """Drop a fake ``V<top>`` binary in ``mdir`` so discovery finds it.

    The real compile step (mocked away in these tests) is what actually
    creates this file; we stand it in directly since only its *presence* and
    *name shape* matter to ``_find_executable``.
    """
    exe = mdir / name
    exe.write_text("", encoding="utf-8")
    # Also drop a same-prefixed build artefact to prove the "no dot in name"
    # filter actually discriminates rather than just picking the first V*.
    (mdir / f"{name}.mk").write_text("", encoding="utf-8")
    return exe


def test_unavailable_when_verilator_missing(tmp_path: Path) -> None:
    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=None),
        patch("semicraft_core.sim.runner.subprocess.run") as mock_run,
    ):
        result = run_smoke(tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path)

    assert result.status == "unavailable"
    assert result.exit_code is None
    assert "verilator" in result.stderr_tail.lower()
    mock_run.assert_not_called()


def test_pass_requires_exit_zero_and_marker(tmp_path: Path) -> None:
    _make_executable(tmp_path)
    compile_ok = _FakeCompletedProcess(returncode=0)
    run_ok = _FakeCompletedProcess(returncode=0, stdout="...\nSMOKE PASS: top\n")

    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=_VERILATOR_PATH),
        patch(
            "semicraft_core.sim.runner.subprocess.run", side_effect=[compile_ok, run_ok]
        ) as mock_run,
    ):
        result = run_smoke(tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path)

    assert result == SimResult(
        status="pass",
        exit_code=0,
        stdout_tail="...\nSMOKE PASS: top",
        stderr_tail="",
        duration_s=result.duration_s,
    )
    assert mock_run.call_count == 2


def test_fatal_check_failure_is_fail(tmp_path: Path) -> None:
    _make_executable(tmp_path)
    compile_ok = _FakeCompletedProcess(returncode=0)
    run_fatal = _FakeCompletedProcess(
        returncode=1, stdout="cycle 3: bad q\n", stderr="%Error: top_tb.sv:42: $fatal\n"
    )

    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=_VERILATOR_PATH),
        patch("semicraft_core.sim.runner.subprocess.run", side_effect=[compile_ok, run_fatal]),
    ):
        result = run_smoke(tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path)

    assert result.status == "fail"
    assert result.exit_code == 1
    assert "$fatal" in result.stderr_tail


def test_exit_zero_without_pass_marker_is_fail(tmp_path: Path) -> None:
    """The marker is mandatory: exit 0 alone must not read as a pass."""
    _make_executable(tmp_path)
    compile_ok = _FakeCompletedProcess(returncode=0)
    run_no_marker = _FakeCompletedProcess(returncode=0, stdout="ran off the end\n")

    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=_VERILATOR_PATH),
        patch("semicraft_core.sim.runner.subprocess.run", side_effect=[compile_ok, run_no_marker]),
    ):
        result = run_smoke(tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path)

    assert result.status == "fail"
    assert result.exit_code == 0


def test_compile_error(tmp_path: Path) -> None:
    compile_bad = _FakeCompletedProcess(
        returncode=1, stdout="", stderr="%Error: top_tb.sv:5: syntax error\n"
    )

    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=_VERILATOR_PATH),
        patch("semicraft_core.sim.runner.subprocess.run", return_value=compile_bad) as mock_run,
    ):
        result = run_smoke(tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path)

    assert result.status == "compile_error"
    assert result.exit_code == 1
    assert "syntax error" in result.stderr_tail
    mock_run.assert_called_once()


def test_compile_error_when_no_executable_produced(tmp_path: Path) -> None:
    """Compile reports exit 0 but -Mdir has no V* binary — degrade, don't crash."""
    compile_ok = _FakeCompletedProcess(returncode=0)

    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=_VERILATOR_PATH),
        patch("semicraft_core.sim.runner.subprocess.run", return_value=compile_ok) as mock_run,
    ):
        result = run_smoke(tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path)

    assert result.status == "compile_error"
    assert "no executable" in result.stderr_tail
    mock_run.assert_called_once()


def test_compile_timeout(tmp_path: Path) -> None:
    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=_VERILATOR_PATH),
        patch(
            "semicraft_core.sim.runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["verilator"], timeout=90),
        ),
    ):
        result = run_smoke(
            tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path, compile_timeout_s=90
        )

    assert result.status == "timeout"
    assert result.exit_code is None
    assert "90" in result.stderr_tail


def test_run_timeout(tmp_path: Path) -> None:
    _make_executable(tmp_path)
    compile_ok = _FakeCompletedProcess(returncode=0)

    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=_VERILATOR_PATH),
        patch(
            "semicraft_core.sim.runner.subprocess.run",
            side_effect=[compile_ok, subprocess.TimeoutExpired(cmd=["Vtop_tb"], timeout=30)],
        ),
    ):
        result = run_smoke(
            tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path, run_timeout_s=30
        )

    assert result.status == "timeout"
    assert result.exit_code is None
    assert "30" in result.stderr_tail


def test_oserror_launching_verilator_is_unavailable(tmp_path: Path) -> None:
    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value=_VERILATOR_PATH),
        patch("semicraft_core.sim.runner.subprocess.run", side_effect=OSError("boom")),
    ):
        result = run_smoke(tmp_path / "top_tb.sv", [tmp_path / "top.sv"], workdir=tmp_path)

    assert result.status == "unavailable"
    assert "boom" in result.stderr_tail


def test_default_workdir_is_created_and_cleaned_up() -> None:
    """No explicit workdir: run_smoke manages its own temp dir and cleans it up."""
    seen_mdirs: list[Path] = []

    def fake_run(cmd, **kwargs):
        mdir = Path(kwargs["cwd"])
        seen_mdirs.append(mdir)
        if cmd[0] != "/usr/bin/verilator":
            # This is the "execute the binary" call — the fake compile step
            # never actually created a binary, so this branch should be
            # unreachable if discovery correctly reports None.
            raise AssertionError("run step should not be reached: no executable was produced")
        return _FakeCompletedProcess(returncode=0)

    with (
        patch("semicraft_core.sim.runner.shutil.which", return_value="/usr/bin/verilator"),
        patch("semicraft_core.sim.runner.subprocess.run", side_effect=fake_run),
    ):
        result = run_smoke("top_tb.sv", ["top.sv"])

    assert result.status == "compile_error"
    assert len(seen_mdirs) == 1
    # The temp dir was cleaned up after the call.
    assert not seen_mdirs[0].exists()
