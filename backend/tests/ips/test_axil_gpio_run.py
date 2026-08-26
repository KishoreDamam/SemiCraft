"""Verilator compile+run gate for the AXI4-Lite GPIO (P4-05a).

This is the first *composed* IP — a spliced register block plus a peripheral —
so the gate has to prove two things: the composition works, and the testbench
can tell a correct composition from a plausible-looking one.

The ``synchroniser_bypassed`` mutation is the interesting one. A read of IN
long after the pins settle passes whether or not the synchroniser exists, so
the testbench also reads IN *immediately* after driving the pins and requires
the old value. Without that check, dropping a metastability guard on an
asynchronous input — a defect that never shows up in simulation — would sail
straight through.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import axil_gpio
from semicraft_core.ir.nodes import Const, ConstBase, ContAssign, ModuleItem, Ref
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "defaults": {},
    "one_pin": {"num_pins": 1},
    "full_width": {"num_pins": 32},
    "odd_width": {"num_pins": 13},
    "deep_synchroniser": {"input_sync_stages": 4},
    "async_reset": {"reset_style": "async"},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("axil-gpio", options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")
    return run_smoke(tb_path, [rtl_path])


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_gpio_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"GPIO run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #


def _swap_dir_and_out(stages: list[str]) -> list[ModuleItem]:
    """Drive the pins from DIR and the enables from OUT."""
    return [
        ContAssign(Ref("gpio_oe"), Ref("out_value")),
        ContAssign(Ref("gpio_out"), Ref("dir_value")),
        ContAssign(Ref("in_value"), Ref(stages[-1])),
    ]


def _bypass_synchroniser(stages: list[str]) -> list[ModuleItem]:  # noqa: ARG001
    """Feed the raw asynchronous pin straight into the IN register."""
    return [
        ContAssign(Ref("gpio_oe"), Ref("dir_value")),
        ContAssign(Ref("gpio_out"), Ref("out_value")),
        ContAssign(Ref("in_value"), Ref("gpio_in")),
    ]


def _outputs_never_enabled(stages: list[str]) -> list[ModuleItem]:
    return [
        ContAssign(Ref("gpio_oe"), Const(0, width=Const(1), base=ConstBase.BIN)),
        ContAssign(Ref("gpio_out"), Ref("out_value")),
        ContAssign(Ref("in_value"), Ref(stages[-1])),
    ]


def _first_stage_only(stages: list[str]) -> list[ModuleItem]:
    """Read from the first synchroniser flop — one stage short of safe."""
    return [
        ContAssign(Ref("gpio_oe"), Ref("dir_value")),
        ContAssign(Ref("gpio_out"), Ref("out_value")),
        ContAssign(Ref("in_value"), Ref(stages[0])),
    ]


_MUTATIONS = {
    "dir_and_out_swapped": (_swap_dir_and_out, {}),
    "synchroniser_bypassed": (_bypass_synchroniser, {}),
    "outputs_never_enabled": (_outputs_never_enabled, {}),
    "one_stage_short": (_first_stage_only, {}),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_gpio_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Generating once first forces the registry's lazy import, so the module
    binds the real helpers before they are patched."""
    generate_files("axil-gpio", {})

    replacement, options = _MUTATIONS[name]
    monkeypatch.setattr(axil_gpio, "_glue_assignments", replacement)

    result = _run(tmp_path, options)
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the GPIO testbench does "
        f"not actually exercise this wiring.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )
