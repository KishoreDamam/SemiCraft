"""Clock-divider module: generation, options, determinism, explanation,
port_groups/tb_spec shape (mirrors test_edge_detector.py).
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from pydantic import ValidationError
from semicraft_core import config_hash, generate
from semicraft_core.ir import validate
from semicraft_core.modules.clock_divider import ClockDividerOptions, port_groups, tb_spec
from semicraft_core.modules.clock_divider import generate as build_ir
from semicraft_core.modules.contract import Check, PortGroup, TbSpec
from semicraft_core.render import render
from semicraft_core.snippets import registry

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("clock-divider", {"language": language})
    assert result.code
    validate(build_ir(ClockDividerOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"clock_divider.{ext}"


def test_default_sv_shape() -> None:
    code = generate("clock-divider", {}).code
    assert "module clock_divider #(" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "CNT_WIDTH = 1" in code  # DIV is not a param (Verilator UNUSEDPARAM)
    assert "endmodule" in code


def test_verilog_infers_reg_and_plain_always() -> None:
    code = generate("clock-divider", {"language": "verilog"}).code
    assert "always @(posedge clk) begin" in code
    assert "reg " in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_toggle_style_toggles_clk_out() -> None:
    code = generate("clock-divider", {"output_enable_style": "toggle"}).code
    assert "clk_out <= ~clk_out;" in code


def test_pulse_style_pulses_clk_out() -> None:
    code = generate("clock-divider", {"output_enable_style": "pulse"}).code
    assert "clk_out <= 1'b1;" in code
    assert "clk_out <= 1'b0;" in code
    assert "~clk_out" not in code


def test_divide_by_changes_counter_constants() -> None:
    # DIV is baked into the comparison constants, not emitted as a param.
    code = generate("clock-divider", {"divide_by": 100}).code
    assert "DIV =" not in code  # ratio baked into constants, not a param
    assert "CNT_WIDTH = 7" in code  # clog2(100)


def test_divide_by_changes_counter_width_param() -> None:
    narrow = generate("clock-divider", {"divide_by": 2}).code
    wide = generate("clock-divider", {"divide_by": 65536}).code
    assert "CNT_WIDTH = 1" in narrow
    assert "CNT_WIDTH = 16" in wide


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "clock-divider",
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
    opts = {"divide_by": 100, "output_enable_style": "pulse"}
    a = generate("clock-divider", opts)
    b = generate("clock-divider", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('clock-divider', {'divide_by':64,'output_enable_style':'pulse'});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("clock-divider", {"divide_by": 4}).config_hash
    b = generate("clock-divider", {"divide_by": 6}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("clock-divider", {"divide_by": 4, "output_enable_style": "pulse"}).config_hash
    b = generate("clock-divider", {"output_enable_style": "pulse", "divide_by": 4}).config_hash
    assert a == b


def test_config_hash_function_matches_entry_point() -> None:
    opts = ClockDividerOptions(divide_by=8)
    expected = config_hash("clock-divider", opts.model_dump(mode="json"))
    assert generate("clock-divider", {"divide_by": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_divide_by_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("clock-divider", {"divide_by": 1})
    with pytest.raises(ValidationError):
        generate("clock-divider", {"divide_by": 65537})


def test_odd_divide_by_raises() -> None:
    with pytest.raises(ValidationError):
        generate("clock-divider", {"divide_by": 3})
    with pytest.raises(ValidationError):
        generate("clock-divider", {"divide_by": 65535})


def test_bad_output_enable_style_enum_raises() -> None:
    with pytest.raises(ValidationError):
        generate("clock-divider", {"output_enable_style": "sideways"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("clock-divider", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("clock-divider", {"divide_by": 10}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 3  # clk, rst, cnt, clk_out
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "cnt", "clk_out"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any(
        "not a low-skew clock" in limit or "PLL" in limit or "MMCM" in limit
        for limit in exp.limitations
    )


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "clock-divider", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronously" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


def test_explanation_reflects_output_style() -> None:
    toggle = generate("clock-divider", {"output_enable_style": "toggle"}).explanation
    pulse = generate("clock-divider", {"output_enable_style": "pulse"}).explanation
    assert "toggle" in toggle.purpose
    assert "pulse" in pulse.purpose


# --------------------------------------------------------------------------- #
# port_groups shape
# --------------------------------------------------------------------------- #


def test_port_groups_shape() -> None:
    groups = port_groups(ClockDividerOptions())
    assert all(isinstance(g, PortGroup) for g in groups)
    names = [g.name for g in groups]
    assert names == ["Clocking", "Data"]
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "clk_out"}
    for g in groups:
        assert g.description.strip()
        assert g.ports


def test_port_groups_reset_name_tracks_polarity() -> None:
    low = port_groups(ClockDividerOptions(reset_polarity="active_low"))
    high = port_groups(ClockDividerOptions(reset_polarity="active_high"))
    assert "rst_n" in low[0].ports
    assert "rst" in high[0].ports and "rst_n" not in high[0].ports


def test_port_groups_names_match_explanation_signals() -> None:
    opts = ClockDividerOptions()
    exp_names = {s.name for s in generate("clock-divider", {}).explanation.signals}
    for group in port_groups(opts):
        for port_name in group.ports:
            assert port_name in exp_names, port_name


# --------------------------------------------------------------------------- #
# tb_spec shape (checks are recipes; NOT executed yet — P2-13)
# --------------------------------------------------------------------------- #


def test_tb_spec_shape() -> None:
    spec = tb_spec(ClockDividerOptions())
    assert isinstance(spec, TbSpec)
    assert spec.clock == "clk"
    assert spec.reset == "rst"
    assert spec.reset_cycles == 2
    assert len(spec.vectors) >= 4
    assert len(spec.checks) == 2
    assert all(isinstance(c, Check) for c in spec.checks)


def test_tb_spec_style_changes_checks() -> None:
    toggle = tb_spec(ClockDividerOptions(output_enable_style="toggle", divide_by=4))
    pulse = tb_spec(ClockDividerOptions(output_enable_style="pulse", divide_by=4))
    assert toggle.checks != pulse.checks


def test_tb_spec_signals_reference_real_ports() -> None:
    spec = tb_spec(ClockDividerOptions())
    code = generate("clock-divider", {}).code
    assert spec.clock in code and spec.reset in code
    for check in spec.checks:
        assert check.signal in code


# --------------------------------------------------------------------------- #
# registry / options schema
# --------------------------------------------------------------------------- #


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("clock-divider").options_model.model_json_schema()
    props = schema["properties"]
    assert props["divide_by"]["description"]
    assert props["output_enable_style"]["description"]
    assert set(props["output_enable_style"]["enum"]) == {"toggle", "pulse"}


def test_generated_ir_is_valid() -> None:
    for opts in (
        ClockDividerOptions(),
        ClockDividerOptions(divide_by=1024, output_enable_style="pulse"),
        ClockDividerOptions(reset_style="async", reset_polarity="active_high"),
    ):
        code = render(build_ir(opts), language="sv")
        assert "endmodule" in code
