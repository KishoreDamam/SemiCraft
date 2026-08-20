"""Unit tests for the cocotb testbench backend (P3-08, beta).

Text-level properties only — that the emitted Python *runs* is
``test_cocotb_run.py``'s job, and that is the check that actually matters.
"""

from __future__ import annotations

import ast
import re

import pytest
from semicraft_core.generate import _render_rtl, config_hash
from semicraft_core.snippets import registry
from semicraft_core.tb.cocotb_tb import cocotb_tb_filename, generate_cocotb_tb

MODULE_IDS = [d.id for d in registry.by_kind("module")]


def _cocotb_tb(item_id: str, options: dict | None = None) -> str:
    item = registry.get(item_id)
    opts = item.options_model.model_validate(options or {})
    chash = config_hash(item_id, opts.model_dump(mode="json"))
    _, _, _, rtl_module = _render_rtl(item, opts, chash)
    return generate_cocotb_tb(item, opts, rtl_module)


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_emitted_text_is_valid_python(item_id: str) -> None:
    """Parse it. A generator emitting Python that will not compile is the
    cheapest possible failure to catch, and text assertions alone miss it."""
    ast.parse(_cocotb_tb(item_id))


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_is_deterministic(item_id: str) -> None:
    assert _cocotb_tb(item_id) == _cocotb_tb(item_id)


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_has_a_cocotb_test_and_pass_marker(item_id: str) -> None:
    text = _cocotb_tb(item_id)
    assert "@cocotb.test(" in text
    assert "async def smoke(dut):" in text
    # The sim runner's pass semantics key off this marker; both backends emit it.
    assert "SMOKE PASS:" in text


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_targets_cocotb_1x_api(item_id: str) -> None:
    """cocotb 2.x renamed these, and its Verilator shim does not build against
    Verilator 5.020 (the newest in apt). The dev pin is 1.9.2; if that pin ever
    moves, this test should fail loudly rather than emit silently-wrong code."""
    text = _cocotb_tb(item_id)
    assert 'units="ns"' in text
    # Word-boundary match: `timeout_unit="ns"` legitimately contains the
    # substring `unit="ns"`, so a naive `in` check false-positives on it.
    assert re.search(r'\bunit="ns"', text) is None


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_reset_deassert_settles_before_release(item_id: str) -> None:
    """TB_SPEC §6a is normative for both backends.

    The deassert must not share a timestep with the rising edge that ends the
    reset hold — the race that broke 17 golden SV testbenches before P3-09a.
    """
    text = _cocotb_tb(item_id)
    lines = [line.strip() for line in text.splitlines()]
    settle = 'await Timer(1, units="ns")'
    deassert = [
        i
        for i, line in enumerate(lines)
        if line.startswith("dut.rst") and ".value = " in line
    ]
    assert deassert, f"{item_id}: no reset drive found"
    release = deassert[-1]
    assert lines[release - 1] == settle, (
        f"{item_id}: reset deassert at line {release} is not preceded by the "
        f"normative settle; got {lines[release - 1]!r}"
    )


def test_names_match_the_rendered_rtl_under_a_naming_style() -> None:
    """Nets resolve through the same style map as the RTL and the SV TB."""
    text = _cocotb_tb("gray-counter", {"naming": {"convention": "snake", "prefix": "u_"}})
    assert "dut.u_clk" in text
    assert "dut.u_gray" in text


def test_no_clock_module_emits_nothing() -> None:
    """Matches generate_tb: a module with no clock has no smoke recipe."""

    class _NoClock:
        def tb_spec(self, opts):  # noqa: ARG002
            from semicraft_core.modules.contract import TbSpec

            return TbSpec(clock=None)

    item = registry.get("gray-counter")
    opts = item.options_model.model_validate({})
    chash = config_hash("gray-counter", opts.model_dump(mode="json"))
    _, _, _, rtl_module = _render_rtl(item, opts, chash)
    assert generate_cocotb_tb(_NoClock(), opts, rtl_module) == ""


def test_filename_convention() -> None:
    assert cocotb_tb_filename("gray_counter") == "test_gray_counter.py"


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_expected_values_match_the_sv_backend(item_id: str) -> None:
    """Both backends must assert the same expected values.

    They are generated from one ``TbSpec``, so a divergence here means one
    backend mis-renders the recipe — which is exactly how the lfsr serial model
    and its RTL drifted apart before P3-09a.
    """
    from semicraft_core.tb import generate_tb

    item = registry.get(item_id)
    opts = item.options_model.model_validate({})
    chash = config_hash(item_id, opts.model_dump(mode="json"))
    _, _, _, rtl_module = _render_rtl(item, opts, chash)

    spec = item.tb_spec(opts)
    sv = generate_tb(item, opts, rtl_module)
    py = generate_cocotb_tb(item, opts, rtl_module)
    for chk in spec.checks:
        assert f"at cycle {chk.cycle} expected {chk.expected}" in sv
        assert f"at cycle {chk.cycle} expected {chk.expected}" in py
