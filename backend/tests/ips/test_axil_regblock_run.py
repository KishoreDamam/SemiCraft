"""Verilator compile+run gate for the AXI4-Lite register block (P4-02).

Two halves, and the second is the important one:

1. The generated testbench must **pass** against the generated RTL, across
   every configuration axis.
2. Deliberately broken generators must make it **fail**. A run gate that
   cannot fail is not a gate, and a transaction sequence over a bus protocol
   is exactly the kind of test that can look thorough while proving nothing —
   drive some signals, check a response code, never actually exercise the
   behaviour. The mutations below each break one documented rule and assert
   the suite notices.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import regblock
from semicraft_core.ir.nodes import Concat, Ref
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "defaults": {},
    "whole_word_fields": {"split_fields": False},
    "data_width_64": {"data_width": 64},
    "no_scratch": {"include_scratch": False},
    "scratch_only": {
        "control_regs": 0,
        "status_regs": 0,
        "irq_regs": 0,
        "command_regs": 0,
    },
    "many_registers": {
        "control_regs": 2,
        "status_regs": 2,
        "irq_regs": 2,
        "command_regs": 2,
    },
    "async_reset": {"reset_style": "async"},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("axil-regblock", options)
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
def test_regblock_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"AXI4-Lite register block run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"Expected values come from the reference model in axil_regblock.py, "
        f"derived from the access-type rules — if this fails, the model and the "
        f"generator disagree. Fix whichever is wrong; do not copy what the "
        f"simulator printed.\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls: the gate must be able to fail
# --------------------------------------------------------------------------- #


def _ignore_byte_strobes(reg, f):
    """Write the whole field regardless of wstrb."""
    return regblock._range_of("wdata_q", f)


def _leak_write_only_fields(reg, data_width):
    """Read back write-only fields instead of zeroing them."""
    parts: list = []
    pos = 0
    for f in reg.fields:
        if f.lsb > pos:
            parts.append(regblock._zeros(f.lsb - pos))
        parts.append(Ref(regblock.hw_port_name(reg, f)))
        pos = f.msb + 1
    if pos < data_width:
        parts.append(regblock._zeros(data_width - pos))
    return Concat(list(reversed(parts))) if len(parts) > 1 else parts[0]


def _drop_w1c_set(reg, f):
    """Lose the hardware set when no write is in flight."""
    return Ref(regblock.hw_port_name(reg, f))


def _no_reserved_bits(reg, data_width):
    """Never consider any bit reserved, so a reserved write is accepted."""
    return 0


_MUTATIONS = {
    "byte_strobes_ignored": ("_byte_merged", _ignore_byte_strobes, {}),
    "write_only_leaks": ("_read_word_expr", _leak_write_only_fields, {}),
    "w1c_set_dropped": ("_w1c_idle", _drop_w1c_set, {}),
    "reserved_check_disabled": ("write_reserved_mask", _no_reserved_bits, {}),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_generator_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Each mutation breaks one documented rule; the run gate must catch it.

    The patch targets ``regblock``'s own globals, which the RTL builder resolves
    at call time, while ``axil_regblock`` keeps the real helpers it imported by
    name — so the *expected values* stay correct and only the *hardware* is
    wrong. Generating once first matters: the registry imports ``axil_regblock``
    lazily, and letting that happen after the patch would corrupt the reference
    model too, making the mutation invisible. That mistake made one of these
    mutations look like a passing test.
    """
    generate_files("axil-regblock", {})  # force the lazy registry import

    attr, replacement, options = _MUTATIONS[name]
    monkeypatch.setattr(regblock, attr, replacement)

    result = _run(tmp_path, options)
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the AXI transaction "
        f"sequence does not actually test this behaviour, so a real regression "
        f"here would ship silently.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )
