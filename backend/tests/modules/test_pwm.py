"""PWM module: generation, options, determinism, explanation, port_groups/
tb_spec shape (mirrors test_edge_detector.py).
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from pydantic import ValidationError
from semicraft_core import config_hash, generate
from semicraft_core.ir import validate
from semicraft_core.modules.contract import Check, PortGroup, TbSpec
from semicraft_core.modules.pwm import PwmOptions, port_groups, tb_spec
from semicraft_core.modules.pwm import generate as build_ir
from semicraft_core.render import render
from semicraft_core.snippets import registry

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("pwm", {"language": language})
    assert result.code
    validate(build_ir(PwmOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"pwm.{ext}"


def test_default_sv_shape() -> None:
    code = generate("pwm", {}).code
    assert "module pwm #(" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "assign pwm_out = cnt < duty;" in code
    assert "endmodule" in code


def test_verilog_infers_reg_and_plain_always() -> None:
    code = generate("pwm", {"language": "verilog"}).code
    assert "always @(posedge clk) begin" in code
    assert "reg " in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_resolution_changes_param() -> None:
    code = generate("pwm", {"resolution": 12}).code
    assert "RES = 12" in code


def test_duty_input_port_adds_duty_port() -> None:
    code = generate("pwm", {"duty_input": "port"}).code
    assert "duty," in code
    assert "assign pwm_out = cnt < duty;" in code


def test_duty_input_param_no_duty_port_but_has_duty_param() -> None:
    code = generate("pwm", {"duty_input": "param"}).code
    assert "DUTY" in code
    assert "assign pwm_out = cnt < DUTY;" in code
    # no runtime duty port declared
    assert " duty," not in code and " duty;" not in code and " duty)" not in code


def test_invert_output_negates_comparison() -> None:
    normal = generate("pwm", {"invert_output": False}).code
    inverted = generate("pwm", {"invert_output": True}).code
    assert "assign pwm_out = cnt < duty;" in normal
    assert "assign pwm_out = !(cnt < duty);" in inverted


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "pwm",
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
    opts = {"resolution": 10, "duty_input": "param", "invert_output": True}
    a = generate("pwm", opts)
    b = generate("pwm", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('pwm', {'resolution':10,'invert_output':True});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("pwm", {"resolution": 8}).config_hash
    b = generate("pwm", {"resolution": 9}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("pwm", {"resolution": 10, "invert_output": True}).config_hash
    b = generate("pwm", {"invert_output": True, "resolution": 10}).config_hash
    assert a == b


def test_config_hash_function_matches_entry_point() -> None:
    opts = PwmOptions(resolution=10)
    expected = config_hash("pwm", opts.model_dump(mode="json"))
    assert generate("pwm", {"resolution": 10}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_resolution_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("pwm", {"resolution": 3})
    with pytest.raises(ValidationError):
        generate("pwm", {"resolution": 17})


def test_bad_duty_input_enum_raises() -> None:
    with pytest.raises(ValidationError):
        generate("pwm", {"duty_input": "sideways"})


def test_bad_bool_raises() -> None:
    with pytest.raises(ValidationError):
        generate("pwm", {"invert_output": "maybe"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("pwm", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("pwm", {"resolution": 10}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 4  # clk, rst, duty, cnt, pwm_out
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "cnt", "pwm_out"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any("duty=0" in limit for limit in exp.limitations)


def test_explanation_reflects_reset_choice() -> None:
    exp = generate("pwm", {"reset_style": "async", "reset_polarity": "active_high"}).explanation
    assert "asynchronously" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


def test_explanation_reflects_duty_input() -> None:
    port = generate("pwm", {"duty_input": "port"}).explanation
    param = generate("pwm", {"duty_input": "param"}).explanation
    assert "runtime input" in port.purpose
    assert "fixed parameter" in param.purpose
    assert any(s.name == "duty" for s in port.signals)
    assert not any(s.name == "duty" for s in param.signals)


def test_explanation_reflects_invert() -> None:
    normal = generate("pwm", {"invert_output": False}).explanation
    inverted = generate("pwm", {"invert_output": True}).explanation
    assert "active-high" in normal.purpose
    assert "inverted" in inverted.purpose


# --------------------------------------------------------------------------- #
# port_groups shape
# --------------------------------------------------------------------------- #


def test_port_groups_shape_port_duty() -> None:
    groups = port_groups(PwmOptions(duty_input="port"))
    assert all(isinstance(g, PortGroup) for g in groups)
    names = [g.name for g in groups]
    assert names == ["Clocking", "Data"]
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "duty", "pwm_out"}
    for g in groups:
        assert g.description.strip()
        assert g.ports


def test_port_groups_shape_param_duty() -> None:
    groups = port_groups(PwmOptions(duty_input="param"))
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "pwm_out"}


def test_port_groups_reset_name_tracks_polarity() -> None:
    low = port_groups(PwmOptions(reset_polarity="active_low"))
    high = port_groups(PwmOptions(reset_polarity="active_high"))
    assert "rst_n" in low[0].ports
    assert "rst" in high[0].ports and "rst_n" not in high[0].ports


def test_port_groups_names_match_explanation_signals() -> None:
    opts = PwmOptions()
    exp_names = {s.name for s in generate("pwm", {}).explanation.signals}
    for group in port_groups(opts):
        for port_name in group.ports:
            assert port_name in exp_names, port_name


# --------------------------------------------------------------------------- #
# tb_spec shape (checks are recipes; NOT executed yet — P2-13)
# --------------------------------------------------------------------------- #


def test_tb_spec_shape_port() -> None:
    spec = tb_spec(PwmOptions(duty_input="port"))
    assert isinstance(spec, TbSpec)
    assert spec.clock == "clk"
    assert spec.reset == "rst"
    assert spec.reset_cycles == 2
    assert len(spec.vectors) == 5
    assert all(set(v) == {"duty"} for v in spec.vectors)
    assert len(spec.checks) == 2
    assert all(isinstance(c, Check) for c in spec.checks)


def test_tb_spec_shape_param() -> None:
    spec = tb_spec(PwmOptions(duty_input="param"))
    assert all(set(v) == set() for v in spec.vectors)
    assert len(spec.checks) == 2


def test_tb_spec_invert_flips_checks() -> None:
    normal = tb_spec(PwmOptions(invert_output=False))
    inverted = tb_spec(PwmOptions(invert_output=True))
    for c1, c2 in zip(normal.checks, inverted.checks, strict=True):
        assert c1.expected != c2.expected


def test_tb_spec_signals_reference_real_ports() -> None:
    spec = tb_spec(PwmOptions(duty_input="port"))
    code = generate("pwm", {"duty_input": "port"}).code
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
    schema = registry.get("pwm").options_model.model_json_schema()
    props = schema["properties"]
    assert props["resolution"]["description"]
    assert props["duty_input"]["description"]
    assert props["invert_output"]["description"]
    assert set(props["duty_input"]["enum"]) == {"port", "param"}


def test_generated_ir_is_valid() -> None:
    for opts in (
        PwmOptions(),
        PwmOptions(resolution=16, duty_input="param", invert_output=True),
        PwmOptions(reset_style="async", reset_polarity="active_high"),
    ):
        code = render(build_ir(opts), language="sv")
        assert "endmodule" in code
