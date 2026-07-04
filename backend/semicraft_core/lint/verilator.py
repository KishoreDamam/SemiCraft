"""Verilator lint integration (IMPLEMENTATION_PLAN.md §5 WP-04).

``lint(code, language, top)`` runs ``verilator --lint-only -Wall`` over
generated HDL and returns a structured :class:`LintReport` matching the API
contract's ``lint`` field (plan §4):
``{"status": "clean" | "warnings" | "unavailable", "messages": [...]}``.

Fragment-mode note
-------------------
Linting always runs against **wrapped** code (a full module with
``module``/``endmodule``), never a bare fragment. Fragments
(``include_wrapper=False``) are not standalone compilation units — Verilator
has nothing to attach ports/parameters to. The API layer is responsible for
generating with ``include_wrapper=True`` specifically for the lint pass (see
plan §5 WP-04 task 3) even when the response it returns to the user is the
fragment. Callers of this module must therefore always pass full-module code;
this function does not force-wrap on their behalf.

``--timing`` decision
----------------------
We deliberately do **not** pass ``--timing`` to Verilator. That flag enables
scheduling support for SystemVerilog timing controls (`#delay`, event
controls used for testbench-style timing) in Verilator's timed simulation
mode. SemiCraft only ever generates pure synthesizable RTL (combinational/
sequential logic, no delays, no testbench timing constructs), so the flag has
no effect on what we lint. This host has no Verilator installed to probe
`--timing` support/version behavior against, and the docs/PROGRESS.md open
item flags exactly this uncertainty (older Verilator releases may not
recognize the flag at all, or may warn). Omitting it is strictly safer and
sufffices for our use case; if a future WP needs timing-control constructs,
add a version probe (``verilator --version`` parse) with graceful fallback
before turning the flag on.

Graceful degradation
---------------------
This module must never raise for "verilator not usable" conditions:

- missing binary (``shutil.which("verilator") is None``) -> ``unavailable``;
- subprocess timeout (10s) -> ``unavailable`` with an explanatory message.

Any other unexpected ``OSError`` launching the subprocess is also degraded to
``unavailable`` rather than propagating, since lint is a best-effort adjunct
to generation, not part of the generation contract itself.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

__all__ = ["LintMessage", "LintReport", "lint"]

_TIMEOUT_SECONDS = 10

# Matches lines like:
#   %Warning-WIDTHTRUNC: file.sv:12:34: message text
#   %Error: file.sv:5:1: message text          (no code between - and :)
#   %Error-UNSUPPORTED: file.sv:9: message text
_MESSAGE_RE = re.compile(
    r"^%(?P<severity>Warning|Error)(?:-(?P<code>[A-Z0-9_]+))?:\s*"
    r"(?:[^:]*:(?P<line>\d+):(?:\d+:)?\s*)?"
    r"(?P<text>.*)$"
)


@dataclass(frozen=True, slots=True)
class LintMessage:
    """A single parsed Verilator diagnostic line."""

    severity: str  # "warning" | "error"
    code: str | None  # e.g. "WIDTHTRUNC"; None if verilator gave no code
    line: int | None  # source line number; None if not present in the message
    text: str  # the message text (code/location stripped)


@dataclass(frozen=True, slots=True)
class LintReport:
    """Result of :func:`lint`, matching the API contract's ``lint`` field."""

    status: Literal["clean", "warnings", "unavailable"]
    messages: list[LintMessage] = field(default_factory=list)


def _extension(language: Literal["sv", "verilog"]) -> str:
    return ".sv" if language == "sv" else ".v"


def _default_language_flag(language: Literal["sv", "verilog"]) -> str:
    return "1800-2017" if language == "sv" else "1364-2005"


def _parse_messages(stderr_text: str) -> list[LintMessage]:
    messages: list[LintMessage] = []
    for raw_line in stderr_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("%Warning") and not line.startswith("%Error"):
            continue
        m = _MESSAGE_RE.match(line)
        if not m:
            continue
        severity = "warning" if m.group("severity") == "Warning" else "error"
        code = m.group("code")
        line_no = int(m.group("line")) if m.group("line") else None
        text = m.group("text").strip()
        messages.append(LintMessage(severity=severity, code=code, line=line_no, text=text))
    return messages


def lint(code: str, language: Literal["sv", "verilog"], top: str) -> LintReport:
    """Lint ``code`` with ``verilator --lint-only -Wall``.

    Parameters
    ----------
    code:
        Full HDL source text for a single file, **wrapped** (must contain a
        complete module declaration, not a fragment — see module docstring).
    language:
        ``"sv"`` or ``"verilog"``; selects the file extension and the
        ``--default-language`` value passed to Verilator.
    top:
        Name of the top-level module. Used to name the temp file
        (``<top>.sv``/``<top>.v``); Verilator infers the top module from the
        single file we pass it, so no explicit ``--top-module`` flag is
        needed for the single-file case this function handles.

    Returns
    -------
    LintReport
        ``status="unavailable"`` if Verilator is not installed, times out, or
        cannot be launched. ``status="clean"`` if Verilator exits 0 with no
        parsed messages. ``status="warnings"`` otherwise (covers both
        Verilator warnings and lint-detected errors — the caller/API surfaces
        the per-message ``severity`` for anything more specific).
    """
    verilator_path = shutil.which("verilator")
    if verilator_path is None:
        return LintReport(
            status="unavailable",
            messages=[
                LintMessage(
                    severity="warning",
                    code=None,
                    line=None,
                    text="verilator binary not found on PATH; lint skipped.",
                )
            ],
        )

    with tempfile.TemporaryDirectory(prefix="semicraft-lint-") as tmpdir:
        file_path = Path(tmpdir) / f"{top}{_extension(language)}"
        file_path.write_text(code, encoding="utf-8")

        cmd = [
            verilator_path,
            "--lint-only",
            "-Wall",
            "--default-language",
            _default_language_flag(language),
            str(file_path),
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return LintReport(
                status="unavailable",
                messages=[
                    LintMessage(
                        severity="warning",
                        code=None,
                        line=None,
                        text=f"verilator timed out after {_TIMEOUT_SECONDS}s; lint skipped.",
                    )
                ],
            )
        except OSError as exc:
            return LintReport(
                status="unavailable",
                messages=[
                    LintMessage(
                        severity="warning",
                        code=None,
                        line=None,
                        text=f"failed to launch verilator: {exc}",
                    )
                ],
            )

    messages = _parse_messages(proc.stderr or "")

    if proc.returncode == 0 and not messages:
        return LintReport(status="clean", messages=[])

    if not messages and proc.returncode != 0:
        # Verilator failed but gave us nothing parseable on stderr — surface
        # what we have as a single opaque message rather than silently
        # reporting "clean".
        messages = [
            LintMessage(
                severity="error",
                code=None,
                line=None,
                text=(proc.stderr or proc.stdout or "verilator exited nonzero").strip(),
            )
        ]

    return LintReport(status="warnings", messages=messages)
