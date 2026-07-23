"""Sim sandbox orchestration service (P3-03).

Thin orchestration layer over :func:`semicraft_core.generate.generate_files`
and :func:`semicraft_core.sim.run_smoke`. Given a catalog item + options it:

    generate the file set  ->  write rtl + tb to a temp workdir  ->  run_smoke

and folds the low-level :class:`SimResult` into the API-facing
:class:`SimServiceResult` (docs/PLAN-semicraft-phases-2-8.md Appendix A / Phase
3 P3-03). Keeping this out of ``api/main.py`` keeps the endpoint lean; the
endpoint only owns request/response marshalling and the 404/422/500 error
mapping (shared with the other v2 routes).

Status mapping (:class:`SimResult` -> :class:`SimServiceResult`)::

    pass            -> "pass"
    fail            -> "fail"
    unavailable     -> "unavailable"    (no verilator: Windows/local dev)
    compile_error   -> "error"
    timeout         -> "error"

Modules whose ``TbSpec.clock`` is ``None`` emit no smoke TB (generate_files
appends no ``tb`` file), so there is nothing to run — that is surfaced as
``status="no_tb"`` rather than a crash.

Determinism / side-effects: the file set is written under a
``TemporaryDirectory`` that is removed on return (``run_smoke`` itself uses the
same temp-dir discipline for Verilator's build artefacts). The only
non-deterministic field is ``duration_s`` (a live wall-clock measurement),
matching :class:`SimResult`; no timestamps are stored or returned elsewhere.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ..generate import GenerateFilesResult
from .runner import (
    _DEFAULT_COMPILE_TIMEOUT_SECONDS,
    _DEFAULT_RUN_TIMEOUT_SECONDS,
    _PASS_MARKER,
    run_smoke,
)

__all__ = ["SimServiceResult", "simulate"]

SimServiceStatus = Literal["pass", "fail", "unavailable", "error", "no_tb"]

# Fold the runner's finer-grained statuses into the API-facing set. "pass",
# "fail" and "unavailable" carry through unchanged; the two "couldn't get a
# clean pass/fail read" statuses (compile_error, timeout) both surface as
# "error" (the task's "timeout surfaced as error/fail" requirement).
_STATUS_MAP: dict[str, SimServiceStatus] = {
    "pass": "pass",
    "fail": "fail",
    "unavailable": "unavailable",
    "compile_error": "error",
    "timeout": "error",
}


@dataclass(frozen=True, slots=True)
class SimServiceResult:
    """API-facing outcome of :func:`simulate`.

    - ``status`` — ``"pass"``/``"fail"``/``"unavailable"``/``"error"`` folded
      from the underlying :class:`SimResult`, plus ``"no_tb"`` when the item
      generated no testbench (e.g. ``TbSpec.clock is None``, or a snippet with
      no TB at all).
    - ``exit_code`` — the run step's exit code when observed, else ``None``.
    - ``stdout_tail`` / ``stderr_tail`` — last ~30 lines from the runner.
    - ``duration_s`` — wall-clock time of the compile+run (``0.0`` for
      ``"no_tb"``, where nothing was executed).
    - ``marker_seen`` — whether the ``SMOKE PASS`` marker was observed on
      stdout (the actual correctness signal; ``True`` implies a genuine pass).
    """

    status: SimServiceStatus
    exit_code: int | None
    stdout_tail: str
    stderr_tail: str
    duration_s: float
    marker_seen: bool


def _no_tb_result() -> SimServiceResult:
    return SimServiceResult(
        status="no_tb",
        exit_code=None,
        stdout_tail="",
        stderr_tail="item generated no testbench (no clock / not a module); nothing to simulate.",
        duration_s=0.0,
        marker_seen=False,
    )


def simulate(
    files_result: GenerateFilesResult,
    *,
    compile_timeout_s: float = _DEFAULT_COMPILE_TIMEOUT_SECONDS,
    run_timeout_s: float = _DEFAULT_RUN_TIMEOUT_SECONDS,
) -> SimServiceResult:
    """Run the smoke TB of an already-generated file set through the sandbox.

    Takes a :class:`GenerateFilesResult` (the endpoint owns the 404/422/500
    mapping by generating the files itself, exactly as the other v2 routes do)
    and runs its ``tb`` file against its ``rtl`` files via :func:`run_smoke`.

    Returns a :class:`SimServiceResult`. Never raises for "verilator missing"
    or "sim failed" conditions — those degrade to ``"unavailable"`` / ``"fail"``
    / ``"error"`` — so the endpoint is a straight marshalling call.
    """
    tb_files = [f for f in files_result.files if f.kind == "tb"]
    rtl_files = [f for f in files_result.files if f.kind == "rtl"]

    if not tb_files or not rtl_files:
        return _no_tb_result()

    with tempfile.TemporaryDirectory(prefix="semicraft-simsvc-") as tmpdir:
        workdir = Path(tmpdir)

        rtl_paths: list[Path] = []
        for f in rtl_files:
            path = workdir / f.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f.text, encoding="utf-8")
            rtl_paths.append(path)

        # A module produces exactly one tb file today; if that ever changes,
        # the first tb file is the smoke TB (rtl-first ordering, tb last).
        tb_file = tb_files[0]
        tb_path = workdir / tb_file.path
        tb_path.parent.mkdir(parents=True, exist_ok=True)
        tb_path.write_text(tb_file.text, encoding="utf-8")

        # run_smoke needs its OWN -Mdir (it drops Verilator build artefacts and
        # the binary there); give it a subdir so it never collides with the
        # source files we just wrote.
        build_dir = workdir / "build"
        build_dir.mkdir(parents=True, exist_ok=True)

        sim = run_smoke(
            tb_path,
            rtl_paths,
            compile_timeout_s=compile_timeout_s,
            run_timeout_s=run_timeout_s,
            workdir=build_dir,
        )

    status = _STATUS_MAP.get(sim.status, "error")
    marker_seen = _PASS_MARKER in (sim.stdout_tail or "")

    return SimServiceResult(
        status=status,
        exit_code=sim.exit_code,
        stdout_tail=sim.stdout_tail,
        stderr_tail=sim.stderr_tail,
        duration_s=sim.duration_s,
        marker_seen=marker_seen,
    )
