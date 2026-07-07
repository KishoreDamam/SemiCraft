"""Edge-detector module: generation, options, determinism, explanation,
port_groups/tb_spec shape (mirrors the counter snippet test suite).
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from pydantic import ValidationError
from semicraft_core import config_hash, generate
from semicraft_core.ir import validate
from semicraft_core.modules.contract import Check, PortGroup, TbSpec
from semicraft_core.modules.edge_detector import EdgeDetectorOptions, port_groups, tb_spec
from semicraft_core.modules.edge_detector import generate as build_ir
from semicraft_core.render import render
from semicraft_core.snippets import registry

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("edge-detector", {"language": language})
    assert result.code
    validate(build_ir(EdgeDetectorOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"edge_detector.{ext}"


def test_default_sv_shape() -> None:
    code = generate("edge-detector", {}).code
    assert "module edge_detector (" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "d_q <= d;" in code
    assert "pulse <= d & (~d_q);" in code  # registered rising edge
    assert "endmodule" in code


def test_verilog_infers_reg_and_plain_always() -> None:
    code = generate("edge-detector", {"language": "verilog"}).code
    assert "always @(posedge clk) begin" in code
    assert "reg " in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_detect_rising_expression() -> None:
    code = generate("edge-detector", {"detect": "rising"}).code
    assert "d & (~d_q)" in code


def test_detect_falling_expression() -> None:
    code = generate("edge-detector", {"detect": "falling"}).code
    assert "(~d) & d_q" in code


def test_detect_both_uses_xor() -> None:
    code = generate("edge-detector", {"detect": "both"}).code
    assert "d ^ d_q" in code


def test_width_adds_parameter_and_vector() -> None:
    code = generate("edge-detector", {"width": 8}).code
    assert "WIDTH = 8" in code
    assert "[WIDTH-1:0]" in code


def test_width_one_has_no_parameter() -> None:
    code = generate("edge-detector", {"width": 1}).code
    assert "WIDTH" not in code
    assert "[WIDTH-1:0]" not in code


def test_registered_output_structural_change() -> None:
    """registered_output flips pulse between a flop (in the process) and a
    continuous assignment (ContAssign)."""
    reg = generate("edge-detector", {"registered_output": True}).code
    comb = generate("edge-detector", {"registered_output": False}).code

    # Registered: pulse is assigned inside the clocked process, no continuous assign.
    assert "pulse <= d & (~d_q);" in reg
    assert "assign pulse" not in reg
    # Combinational: pulse is a continuous assignment, not a clocked assignment.
    assert "assign pulse = d & (~d_q);" in comb
    assert "pulse <=" not in comb


def test_registered_output_reset_clears_pulse() -> None:
    reg = generate("edge-detector", {"registered_output": True}).code
    comb = generate("edge-detector", {"registered_output": False}).code
    # The pulse register is reset only when registered.
    assert "pulse <= 1'b0;" in reg
    assert "pulse <= 1'b0;" not in comb


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "edge-detector",
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
    opts = {"detect": "both", "width": 4, "registered_output": False}
    a = generate("edge-detector", opts)
    b = generate("edge-detector", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('edge-detector', {'detect':'falling','width':3});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("edge-detector", {"detect": "rising"}).config_hash
    b = generate("edge-detector", {"detect": "falling"}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("edge-detector", {"detect": "both", "width": 4}).config_hash
    b = generate("edge-detector", {"width": 4, "detect": "both"}).config_hash
    assert a == b


def test_config_hash_function_matches_entry_point() -> None:
    opts = EdgeDetectorOptions(width=8)
    expected = config_hash("edge-detector", opts.model_dump(mode="json"))
    assert generate("edge-detector", {"width": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("edge-detector", {"width": 0})
    with pytest.raises(ValidationError):
        generate("edge-detector", {"width": 65})


def test_bad_detect_enum_raises() -> None:
    with pytest.raises(ValidationError):
        generate("edge-detector", {"detect": "sideways"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("edge-detector", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("edge-detector", {"detect": "both", "width": 4}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 4
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 4  # clk, rst, d, d_q, pulse
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "d", "d_q", "pulse"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any("CDC" in limit or "clock-domain" in limit for limit in exp.limitations)


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "edge-detector", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronous" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


def test_explanation_reflects_registered_vs_combinational() -> None:
    reg = generate("edge-detector", {"registered_output": True}).explanation
    comb = generate("edge-detector", {"registered_output": False}).explanation
    assert "one cycle after" in reg.purpose
    assert "same cycle" in comb.purpose


# --------------------------------------------------------------------------- #
# port_groups shape
# --------------------------------------------------------------------------- #


def test_port_groups_shape() -> None:
    groups = port_groups(EdgeDetectorOptions())
    assert all(isinstance(g, PortGroup) for g in groups)
    names = [g.name for g in groups]
    assert names == ["Clocking", "Data"]
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "d", "pulse"}
    for g in groups:
        assert g.description.strip()
        assert g.ports


def test_port_groups_reset_name_tracks_polarity() -> None:
    low = port_groups(EdgeDetectorOptions(reset_polarity="active_low"))
    high = port_groups(EdgeDetectorOptions(reset_polarity="active_high"))
    assert "rst_n" in low[0].ports
    assert "rst" in high[0].ports and "rst_n" not in high[0].ports


def test_port_groups_names_match_explanation_signals() -> None:
    """Every port named in a group appears as a signal in the explanation, so
    the doc port table joins cleanly."""
    opts = EdgeDetectorOptions()
    exp_names = {s.name for s in generate("edge-detector", {}).explanation.signals}
    for group in port_groups(opts):
        for port_name in group.ports:
            assert port_name in exp_names, port_name


# --------------------------------------------------------------------------- #
# tb_spec shape (checks are recipes; NOT executed yet — P2-13)
# --------------------------------------------------------------------------- #


def test_tb_spec_shape() -> None:
    spec = tb_spec(EdgeDetectorOptions())
    assert isinstance(spec, TbSpec)
    assert spec.clock == "clk"
    assert spec.reset == "rst"
    assert spec.reset_cycles == 2
    assert len(spec.vectors) == 6
    assert all(set(v) == {"d"} for v in spec.vectors)
    assert len(spec.checks) == 2
    assert all(isinstance(c, Check) for c in spec.checks)


def test_tb_spec_registered_latency_shifts_check_cycles() -> None:
    reg = tb_spec(EdgeDetectorOptions(registered_output=True))
    comb = tb_spec(EdgeDetectorOptions(registered_output=False))
    # The rising-edge check happens one cycle later for the registered output.
    reg_rise = next(c for c in reg.checks if c.expected != 0)
    comb_rise = next(c for c in comb.checks if c.expected != 0)
    assert reg_rise.cycle == comb_rise.cycle + 1


def test_tb_spec_both_has_two_positive_checks() -> None:
    spec = tb_spec(EdgeDetectorOptions(detect="both"))
    positive = [c for c in spec.checks if c.expected != 0]
    assert len(positive) == 2  # a rising and a falling check


def test_tb_spec_signals_reference_real_ports() -> None:
    spec = tb_spec(EdgeDetectorOptions())
    code = generate("edge-detector", {}).code
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
    schema = registry.get("edge-detector").options_model.model_json_schema()
    props = schema["properties"]
    assert props["detect"]["description"]
    assert props["width"]["description"]
    assert props["registered_output"]["description"]
    assert set(props["detect"]["enum"]) == {"rising", "falling", "both"}


def test_generated_ir_is_valid() -> None:
    for opts in (
        EdgeDetectorOptions(),
        EdgeDetectorOptions(detect="both", width=8, registered_output=False),
        EdgeDetectorOptions(reset_style="async", reset_polarity="active_high"),
    ):
        code = render(build_ir(opts), language="sv")
        assert "endmodule" in code
