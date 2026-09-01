"""Verilator compile+run gate for the AXI4-Lite timer (P4-08).

The mutations here all attack *timing*, because timing is the whole of what a
timer does and the easiest thing for a testbench to accept without checking.
The pair of checks around each expiry — ``irq`` low on the cycle before the
derived rise, high on it — is what gives them something to fail against: a
single "high at cycle N" check would pass for a timer that fired early, which
is exactly what ``prescaler_ignored`` and ``terminal_off_by_one`` produce.

``always_reload`` is the odd one out: it fires at the right moment and only
diverges afterwards, so it is caught by the three idle periods that follow the
one-shot expiry rather than by the expiry itself.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import axil_timer
from semicraft_core.ips.axil_timer import AxilTimerOptions, _f, _one, _zero
from semicraft_core.ir.nodes import ContAssign, Ref
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "defaults": {},
    "narrow_counter": {"counter_width": 4},
    "no_prescaler": {"prescale_width": 1},
    "wide_prescaler": {"prescale_width": 32},
    "async_reset": {"reset_style": "async"},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("axil-timer", options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")

    # The P4-09 verification scaffold, compiled in alongside the DUT. It binds
    # itself, so nothing else here changes - but every option case below now
    # runs the bus checks too, which is far wider coverage than the scaffold's
    # own gate can afford. Absent for a Verilog build (`bind` is SV-only).
    sources = [rtl_path]
    checks = next((f for f in res.files if f.path.endswith("_checks.sv")), None)
    if checks is not None:
        checks_path = tmp_path / checks.path
        checks_path.write_text(checks.text, encoding="utf-8")
        sources.append(checks_path)
    return run_smoke(tb_path, sources)


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_timer_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"timer run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #


def _tick_every_clock(opts: AxilTimerOptions):  # noqa: ARG001
    """Ignore PRESCALE: every clock is a tick, so the timer expires early."""
    return _one()


def _terminal_at_one(opts: AxilTimerOptions):
    """Expire at COUNT == 1 — one tick short of the programmed period."""
    from semicraft_core.ips.axil_timer import _eq

    return _eq(Ref(_f("COUNT", "value")), _one(opts.counter_width))


def _always_reload(opts: AxilTimerOptions):  # noqa: ARG001
    """Restart at every expiry, so one-shot mode is silently periodic."""
    return _one()


def _irq_unmasked(*_args):
    """Drive irq straight from the flag, ignoring CTRL.irq_enable."""
    return [ContAssign(Ref("irq"), Ref(_f("STATUS", "expired")))]


def _irq_never(*_args):
    """Never request an interrupt."""
    return [ContAssign(Ref("irq"), _zero())]


_MUTATIONS = {
    "prescaler_ignored": ("_tick_condition", _tick_every_clock),
    "terminal_off_by_one": ("_terminal_condition", _terminal_at_one),
    "always_reload": ("_reload_condition", _always_reload),
    "irq_unmasked": ("_glue_assignments", _irq_unmasked),
    "irq_never_raised": ("_glue_assignments", _irq_never),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_timer_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Generating once first forces the registry's lazy import, so the module
    binds the real helpers before they are patched."""
    generate_files("axil-timer", {})

    attr, replacement = _MUTATIONS[name]
    monkeypatch.setattr(axil_timer, attr, replacement)

    result = _run(tmp_path, {})
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the timer testbench "
        f"does not actually exercise this behaviour.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )
