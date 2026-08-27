"""Verilator compile+run gate for the AXI4-Lite interrupt controller (P4-08).

Three families of mutation, one per thing the controller actually decides.

*Where the mask is applied.* ``mask_before_latch`` moves ENABLE into the latch,
so a request arriving while masked is lost; ``status_ignores_mask`` drops it
from the masked view, so a masked source raises the output. Both are caught by
the opening section, which deliberately latches a request before enabling it.

*Which value is trusted.* ``synchroniser_bypassed`` and ``one_stage_short``
take the request from the pin or from the first flop instead of the settled
last stage. Simulation has no metastability, so neither produces a wrong
*value* — only a wrong *latency*, and the read issued exactly on the settling
cycle is what turns that into a failure.

*What counts as a request.* ``level_instead_of_edge`` and its inverse swap the
trigger. Every pulse in the sequence latches identically under both, so these
are caught only by the final section, which holds a source asserted across a
write-1-to-clear.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import axil_intc
from semicraft_core.ips.axil_intc import _HIST, AxilIntcOptions, _f, _set, _sync_stage
from semicraft_core.ir.nodes import (
    BinOp,
    BinOpKind,
    ContAssign,
    ModuleItem,
    Ref,
    UnaryOp,
    UnaryOpKind,
)
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

_CASES = {
    "defaults": {},
    "one_source": {"num_irq": 1},
    "full_width": {"num_irq": 32},
    "odd_width": {"num_irq": 13},
    "level_triggered": {"trigger": "level"},
    "deep_synchroniser": {"input_sync_stages": 4},
    "async_reset": {"reset_style": "async"},
    "verilog": {"language": "verilog"},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _run(tmp_path: Path, options: dict) -> SimResult:
    res = generate_files("axil-intc", options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")
    return run_smoke(tb_path, [rtl_path])


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("case", sorted(_CASES), ids=sorted(_CASES))
def test_intc_tb_runs(case: str, tmp_path: Path) -> None:
    result = _run(tmp_path, _CASES[case])
    assert result.status == "pass", (
        f"interrupt-controller run gate failed for case {case!r} "
        f"(status={result.status!r}, exit_code={result.exit_code}).\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #


def _rising(source: str) -> BinOp:
    return BinOp(
        BinOpKind.AND, Ref(source), UnaryOp(UnaryOpKind.NOT_BITWISE, Ref(_HIST))
    )


def _level_trigger(opts: AxilIntcOptions, settled: str):  # noqa: ARG001
    """Latch the level even when the IP was asked for edge triggering."""
    return Ref(settled)


def _edge_trigger(opts: AxilIntcOptions, settled: str):  # noqa: ARG001
    """Latch a rising edge even when the IP was asked for level triggering.

    Needs a history flop, which a level-triggered build does not declare, so
    the second-to-last synchroniser stage stands in. That is the wrong place to
    take it from for real hardware — which is the point of the mutation next
    door — but here it only has to change the semantics.
    """
    return BinOp(
        BinOpKind.AND,
        Ref(settled),
        UnaryOp(UnaryOpKind.NOT_BITWISE, Ref(_sync_stage(0))),
    )


def _mask_before_latch(opts: AxilIntcOptions, settled: str) -> list[ModuleItem]:
    """Gate the latch with ENABLE, losing requests that arrive while masked."""
    return [
        ContAssign(
            Ref(_set("PENDING")),
            BinOp(BinOpKind.AND, _rising(settled), Ref(_f("ENABLE"))),
        ),
        ContAssign(
            Ref(_f("STATUS")),
            BinOp(BinOpKind.AND, Ref(_f("PENDING")), Ref(_f("ENABLE"))),
        ),
        ContAssign(Ref("irq_out"), UnaryOp(UnaryOpKind.RED_OR, Ref(_f("STATUS")))),
    ]


def _status_ignores_mask(opts: AxilIntcOptions, settled: str) -> list[ModuleItem]:
    """Report every pending source as requesting, enabled or not."""
    return [
        ContAssign(Ref(_set("PENDING")), _rising(settled)),
        ContAssign(Ref(_f("STATUS")), Ref(_f("PENDING"))),
        ContAssign(Ref("irq_out"), UnaryOp(UnaryOpKind.RED_OR, Ref(_f("STATUS")))),
    ]


def _from_pin(opts: AxilIntcOptions, settled: str) -> list[ModuleItem]:  # noqa: ARG001
    """Latch straight off the asynchronous pin — no synchroniser at all."""
    return _glue_from("irq_in")


def _from_first_stage(opts: AxilIntcOptions, settled: str) -> list[ModuleItem]:  # noqa: ARG001
    """Latch off the first synchroniser flop — one stage short of settled."""
    return _glue_from(_sync_stage(0))


def _glue_from(source: str) -> list[ModuleItem]:
    return [
        ContAssign(Ref(_set("PENDING")), _rising(source)),
        ContAssign(
            Ref(_f("STATUS")),
            BinOp(BinOpKind.AND, Ref(_f("PENDING")), Ref(_f("ENABLE"))),
        ),
        ContAssign(Ref("irq_out"), UnaryOp(UnaryOpKind.RED_OR, Ref(_f("STATUS")))),
    ]


_MUTATIONS = {
    "mask_before_latch": ("_glue_assignments", _mask_before_latch, {}),
    "status_ignores_mask": ("_glue_assignments", _status_ignores_mask, {}),
    "synchroniser_bypassed": ("_glue_assignments", _from_pin, {}),
    "one_stage_short": ("_glue_assignments", _from_first_stage, {}),
    "level_instead_of_edge": ("_trigger_expr", _level_trigger, {}),
    "edge_instead_of_level": ("_trigger_expr", _edge_trigger, {"trigger": "level"}),
}


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_MUTATIONS), ids=sorted(_MUTATIONS))
def test_a_broken_intc_fails_the_gate(name: str, tmp_path: Path, monkeypatch) -> None:
    """Generating once first forces the registry's lazy import, so the module
    binds the real helpers before they are patched."""
    generate_files("axil-intc", {})

    attr, replacement, options = _MUTATIONS[name]
    monkeypatch.setattr(axil_intc, attr, replacement)

    result = _run(tmp_path, options)
    assert result.status != "pass", (
        f"mutation {name!r} did not fail the run gate — the interrupt-controller "
        f"testbench does not actually exercise this behaviour.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )
