"""Unit tests for semicraft_core.sim.service (P3-03).

All tests here run WITHOUT verilator installed: ``run_smoke`` is mocked so we
assert the orchestration wiring (generate -> write files -> run_smoke -> fold
status) and every degradation path, matching the convention in
``test_runner.py`` / ``test_verilator.py``. Verifying a real sim run is the
golden run-gate's job (``tests/golden/test_tb_run.py``).
"""

from __future__ import annotations

from unittest.mock import patch

from semicraft_core.generate import GeneratedFile, GenerateFilesResult, generate_files
from semicraft_core.sim import SimResult
from semicraft_core.sim.service import simulate


def _files_with_tb() -> GenerateFilesResult:
    """A minimal rtl+tb file set (contents irrelevant — run_smoke is mocked)."""
    return GenerateFilesResult(
        files=[
            GeneratedFile(path="foo.sv", kind="rtl", text="module foo; endmodule\n"),
            GeneratedFile(path="foo_tb.sv", kind="tb", text="module foo_tb; endmodule\n"),
        ],
        explanation=None,
        config_hash="abc123abc123",
        language="sv",
    )


def _fake_run(status: str, *, exit_code=None, stdout="", stderr=""):
    def _run(tb_path, rtl_paths, **kwargs):
        return SimResult(
            status=status,
            exit_code=exit_code,
            stdout_tail=stdout,
            stderr_tail=stderr,
            duration_s=0.5,
        )

    return _run


def test_pass_maps_through_and_sets_marker_seen() -> None:
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("pass", exit_code=0, stdout="hello\nSMOKE PASS: foo\n"),
    ):
        result = simulate(_files_with_tb())
    assert result.status == "pass"
    assert result.exit_code == 0
    assert result.marker_seen is True
    assert result.duration_s == 0.5


def test_fail_maps_through_without_marker() -> None:
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("fail", exit_code=1, stdout="some output\n"),
    ):
        result = simulate(_files_with_tb())
    assert result.status == "fail"
    assert result.exit_code == 1
    assert result.marker_seen is False


def test_unavailable_degrades_not_raises() -> None:
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("unavailable", stderr="verilator binary not found on PATH"),
    ):
        result = simulate(_files_with_tb())
    assert result.status == "unavailable"
    assert result.exit_code is None
    assert result.marker_seen is False
    assert "verilator" in result.stderr_tail


def test_compile_error_folds_to_error() -> None:
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("compile_error", exit_code=3, stderr="%Error: syntax"),
    ):
        result = simulate(_files_with_tb())
    assert result.status == "error"


def test_timeout_folds_to_error() -> None:
    with patch(
        "semicraft_core.sim.service.run_smoke",
        side_effect=_fake_run("timeout", stderr="simulation binary timed out after 30s"),
    ):
        result = simulate(_files_with_tb())
    assert result.status == "error"
    assert "timed out" in result.stderr_tail


def test_no_tb_when_file_set_has_no_tb_file() -> None:
    """A file set with only rtl (a snippet, or a clock-less module) never runs
    run_smoke and surfaces status='no_tb'."""
    files = GenerateFilesResult(
        files=[GeneratedFile(path="foo.sv", kind="rtl", text="module foo; endmodule\n")],
        config_hash="deadbeefcafe",
        language="sv",
    )
    with patch("semicraft_core.sim.service.run_smoke") as mock_run:
        result = simulate(files)
    mock_run.assert_not_called()
    assert result.status == "no_tb"
    assert result.exit_code is None
    assert result.duration_s == 0.0


def test_counter_snippet_generates_no_tb_end_to_end() -> None:
    """Real generate_files for a snippet produces no tb file -> no_tb."""
    files = generate_files("counter", {"language": "sv"})
    with patch("semicraft_core.sim.service.run_smoke") as mock_run:
        result = simulate(files)
    mock_run.assert_not_called()
    assert result.status == "no_tb"


def test_run_smoke_receives_written_tb_and_rtl_paths() -> None:
    """The tb path and rtl paths handed to run_smoke exist on disk with the
    generated contents (files are materialised in the temp workdir)."""
    captured = {}

    def _run(tb_path, rtl_paths, **kwargs):
        captured["tb_text"] = tb_path.read_text(encoding="utf-8")
        captured["rtl_texts"] = [p.read_text(encoding="utf-8") for p in rtl_paths]
        captured["workdir"] = kwargs.get("workdir")
        return SimResult("pass", 0, "SMOKE PASS", "", 0.1)

    with patch("semicraft_core.sim.service.run_smoke", side_effect=_run):
        simulate(_files_with_tb())

    assert "module foo_tb" in captured["tb_text"]
    assert captured["rtl_texts"] == ["module foo; endmodule\n"]
    assert captured["workdir"] is not None
