"""LFSR module: generation, options, determinism, explanation, port_groups/
tb_spec shape (mirrors test_pwm.py / test_edge_detector.py).
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from pydantic import ValidationError
from semicraft_core import config_hash, generate
from semicraft_core.generate import generate_files
from semicraft_core.ir import validate
from semicraft_core.modules.contract import Check, PortGroup, TbSpec
from semicraft_core.modules.lfsr import LfsrOptions, port_groups, tb_spec
from semicraft_core.modules.lfsr import generate as build_ir
from semicraft_core.render import render
from semicraft_core.snippets import registry

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("lfsr", {"language": language})
    assert result.code
    validate(build_ir(LfsrOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"lfsr.{ext}"


def test_default_sv_shape() -> None:
    code = generate("lfsr", {}).code
    assert "module lfsr #(" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "q <=" in code
    assert "endmodule" in code


def test_verilog_infers_reg_and_plain_always() -> None:
    code = generate("lfsr", {"language": "verilog"}).code
    assert "always @(posedge clk) begin" in code
    assert "reg " in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("width", [4, 8, 16, 24, 32])
def test_each_width_generates_and_validates(width: int) -> None:
    code = render(build_ir(LfsrOptions(width=width)), language="sv")
    assert f"WIDTH = {width}" in code
    validate(build_ir(LfsrOptions(width=width)))


def test_width_4_tap_xor_expression() -> None:
    """width=4 taps are (4, 3) -> indices 3, 2 (1-indexed from LSB)."""
    code = generate("lfsr", {"width": 4}).code
    assert "q[3] ^ q[2]" in code


def test_width_8_default_tap_xor_expression() -> None:
    """Default width=8 taps are (8, 6, 5, 4) -> indices 7, 5, 4, 3."""
    code = generate("lfsr", {}).code
    assert "q[7] ^ q[5]" in code and "q[4]" in code and "q[3]" in code


def test_bad_width_raises() -> None:
    with pytest.raises(ValidationError):
        generate("lfsr", {"width": 12})  # not one of the Literal choices


def test_init_value_zero_raises() -> None:
    with pytest.raises(ValidationError):
        generate("lfsr", {"init_value": 0})


def test_init_value_at_or_above_max_raises() -> None:
    with pytest.raises(ValidationError):
        generate("lfsr", {"width": 4, "init_value": 16})  # == 2**4
    with pytest.raises(ValidationError):
        generate("lfsr", {"width": 4, "init_value": 17})


def test_init_value_valid_range_ok() -> None:
    code = generate("lfsr", {"width": 4, "init_value": 15}).code
    assert "INIT = 4'd15" in code or "INIT" in code


def test_enable_true_adds_en_port_and_gates_shift() -> None:
    code = generate("lfsr", {"enable": True}).code
    assert "en," in code or "en)" in code
    assert "if (en) begin" in code


def test_enable_false_removes_en_port() -> None:
    code = generate("lfsr", {"enable": False}).code
    assert " en," not in code and " en;" not in code and " en)" not in code
    assert "if (en)" not in code


def test_output_style_serial_removes_parallel_q_port() -> None:
    parallel_code = generate("lfsr", {"output_style": "parallel"}).code
    serial_code = generate("lfsr", {"output_style": "serial"}).code
    assert "output" in parallel_code
    # parallel style declares q as a port
    assert "] q" in parallel_code
    # serial style has an 'out' output port and no parallel q port declaration
    assert "output logic out" in serial_code
    assert "output logic [WIDTH-1:0] q" not in serial_code


def test_output_style_serial_out_is_feedback_expression() -> None:
    code = generate("lfsr", {"output_style": "serial", "width": 4}).code
    assert "assign out = q[3] ^ q[2];" in code


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "lfsr",
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
    # reset always loads INIT, never a bare zero constant for q
    assert "q <= INIT;" in code


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"width": 16, "init_value": 5, "output_style": "serial"}
    a = generate("lfsr", opts)
    b = generate("lfsr", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('lfsr', {'width':16,'init_value':5});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("lfsr", {"width": 8}).config_hash
    b = generate("lfsr", {"width": 16}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("lfsr", {"width": 16, "init_value": 5}).config_hash
    b = generate("lfsr", {"init_value": 5, "width": 16}).config_hash
    assert a == b


def test_config_hash_function_matches_entry_point() -> None:
    opts = LfsrOptions(width=16)
    expected = config_hash("lfsr", opts.model_dump(mode="json"))
    assert generate("lfsr", {"width": 16}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_bad_output_style_enum_raises() -> None:
    with pytest.raises(ValidationError):
        generate("lfsr", {"output_style": "sideways"})


def test_bad_bool_raises() -> None:
    with pytest.raises(ValidationError):
        generate("lfsr", {"enable": "maybe"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("lfsr", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("lfsr", {"width": 16}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 3  # clk, rst, q (at least)
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "q"}
    assert exp.reset_behavior.strip()
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)


def test_explanation_mentions_non_cryptographic_limitation() -> None:
    exp = generate("lfsr", {}).explanation
    joined = " ".join(exp.limitations).lower()
    assert "cryptographic" in joined


def test_explanation_mentions_period_and_lockup() -> None:
    exp = generate("lfsr", {"width": 8}).explanation
    joined = " ".join(exp.limitations).lower()
    assert "255" in joined or "period" in joined
    assert "lockup" in joined or "zero" in joined


def test_explanation_reflects_reset_choice() -> None:
    exp = generate("lfsr", {"reset_style": "async", "reset_polarity": "active_high"}).explanation
    assert "asynchronously" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


def test_explanation_reflects_enable() -> None:
    on = generate("lfsr", {"enable": True}).explanation
    off = generate("lfsr", {"enable": False}).explanation
    assert on.enable_behavior is not None
    assert off.enable_behavior is None
    assert any(s.name == "en" for s in on.signals)
    assert not any(s.name == "en" for s in off.signals)


def test_explanation_reflects_output_style() -> None:
    parallel = generate("lfsr", {"output_style": "parallel"}).explanation
    serial = generate("lfsr", {"output_style": "serial"}).explanation
    assert any(s.name == "q" and s.direction == "output" for s in parallel.signals)
    assert any(s.name == "out" and s.direction == "output" for s in serial.signals)
    assert any(s.name == "q" and s.direction == "internal" for s in serial.signals)


# --------------------------------------------------------------------------- #
# port_groups shape
# --------------------------------------------------------------------------- #


def test_port_groups_shape_parallel() -> None:
    groups = port_groups(LfsrOptions(output_style="parallel"))
    assert all(isinstance(g, PortGroup) for g in groups)
    names = [g.name for g in groups]
    assert names == ["Clocking", "Data"]
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "en", "q"}
    for g in groups:
        assert g.description.strip()
        assert g.ports


def test_port_groups_shape_serial_no_enable() -> None:
    groups = port_groups(LfsrOptions(output_style="serial", enable=False))
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "out"}


def test_port_groups_names_match_explanation_signals() -> None:
    opts = LfsrOptions()
    exp_names = {s.name for s in generate("lfsr", {}).explanation.signals}
    for group in port_groups(opts):
        for port_name in group.ports:
            assert port_name in exp_names, port_name


# --------------------------------------------------------------------------- #
# tb_spec shape (checks are recipes; NOT executed yet — P2-13)
# --------------------------------------------------------------------------- #


def test_tb_spec_shape_default() -> None:
    spec = tb_spec(LfsrOptions())
    assert isinstance(spec, TbSpec)
    assert spec.clock == "clk"
    assert spec.reset == "rst"
    assert spec.reset_cycles == 2
    assert len(spec.vectors) == 6
    assert all(set(v) == {"en"} for v in spec.vectors)
    assert len(spec.checks) == 2
    assert all(isinstance(c, Check) for c in spec.checks)


def test_tb_spec_no_enable_empty_vectors() -> None:
    spec = tb_spec(LfsrOptions(enable=False))
    assert all(set(v) == set() for v in spec.vectors)
    assert len(spec.checks) == 2


def test_tb_spec_signal_matches_output_style() -> None:
    parallel = tb_spec(LfsrOptions(output_style="parallel"))
    serial = tb_spec(LfsrOptions(output_style="serial"))
    assert {c.signal for c in parallel.checks} == {"q"}
    assert {c.signal for c in serial.checks} == {"out"}


def test_tb_spec_first_check_is_seed_value() -> None:
    spec = tb_spec(LfsrOptions(width=8, init_value=5))
    first = next(c for c in spec.checks if c.cycle == 0)
    assert first.expected == 5


def test_tb_spec_signals_reference_real_ports() -> None:
    spec = tb_spec(LfsrOptions())
    code = generate("lfsr", {}).code
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
    schema = registry.get("lfsr").options_model.model_json_schema()
    props = schema["properties"]
    assert props["width"]["description"]
    assert props["init_value"]["description"]
    assert props["enable"]["description"]
    assert props["output_style"]["description"]
    assert set(props["output_style"]["enum"]) == {"parallel", "serial"}


def test_generated_ir_is_valid() -> None:
    for opts in (
        LfsrOptions(),
        LfsrOptions(width=32, output_style="serial", enable=False),
        LfsrOptions(reset_style="async", reset_polarity="active_high"),
    ):
        code = render(build_ir(opts), language="sv")
        assert "endmodule" in code


# --------------------------------------------------------------------------- #
# generate_files: rtl + doc
# --------------------------------------------------------------------------- #


def test_generate_files_yields_rtl_and_doc() -> None:
    res = generate_files("lfsr", {})
    kinds = {f.kind for f in res.files}
    assert "rtl" in kinds
    assert "doc" in kinds
