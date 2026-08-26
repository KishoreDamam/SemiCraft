"""Verilator compile+run gate for the synchronous RAM (P4-04).

Configurations that must pass, plus broken generators that must fail. The
mutation that matters most is write-first: a RAM whose read-during-write
returns the *new* data is a completely different component, and nothing in the
port list distinguishes the two — only a directed check does.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import ram
from semicraft_core.ir.nodes import Assign, Bit, Const, If, Ref, Ternary
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "defaults": {},
    "simple_dual": {"port_mode": "simple_dual"},
    "no_read_enable": {"read_enable": False},
    "dual_without_read_enable": {"port_mode": "simple_dual", "read_enable": False},
    "depth_2_width_1": {"depth": 2, "width": 1},
    "wide_deep": {"depth": 1024, "width": 64},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("sync-ram", options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")
    return run_smoke(tb_path, [rtl_path])


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_ram_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"RAM run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #


def _write_first(opts):
    """Bypass the write data onto dout — READ_FIRST becomes WRITE_FIRST.

    The defining behaviour this RAM documents. A generator that got it wrong
    would still compile, still lint clean, and still pass a testbench that only
    writes and reads on separate cycles.
    """
    load = Assign(
        Ref("dout"),
        Ternary(Ref("we"), Ref("din"), Bit(Ref("mem"), Ref(opts.read_addr))),
    )
    if not opts.read_enable:
        return load
    return If(Ref("re"), then=[load])


def _write_ignores_enable(opts):
    """Drop the `we` guard, so every cycle writes whatever din holds."""
    return Assign(Bit(Ref("mem"), Ref(opts.write_addr)), Ref("din"))


def _read_ignores_enable(opts):
    """Drop the `re` guard, so dout reloads even when the read is gated off."""
    return Assign(Ref("dout"), Bit(Ref("mem"), Ref(opts.read_addr)))


def _write_to_address_zero(opts):  # noqa: ARG001
    """Every write lands at address 0, destroying addressing."""
    return If(
        Ref("we"),
        then=[Assign(Bit(Ref("mem"), Const(0)), Ref("din"))],
    )


_MUTATIONS = {
    "write_first_bypass": ("_read_stmt", _write_first, {}),
    "write_enable_ignored": ("_write_stmt", _write_ignores_enable, {}),
    "read_enable_ignored": ("_read_stmt", _read_ignores_enable, {}),
    "all_writes_to_address_zero": ("_write_stmt", _write_to_address_zero, {}),
    "dual_write_first": ("_read_stmt", _write_first, {"port_mode": "simple_dual"}),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_ram_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Generating once first forces the registry's lazy import, so the module
    binds the real helpers before they are patched — otherwise the expected
    values would be derived from the mutated generator and agree with it."""
    generate_files("sync-ram", {})

    attr, replacement, options = _MUTATIONS[name]
    monkeypatch.setattr(ram, attr, replacement)

    result = _run(tmp_path, options)
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the RAM testbench does "
        f"not actually exercise this behaviour.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )
