"""Local subprocess sim runner (P3-03a — first slice of P3-03 sim sandbox).

:func:`run_smoke` compiles a smoke testbench with ``verilator --timing
--binary`` (same invocation as ``backend/tests/golden/test_tb_compile.py``)
and then *executes* the produced binary, classifying the outcome. This is the
"local subprocess isolation" slice of P3-03 (docs/PLAN-semicraft-phases-2-8.md
Phase 3 table): no container/queue/API yet, just a reusable, testable runner
that both the golden CI gate (``test_tb_run.py``) and later WPs (the sim
sandbox service, P3-03 proper) can build on.

Success semantics (docs/TB_SPEC.md / ``tb/generate_tb.py`` docstring): a smoke
TB ``$fatal``s on any failed check (nonzero exit) and prints
``"SMOKE PASS: <module>"`` followed by ``$finish`` (exit 0) when every check
passed. Both conditions are required for ``status="pass"`` — an exit-0 run
that never printed the marker (e.g. a TB that fell off the end of its
``initial`` block without reaching the pass line) is treated as ``"fail"``,
not ``"pass"``, because the marker is the actual correctness signal.

Graceful degradation follows ``semicraft_core.lint.verilator``'s conventions:
missing ``verilator`` binary -> ``"unavailable"``; anything that prevents a
clean pass/fail read (subprocess timeout, missing executable after a "clean"
compile, OSError launching a subprocess) is degraded rather than raised.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

__all__ = ["SimResult", "run_smoke"]

# Separate budgets for the two subprocess steps: compiling a Verilator
# testbench (parsing + C++ codegen + native build) is far slower than
# running the resulting binary through a handful of directed cycles.
_DEFAULT_COMPILE_TIMEOUT_SECONDS = 90
_DEFAULT_RUN_TIMEOUT_SECONDS = 30

_TAIL_LINES = 30
_PASS_MARKER = "SMOKE PASS"

SimStatus = Literal["pass", "fail", "compile_error", "timeout", "unavailable"]


@dataclass(frozen=True, slots=True)
class SimResult:
    """Outcome of :func:`run_smoke`.

    - ``status``:
        - ``"pass"`` — compiled, ran, exited 0, and printed the
          ``SMOKE PASS`` marker.
        - ``"fail"`` — compiled and ran, but either exited nonzero (a
          ``$fatal`` from a failed check) or exited 0 without the marker
          (the TB never reached its pass line).
        - ``"compile_error"`` — ``verilator --timing --binary`` itself
          exited nonzero, or exited 0 but produced no runnable executable.
        - ``"timeout"`` — the compile step or the run step exceeded its
          budget.
        - ``"unavailable"`` — no ``verilator`` binary on ``PATH``, or it
          could not be launched at all (``OSError``).
    - ``exit_code`` — the run step's exit code when one was observed
      (``None`` for ``compile_error``/``timeout``/``unavailable``, where
      there either is no run-step exit code or none is trustworthy).
    - ``stdout_tail`` / ``stderr_tail`` — last ~30 lines of whichever step
      produced the result (compile step for ``compile_error``, run step
      otherwise), so CI logs show exactly what happened without dumping the
      full Verilator build log.
    - ``duration_s`` — wall-clock time across both steps.
    """

    status: SimStatus
    exit_code: int | None
    stdout_tail: str
    stderr_tail: str
    duration_s: float


def _tail(text: str | None, n: int = _TAIL_LINES) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-n:])


def _find_executable(mdir: Path) -> Path | None:
    """Locate the ``V<top>`` binary Verilator's ``--binary`` mode produces.

    Verilator names the executable ``V<top-module-name>`` and drops it at the
    top of ``-Mdir`` alongside build artefacts (``V<top>.mk``,
    ``V<top>__ALL.a``, object files, etc.) — those all contain a ``.`` in
    their name, so filtering on "starts with V, no dot" isolates the binary
    without needing to know the top module name up front (Verilator infers it
    itself: the TB module, since it is never instantiated by anything else).
    """
    candidates = sorted(
        (p for p in mdir.iterdir() if p.is_file() and p.name.startswith("V") and "." not in p.name),
        key=lambda p: len(p.name),
    )
    return candidates[0] if candidates else None


def run_smoke(
    tb_path: str | Path,
    rtl_paths: list[str | Path] | tuple[str | Path, ...],
    *,
    compile_timeout_s: float = _DEFAULT_COMPILE_TIMEOUT_SECONDS,
    run_timeout_s: float = _DEFAULT_RUN_TIMEOUT_SECONDS,
    workdir: str | Path | None = None,
) -> SimResult:
    """Compile ``tb_path`` + ``rtl_paths`` and execute the resulting binary.

    Parameters
    ----------
    tb_path:
        Path to the smoke testbench source (SystemVerilog).
    rtl_paths:
        Path(s) to the RTL file(s) the TB instantiates as its DUT.
    compile_timeout_s:
        Budget for the ``verilator --timing --binary`` step (default 90s).
    run_timeout_s:
        Budget for executing the produced binary (default 30s).
    workdir:
        Directory to use as Verilator's ``-Mdir`` (and the run step's cwd).
        When ``None`` (the default), a temporary directory is created and
        removed automatically — callers that don't need the build artefacts
        afterwards never have to think about cleanup. Pass an explicit
        directory to inspect artefacts after the call (the caller then owns
        cleanup).
    """
    verilator_path = shutil.which("verilator")
    if verilator_path is None:
        return SimResult(
            status="unavailable",
            exit_code=None,
            stdout_tail="",
            stderr_tail="verilator binary not found on PATH; sim run skipped.",
            duration_s=0.0,
        )

    tb_path = Path(tb_path)
    rtl_path_list = [Path(p) for p in rtl_paths]

    if workdir is not None:
        return _run_smoke_in(
            Path(workdir), verilator_path, tb_path, rtl_path_list, compile_timeout_s, run_timeout_s
        )

    with tempfile.TemporaryDirectory(prefix="semicraft-simrun-") as tmpdir:
        return _run_smoke_in(
            Path(tmpdir), verilator_path, tb_path, rtl_path_list, compile_timeout_s, run_timeout_s
        )


def _run_smoke_in(
    mdir: Path,
    verilator_path: str,
    tb_path: Path,
    rtl_paths: list[Path],
    compile_timeout_s: float,
    run_timeout_s: float,
) -> SimResult:
    start = time.monotonic()

    compile_cmd = [
        verilator_path,
        "--timing",
        "--binary",
        "--build-jobs",
        "1",
        "-Mdir",
        str(mdir),
        str(tb_path),
        *(str(p) for p in rtl_paths),
    ]
    try:
        compile_proc = subprocess.run(
            compile_cmd,
            cwd=str(mdir),
            capture_output=True,
            text=True,
            timeout=compile_timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        return SimResult(
            status="timeout",
            exit_code=None,
            stdout_tail=_tail(exc.stdout if isinstance(exc.stdout, str) else None),
            stderr_tail=_tail(exc.stderr if isinstance(exc.stderr, str) else None)
            or f"verilator compile timed out after {compile_timeout_s}s",
            duration_s=time.monotonic() - start,
        )
    except OSError as exc:
        return SimResult(
            status="unavailable",
            exit_code=None,
            stdout_tail="",
            stderr_tail=f"failed to launch verilator: {exc}",
            duration_s=time.monotonic() - start,
        )

    if compile_proc.returncode != 0:
        return SimResult(
            status="compile_error",
            exit_code=compile_proc.returncode,
            stdout_tail=_tail(compile_proc.stdout),
            stderr_tail=_tail(compile_proc.stderr),
            duration_s=time.monotonic() - start,
        )

    exe_path = _find_executable(mdir)
    if exe_path is None:
        return SimResult(
            status="compile_error",
            exit_code=compile_proc.returncode,
            stdout_tail=_tail(compile_proc.stdout),
            stderr_tail="verilator exited 0 but produced no executable in -Mdir",
            duration_s=time.monotonic() - start,
        )

    try:
        run_proc = subprocess.run(
            [str(exe_path)],
            cwd=str(mdir),
            capture_output=True,
            text=True,
            timeout=run_timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        return SimResult(
            status="timeout",
            exit_code=None,
            stdout_tail=_tail(exc.stdout if isinstance(exc.stdout, str) else None),
            stderr_tail=_tail(exc.stderr if isinstance(exc.stderr, str) else None)
            or f"simulation binary timed out after {run_timeout_s}s",
            duration_s=time.monotonic() - start,
        )
    except OSError as exc:
        return SimResult(
            status="unavailable",
            exit_code=None,
            stdout_tail="",
            stderr_tail=f"failed to launch simulation binary: {exc}",
            duration_s=time.monotonic() - start,
        )

    passed = run_proc.returncode == 0 and _PASS_MARKER in (run_proc.stdout or "")
    return SimResult(
        status="pass" if passed else "fail",
        exit_code=run_proc.returncode,
        stdout_tail=_tail(run_proc.stdout),
        stderr_tail=_tail(run_proc.stderr),
        duration_s=time.monotonic() - start,
    )
