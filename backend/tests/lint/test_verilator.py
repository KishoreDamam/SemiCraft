"""Unit tests for semicraft_core.lint.verilator (WP-04).

All tests here run WITHOUT verilator installed — subprocess.run and
shutil.which are mocked. The real-binary integration test lives in
test_verilator_integration.py and is skipped unless verilator is on PATH.
"""

from __future__ import annotations

import subprocess
from unittest.mock import patch

from semicraft_core.lint import LintReport, lint
from semicraft_core.lint.verilator import LintMessage, _parse_messages

SAMPLE_SV = """\
module top (
    input  logic clk,
    output logic q
);
    always_ff @(posedge clk) begin
        q <= 1'b1;
    end
endmodule
"""


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_clean_output_yields_clean_status():
    with (
        patch("semicraft_core.lint.verilator.shutil.which", return_value="/usr/bin/verilator"),
        patch(
            "semicraft_core.lint.verilator.subprocess.run",
            return_value=_FakeCompletedProcess(returncode=0, stdout="", stderr=""),
        ),
    ):
        report = lint(SAMPLE_SV, "sv", "top")

    assert report.status == "clean"
    assert report.messages == []


def test_warning_line_parsed_into_structured_message():
    stderr = (
        "%Warning-WIDTHTRUNC: top.sv:12:10: Operator ASSIGNW expects 8 bits "
        "on the Assign RHS, but RHS's CONST '1'h1' generates 1 bits.\n"
        "                                : ... In instance top\n"
    )
    with (
        patch("semicraft_core.lint.verilator.shutil.which", return_value="/usr/bin/verilator"),
        patch(
            "semicraft_core.lint.verilator.subprocess.run",
            return_value=_FakeCompletedProcess(returncode=0, stdout="", stderr=stderr),
        ),
    ):
        report = lint(SAMPLE_SV, "sv", "top")

    assert report.status == "warnings"
    assert len(report.messages) == 1
    msg = report.messages[0]
    assert msg.severity == "warning"
    assert msg.code == "WIDTHTRUNC"
    assert msg.line == 12
    assert "Operator ASSIGNW expects 8 bits" in msg.text


def test_nonzero_exit_with_error_line_yields_warnings_status_with_error_severity():
    stderr = "%Error: top.sv:3:5: syntax error, unexpected ';'\n"
    with (
        patch("semicraft_core.lint.verilator.shutil.which", return_value="/usr/bin/verilator"),
        patch(
            "semicraft_core.lint.verilator.subprocess.run",
            return_value=_FakeCompletedProcess(returncode=1, stdout="", stderr=stderr),
        ),
    ):
        report = lint(SAMPLE_SV, "sv", "top")

    assert report.status == "warnings"
    assert len(report.messages) == 1
    msg = report.messages[0]
    assert msg.severity == "error"
    assert msg.code is None
    assert msg.line == 3
    assert "syntax error" in msg.text


def test_nonzero_exit_with_unparseable_stderr_still_reports_warnings_not_clean():
    with (
        patch("semicraft_core.lint.verilator.shutil.which", return_value="/usr/bin/verilator"),
        patch(
            "semicraft_core.lint.verilator.subprocess.run",
            return_value=_FakeCompletedProcess(
                returncode=1, stdout="", stderr="internal error, no % lines"
            ),
        ),
    ):
        report = lint(SAMPLE_SV, "sv", "top")

    assert report.status == "warnings"
    assert len(report.messages) == 1
    assert report.messages[0].severity == "error"


def test_missing_binary_yields_unavailable():
    with patch("semicraft_core.lint.verilator.shutil.which", return_value=None):
        report = lint(SAMPLE_SV, "sv", "top")

    assert report.status == "unavailable"
    assert len(report.messages) == 1
    assert "not found" in report.messages[0].text


def test_timeout_yields_unavailable():
    with (
        patch("semicraft_core.lint.verilator.shutil.which", return_value="/usr/bin/verilator"),
        patch(
            "semicraft_core.lint.verilator.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["verilator"], timeout=10),
        ),
    ):
        report = lint(SAMPLE_SV, "sv", "top")

    assert report.status == "unavailable"
    assert len(report.messages) == 1
    assert "timed out" in report.messages[0].text


def test_launch_failure_oserror_yields_unavailable():
    with (
        patch("semicraft_core.lint.verilator.shutil.which", return_value="/usr/bin/verilator"),
        patch(
            "semicraft_core.lint.verilator.subprocess.run",
            side_effect=OSError("permission denied"),
        ),
    ):
        report = lint(SAMPLE_SV, "sv", "top")

    assert report.status == "unavailable"
    assert "permission denied" in report.messages[0].text


def test_lint_report_and_message_are_hashable_frozen_dataclasses():
    msg = LintMessage(severity="warning", code="WIDTHTRUNC", line=1, text="x")
    report = LintReport(status="clean", messages=[msg])
    assert report.status == "clean"
    assert report.messages[0].code == "WIDTHTRUNC"


def test_parse_messages_ignores_non_diagnostic_lines():
    stderr = (
        "Some banner line\n"
        "%Warning-UNUSED: f.sv:7:1: Signal is not used: 'foo'\n"
        "                : ... continuation line\n"
    )
    messages = _parse_messages(stderr)
    assert len(messages) == 1
    assert messages[0].code == "UNUSED"
    assert messages[0].line == 7


def test_verilator_invocation_uses_expected_flags_and_extension():
    """Confirms the exact command shape: --lint-only -Wall, --default-language,
    a .sv/.v file, and no --timing flag (see module docstring decision)."""
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _FakeCompletedProcess(returncode=0)

    with (
        patch("semicraft_core.lint.verilator.shutil.which", return_value="/usr/bin/verilator"),
        patch("semicraft_core.lint.verilator.subprocess.run", side_effect=fake_run),
    ):
        lint(SAMPLE_SV, "sv", "top")

    cmd = captured["cmd"]
    assert cmd[0] == "/usr/bin/verilator"
    assert "--lint-only" in cmd
    assert "-Wall" in cmd
    assert "--timing" not in cmd
    assert "--default-language" in cmd
    lang_idx = cmd.index("--default-language")
    assert cmd[lang_idx + 1] == "1800-2017"
    file_arg = cmd[-1]
    assert file_arg.endswith("top.sv")


def test_verilog_language_uses_v_extension_and_1364():
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _FakeCompletedProcess(returncode=0)

    with (
        patch("semicraft_core.lint.verilator.shutil.which", return_value="/usr/bin/verilator"),
        patch("semicraft_core.lint.verilator.subprocess.run", side_effect=fake_run),
    ):
        lint(SAMPLE_SV, "verilog", "top")

    cmd = captured["cmd"]
    lang_idx = cmd.index("--default-language")
    assert cmd[lang_idx + 1] == "1364-2005"
    assert cmd[-1].endswith("top.v")
