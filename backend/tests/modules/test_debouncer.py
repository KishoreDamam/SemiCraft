"""Debouncer module: generation, options, determinism, explanation,
port_groups/tb_spec shape (mirrors test_edge_detector.py).
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from pydantic import ValidationError
from semicraft_core import config_hash, generate
from semicraft_core.ir import validate
from semicraft_core.modules.contract import Check, PortGroup, TbSpec
from semicraft_core.modules.debouncer import DebouncerOptions, port_groups, tb_spec
from semicraft_core.modules.debouncer import generate as build_ir
from semicraft_core.render import render
from semicraft_core.snippets import registry

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("debouncer", {"language": language})
    assert result.code
    validate(build_ir(DebouncerOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"debouncer.{ext}"


def test_default_sv_shape() -> None:
    code = generate("debouncer", {}).code
    assert "module debouncer #(" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "CNT_WIDTH" in code
    assert "endmodule" in code


def test_verilog_infers_reg_and_plain_always() -> None:
    code = generate("debouncer", {"language": "verilog"}).code
    assert "always @(posedge clk) begin" in code
    assert "reg " in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_counter_width_changes_param() -> None:
    code = generate("debouncer", {"counter_width": 20}).code
    assert "CNT_WIDTH = 20" in code


def test_active_level_high_reset_value() -> None:
    code = generate("debouncer", {"active_level": "high"}).code
    assert "q <= 1'b1;" in code


def test_active_level_low_reset_value() -> None:
    code = generate("debouncer", {"active_level": "low"}).code
    assert "q <= 1'b0;" in code


def test_disagreement_logic_present() -> None:
    code = generate("debouncer", {}).code
    assert "d_in != q" in code
    assert "q <= d_in;" in code


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "debouncer",
        {"reset_style": reset_style, "reset_polarity": reset_polarity},
    ).code
    if reset_polarity == "active_low":
        assert "rst_n" in code
        assert "if (!rst_n)" in code
    else:
        assert "if (rst)" in code
    if reset_style == "async":
        assert " or " in code  # reset edge in the sensitivity list
    else:
        assert "always_ff @(posedge clk) begin" in code


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"counter_width": 10, "active_level": "low"}
    a = generate("debouncer", opts)
    b = generate("debouncer", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('debouncer', {'counter_width':12,'active_level':'low'});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("debouncer", {"counter_width": 8}).config_hash
    b = generate("debouncer", {"counter_width": 9}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("debouncer", {"counter_width": 12, "active_level": "low"}).config_hash
    b = generate("debouncer", {"active_level": "low", "counter_width": 12}).config_hash
    assert a == b


def test_config_hash_function_matches_entry_point() -> None:
    opts = DebouncerOptions(counter_width=12)
    expected = config_hash("debouncer", opts.model_dump(mode="json"))
    assert generate("debouncer", {"counter_width": 12}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_counter_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("debouncer", {"counter_width": 3})
    with pytest.raises(ValidationError):
        generate("debouncer", {"counter_width": 25})


def test_bad_active_level_enum_raises() -> None:
    with pytest.raises(ValidationError):
        generate("debouncer", {"active_level": "sideways"})


def test_bad_bool_raises() -> None:
    with pytest.raises(ValidationError):
        generate("debouncer", {"active_level": "maybe"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("debouncer", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("debouncer", {"counter_width": 10}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 4  # clk, rst, d_in, cnt, q
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "d_in", "cnt", "q"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any(
        "synchron" in limit.lower() or "2-flop" in limit.lower() or "cdc" in limit.lower()
        for limit in exp.limitations
    )


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "debouncer", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronously" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


def test_explanation_reflects_counter_width() -> None:
    exp4 = generate("debouncer", {"counter_width": 4}).explanation
    exp8 = generate("debouncer", {"counter_width": 8}).explanation
    assert str(2**4) in exp4.purpose
    assert str(2**8) in exp8.purpose


# --------------------------------------------------------------------------- #
# port_groups shape
# --------------------------------------------------------------------------- #


def test_port_groups_shape() -> None:
    groups = port_groups(DebouncerOptions())
    assert all(isinstance(g, PortGroup) for g in groups)
    names = [g.name for g in groups]
    assert names == ["Clocking", "Data"]
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "d_in", "q"}
    for g in groups:
        assert g.description.strip()
        assert g.ports


def test_port_groups_reset_name_tracks_polarity() -> None:
    low = port_groups(DebouncerOptions(reset_polarity="active_low"))
    high = port_groups(DebouncerOptions(reset_polarity="active_high"))
    assert "rst_n" in low[0].ports
    assert "rst" in high[0].ports and "rst_n" not in high[0].ports


def test_port_groups_names_match_explanation_signals() -> None:
    opts = DebouncerOptions()
    exp_names = {s.name for s in generate("debouncer", {}).explanation.signals}
    for group in port_groups(opts):
        for port_name in group.ports:
            assert port_name in exp_names, port_name


# --------------------------------------------------------------------------- #
# tb_spec shape (checks are recipes; NOT executed yet — P2-13)
# --------------------------------------------------------------------------- #


def test_tb_spec_shape() -> None:
    spec = tb_spec(DebouncerOptions())
    assert isinstance(spec, TbSpec)
    assert spec.clock == "clk"
    assert spec.reset == "rst"
    assert spec.reset_cycles == 2
    assert len(spec.vectors) == 8
    assert all(set(v) == {"d_in"} for v in spec.vectors)
    assert len(spec.checks) == 2
    assert all(isinstance(c, Check) for c in spec.checks)


def test_tb_spec_active_level_flips_idle() -> None:
    high = tb_spec(DebouncerOptions(active_level="high"))
    low = tb_spec(DebouncerOptions(active_level="low"))
    assert high.vectors[0]["d_in"] == 1
    assert low.vectors[0]["d_in"] == 0


def test_tb_spec_signals_reference_real_ports() -> None:
    spec = tb_spec(DebouncerOptions())
    code = generate("debouncer", {}).code
    assert spec.clock in code and spec.reset in code
    for v in spec.vectors:
        for sig in v:
            assert sig in code
    for check in spec.checks:
        assert check.signal in code


# --------------------------------------------------------------------------- #
# registry / options schema
# --------------------------------------------------------------------------- #


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("debouncer").options_model.model_json_schema()
    props = schema["properties"]
    assert props["counter_width"]["description"]
    assert props["active_level"]["description"]
    assert set(props["active_level"]["enum"]) == {"high", "low"}


def test_generated_ir_is_valid() -> None:
    for opts in (
        DebouncerOptions(),
        DebouncerOptions(counter_width=24, active_level="low"),
        DebouncerOptions(reset_style="async", reset_polarity="active_high"),
    ):
        code = render(build_ir(opts), language="sv")
        assert "endmodule" in code
