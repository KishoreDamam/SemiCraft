"""Gray-counter module: generation, options, determinism, explanation,
port_groups/tb_spec shape (mirrors test_pwm.py / test_edge_detector.py).
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
from semicraft_core.modules.gray_counter import GrayCounterOptions, port_groups, tb_spec
from semicraft_core.modules.gray_counter import generate as build_ir
from semicraft_core.render import render
from semicraft_core.snippets import registry

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("gray-counter", {"language": language})
    assert result.code
    validate(build_ir(GrayCounterOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"gray_counter.{ext}"


def test_default_sv_shape() -> None:
    code = generate("gray-counter", {}).code
    assert "module gray_counter #(" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "assign gray = bin ^ (bin >> 1'b1);" in code
    assert "endmodule" in code


def test_verilog_infers_reg_and_plain_always() -> None:
    code = generate("gray-counter", {"language": "verilog"}).code
    assert "always @(posedge clk) begin" in code
    assert "reg " in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_width_changes_param() -> None:
    code = generate("gray-counter", {"width": 12}).code
    assert "WIDTH = 12" in code


def test_gray_expression_present_regardless_of_width() -> None:
    for width in (2, 8, 16, 32):
        code = generate("gray-counter", {"width": width}).code
        assert "assign gray = bin ^ (bin >> 1'b1);" in code


def test_enable_true_adds_en_port_and_gates_count() -> None:
    code = generate("gray-counter", {"enable": True}).code
    assert "en," in code or "en)" in code
    assert "if (en) begin" in code


def test_enable_false_removes_en_port() -> None:
    code = generate("gray-counter", {"enable": False}).code
    assert " en," not in code and " en;" not in code and " en)" not in code
    assert "if (en)" not in code


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "gray-counter",
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
    opts = {"width": 12, "enable": False}
    a = generate("gray-counter", opts)
    b = generate("gray-counter", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('gray-counter', {'width':12});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("gray-counter", {"width": 8}).config_hash
    b = generate("gray-counter", {"width": 9}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("gray-counter", {"width": 12, "enable": False}).config_hash
    b = generate("gray-counter", {"enable": False, "width": 12}).config_hash
    assert a == b


def test_config_hash_function_matches_entry_point() -> None:
    opts = GrayCounterOptions(width=12)
    expected = config_hash("gray-counter", opts.model_dump(mode="json"))
    assert generate("gray-counter", {"width": 12}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("gray-counter", {"width": 1})
    with pytest.raises(ValidationError):
        generate("gray-counter", {"width": 33})


def test_bad_bool_raises() -> None:
    with pytest.raises(ValidationError):
        generate("gray-counter", {"enable": "maybe"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("gray-counter", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("gray-counter", {"width": 12}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 3  # clk, rst, gray (at least)
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "bin", "gray"}
    assert exp.reset_behavior.strip()
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)


def test_explanation_mentions_cdc_synchronizer() -> None:
    exp = generate("gray-counter", {}).explanation
    joined = " ".join(exp.limitations).lower()
    assert "cdc" in joined or "synchroniz" in joined


def test_explanation_mentions_single_bit_transition() -> None:
    exp = generate("gray-counter", {}).explanation
    assert "one bit" in exp.purpose.lower() or "single-bit" in exp.purpose.lower()


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "gray-counter", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronously" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


def test_explanation_reflects_enable() -> None:
    on = generate("gray-counter", {"enable": True}).explanation
    off = generate("gray-counter", {"enable": False}).explanation
    assert on.enable_behavior is not None
    assert off.enable_behavior is None
    assert any(s.name == "en" for s in on.signals)
    assert not any(s.name == "en" for s in off.signals)


# --------------------------------------------------------------------------- #
# port_groups shape
# --------------------------------------------------------------------------- #


def test_port_groups_shape_enabled() -> None:
    groups = port_groups(GrayCounterOptions(enable=True))
    assert all(isinstance(g, PortGroup) for g in groups)
    names = [g.name for g in groups]
    assert names == ["Clocking", "Data"]
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "en", "gray"}
    for g in groups:
        assert g.description.strip()
        assert g.ports


def test_port_groups_shape_no_enable() -> None:
    groups = port_groups(GrayCounterOptions(enable=False))
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "gray"}


def test_port_groups_reset_name_tracks_polarity() -> None:
    low = port_groups(GrayCounterOptions(reset_polarity="active_low"))
    high = port_groups(GrayCounterOptions(reset_polarity="active_high"))
    assert "rst_n" in low[0].ports
    assert "rst" in high[0].ports and "rst_n" not in high[0].ports


def test_port_groups_names_match_explanation_signals() -> None:
    opts = GrayCounterOptions()
    exp_names = {s.name for s in generate("gray-counter", {}).explanation.signals}
    for group in port_groups(opts):
        for port_name in group.ports:
            assert port_name in exp_names, port_name


# --------------------------------------------------------------------------- #
# tb_spec shape (checks are recipes; NOT executed yet — P2-13)
# --------------------------------------------------------------------------- #


def test_tb_spec_shape_enabled() -> None:
    spec = tb_spec(GrayCounterOptions(enable=True))
    assert isinstance(spec, TbSpec)
    assert spec.clock == "clk"
    assert spec.reset == "rst"
    assert spec.reset_cycles == 2
    assert len(spec.vectors) == 6
    assert all(set(v) == {"en"} for v in spec.vectors)
    assert len(spec.checks) == 2
    assert all(isinstance(c, Check) for c in spec.checks)


def test_tb_spec_no_enable_empty_vectors() -> None:
    spec = tb_spec(GrayCounterOptions(enable=False))
    assert all(set(v) == set() for v in spec.vectors)
    assert len(spec.checks) == 2


def test_tb_spec_first_check_is_zero() -> None:
    spec = tb_spec(GrayCounterOptions())
    first = next(c for c in spec.checks if c.cycle == 0)
    assert first.expected == 0  # gray(bin=0) == 0
    assert first.signal == "gray"


def test_tb_spec_hold_check_matches_manual_gray_of_three() -> None:
    """With width=8, enable on: 3 counted cycles then hold -> bin=3, gray=3^1=2."""
    spec = tb_spec(GrayCounterOptions(width=8, enable=True))
    hold_check = next(c for c in spec.checks if c.cycle == 4)
    assert hold_check.expected == (3 ^ (3 >> 1))


def test_tb_spec_signals_reference_real_ports() -> None:
    spec = tb_spec(GrayCounterOptions())
    code = generate("gray-counter", {}).code
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
    schema = registry.get("gray-counter").options_model.model_json_schema()
    props = schema["properties"]
    assert props["width"]["description"]
    assert props["enable"]["description"]


def test_generated_ir_is_valid() -> None:
    for opts in (
        GrayCounterOptions(),
        GrayCounterOptions(width=32, enable=False),
        GrayCounterOptions(reset_style="async", reset_polarity="active_high"),
    ):
        code = render(build_ir(opts), language="sv")
        assert "endmodule" in code


# --------------------------------------------------------------------------- #
# generate_files: rtl + doc
# --------------------------------------------------------------------------- #


def test_generate_files_yields_rtl_and_doc() -> None:
    res = generate_files("gray-counter", {})
    kinds = {f.kind for f in res.files}
    assert "rtl" in kinds
    assert "doc" in kinds
