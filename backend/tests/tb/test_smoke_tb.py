"""P2-13 smoke-testbench generator tests.

Covers: end-to-end emission through generate_files, name-map consistency with
the rendered RTL (the correctness trap: styled/active-low names must match),
reset polarity sequences, mixed-language DUTs, a structural sweep over every
registered module, and determinism.
"""

from __future__ import annotations

import re

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.snippets import registry

MODULE_IDS = sorted(m.id for m in registry.by_kind("module"))


def _tb(item_id: str, options: dict | None = None) -> str:
    res = generate_files(item_id, options or {})
    return next(f.text for f in res.files if f.kind == "tb")


def _rtl(item_id: str, options: dict | None = None) -> str:
    res = generate_files(item_id, options or {})
    return next(f.text for f in res.files if f.kind == "rtl")


# --------------------------------------------------------------------------- #
# structural sweep: every module, both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("item_id", MODULE_IDS)
@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_every_module_emits_wellformed_tb(item_id: str, language: str) -> None:
    res = generate_files(item_id, {"language": language})
    tb = next(f for f in res.files if f.kind == "tb")

    assert tb.path.endswith("_tb.sv")  # TB is always SystemVerilog
    text = tb.text
    assert "`timescale 1ns/1ps" in text
    assert re.search(r"module \w+_tb;", text)
    assert "$finish" in text
    assert "SMOKE PASS" in text
    assert text.rstrip().endswith("endmodule")

    # DUT instance references the RTL module name and only rendered port names.
    rtl = next(f for f in res.files if f.kind == "rtl")
    dut_module = re.search(r"module (\w+)", rtl.text).group(1)
    assert f"{dut_module} dut (" in text
    for port in re.findall(r"\.(\w+)\s*\(", text):
        assert re.search(rf"\b{port}\b", rtl.text), f"TB port {port} not in RTL"


@pytest.mark.parametrize("item_id", MODULE_IDS)
def test_tb_signal_names_match_rendered_rtl(item_id: str) -> None:
    """Every net the TB drives or checks exists verbatim in the rendered RTL."""
    res = generate_files(item_id, {})
    tb = next(f.text for f in res.files if f.kind == "tb")
    rtl = next(f.text for f in res.files if f.kind == "rtl")
    for name in re.findall(r"^\s*(\w+)\s*=\s*\d+'d\d+;", tb, flags=re.M):
        assert re.search(rf"\b{name}\b", rtl), f"driven net {name} missing from RTL"


# --------------------------------------------------------------------------- #
# reset polarity sequences
# --------------------------------------------------------------------------- #


def test_active_low_reset_sequence() -> None:
    tb = _tb("edge-detector", {"reset_polarity": "active_low"})
    # Assert low, wait, deassert high — and the styled name carries _n.
    assert "rst_n = 1'd0;" in tb
    assert tb.index("rst_n = 1'd0;") < tb.index("rst_n = 1'd1;")


def test_active_high_reset_sequence() -> None:
    tb = _tb("edge-detector", {"reset_polarity": "active_high"})
    assert "rst = 1'd1;" in tb
    assert tb.index("rst = 1'd1;") < tb.index("rst = 1'd0;")
    assert "rst_n" not in tb


# --------------------------------------------------------------------------- #
# mixed language: verilog DUT still gets an SV testbench
# --------------------------------------------------------------------------- #


def test_verilog_dut_gets_sv_tb_with_correct_instance() -> None:
    res = generate_files("pwm", {"language": "verilog"})
    paths = {f.kind: f.path for f in res.files}
    assert paths["rtl"].endswith(".v")
    assert paths["tb"].endswith("_tb.sv")
    tb = next(f.text for f in res.files if f.kind == "tb")
    assert "pwm dut (" in tb


# --------------------------------------------------------------------------- #
# header + determinism
# --------------------------------------------------------------------------- #


def test_tb_header_carries_hash_and_disclaimer() -> None:
    res = generate_files("debouncer", {})
    tb = next(f.text for f in res.files if f.kind == "tb")
    assert res.config_hash in tb
    assert "without warranty" in tb


def test_tb_deterministic() -> None:
    a = _tb("rr-arbiter", {"num_requesters": 8})
    b = _tb("rr-arbiter", {"num_requesters": 8})
    assert a == b


def test_snippets_emit_no_tb() -> None:
    res = generate_files("counter", {})
    assert [f.kind for f in res.files] == ["rtl"]
