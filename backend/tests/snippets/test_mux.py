"""Mux snippet tests: generation, options, determinism, explanation.

Mirrors ``test_counter.py`` / ``test_register.py`` (WP-03 reference test
template) adapted to the mux's option surface: num_inputs, width, impl.
Purely combinational: no reset/clock fields, no reset-matrix test.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from pydantic import ValidationError
from semicraft_core import config_hash, generate
from semicraft_core.ir import validate
from semicraft_core.render import render
from semicraft_core.snippets import registry
from semicraft_core.snippets.mux import MuxOptions
from semicraft_core.snippets.mux import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("mux", {"language": language})
    assert result.code
    validate(build_ir(MuxOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"mux.{ext}"


def test_default_sv_matches_shape() -> None:
    code = generate("mux", {}).code
    assert "module mux #(" in code
    assert "parameter int unsigned WIDTH = 8" in code
    assert "localparam int unsigned SEL_WIDTH = 2" in code
    assert "always_comb begin" in code
    assert "case (sel)" in code
    assert "endmodule" in code


def test_verilog_infers_output_reg_and_plain_always() -> None:
    code = generate("mux", {"language": "verilog"}).code
    assert "output reg  [WIDTH-1:0]     out" in code
    assert "always @(*) begin" in code
    assert "parameter WIDTH = 8" in code


def test_ternary_impl_uses_continuous_assign_no_always() -> None:
    code = generate("mux", {"impl": "ternary"}).code
    assert "always_comb" not in code
    assert "assign out =" in code
    assert "?" in code and ":" in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_num_inputs_changes_port_list() -> None:
    code4 = generate("mux", {"num_inputs": 4}).code
    code8 = generate("mux", {"num_inputs": 8}).code
    for i in range(4):
        assert f"in{i}" in code4
    assert "in4" not in code4
    for i in range(8):
        assert f"in{i}" in code8


def test_impl_case_vs_ternary_differ_in_text() -> None:
    case_code = generate("mux", {"impl": "case"}).code
    ternary_code = generate("mux", {"impl": "ternary"}).code
    assert case_code != ternary_code
    assert "case (sel)" in case_code
    assert "case (sel)" not in ternary_code


def test_width_changes_ranges() -> None:
    code8 = generate("mux", {"width": 8}).code
    code32 = generate("mux", {"width": 32}).code
    assert "parameter int unsigned WIDTH = 8" in code8
    assert "parameter int unsigned WIDTH = 32" in code32
    assert "[WIDTH-1:0]" in code8
    assert "[WIDTH-1:0]" in code32


def test_sel_width_derived_from_num_inputs() -> None:
    code3 = generate("mux", {"num_inputs": 3}).code  # ceil(log2(3)) = 2
    code5 = generate("mux", {"num_inputs": 5}).code  # ceil(log2(5)) = 3
    code2 = generate("mux", {"num_inputs": 2}).code  # ceil(log2(2)) = 1
    assert "localparam int unsigned SEL_WIDTH = 2" in code3
    assert "localparam int unsigned SEL_WIDTH = 3" in code5
    assert "localparam int unsigned SEL_WIDTH = 1" in code2


def test_non_pow2_num_inputs_documented_in_assumptions() -> None:
    exp3 = generate("mux", {"num_inputs": 3}).explanation
    exp4 = generate("mux", {"num_inputs": 4}).explanation
    combined3 = " ".join(exp3.assumptions).lower()
    combined4 = " ".join(exp4.assumptions).lower()
    assert "power of two" in combined3
    assert "not a power of two" in combined3
    # power-of-two case should not claim it's non-power-of-two.
    assert "not a power of two" not in combined4


def test_non_pow2_num_inputs_renders_default_arm_fallback() -> None:
    """num_inputs=3: sel can be 0,1,2,3 (2-bit) but only 0-2 map to inputs;
    the default/fallback arm (in0) must still be present and cover code 3."""
    code = generate("mux", {"num_inputs": 3, "impl": "case"}).code
    assert "default: out = in0;" in code


def test_num_inputs_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("mux", {"num_inputs": 1})  # below ge=2
    with pytest.raises(ValidationError):
        generate("mux", {"num_inputs": 17})  # above le=16


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"num_inputs": 6, "width": 12, "impl": "ternary"}
    a = generate("mux", opts)
    b = generate("mux", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('mux', {'num_inputs':6,'impl':'ternary'});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("mux", {"num_inputs": 4}).config_hash
    b = generate("mux", {"num_inputs": 8}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("mux", {"width": 8, "num_inputs": 4}).config_hash
    b = generate("mux", {"num_inputs": 4, "width": 8}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("mux", {"width": 8})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_function_matches_entry_point() -> None:
    opts = MuxOptions(num_inputs=4)
    expected = config_hash("mux", opts.model_dump(mode="json"))
    assert generate("mux", {"num_inputs": 4}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_bad_enum_value_raises() -> None:
    with pytest.raises(ValidationError):
        generate("mux", {"impl": "priority"})


def test_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("mux", {"width": 0})
    with pytest.raises(ValidationError):
        generate("mux", {"width": 1024})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("mux", {"nonsense": 1})


def test_bad_bool_type_raises() -> None:
    with pytest.raises(ValidationError):
        generate("mux", {"include_wrapper": "maybe"})  # not bool-coercible


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("mux", {"num_inputs": 8, "impl": "ternary"}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 4
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 10  # 8 inputs + sel + out
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"in0", "in7", "sel", "out"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None  # no clock/reset/enable concept
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any("CDC" in limit or "clock-domain" in limit for limit in exp.limitations)


def test_reset_behavior_states_combinational() -> None:
    exp = generate("mux", {}).explanation
    assert "combinational" in exp.reset_behavior.lower()


# --------------------------------------------------------------------------- #
# fragment mode
# --------------------------------------------------------------------------- #


def test_fragment_mode_filename_and_no_wrapper() -> None:
    result = generate("mux", {"include_wrapper": False})
    assert result.filename == "mux_fragment.sv"
    assert "module mux" not in result.code
    assert "endmodule" not in result.code
    assert "Fragment mode" in result.code


def test_fragment_mode_verilog_extension() -> None:
    result = generate("mux", {"include_wrapper": False, "language": "verilog"})
    assert result.filename == "mux_fragment.v"


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("mux", {"naming": {"prefix": "u_"}}).code
    assert "u_in0" in code
    assert "u_out" in code
    assert "WIDTH" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("mux").options_model.model_json_schema()
    props = schema["properties"]
    assert props["num_inputs"]["description"]
    assert props["width"]["description"]
    assert props["impl"]["description"]
    assert set(props["impl"]["enum"]) == {"case", "ternary"}


# --------------------------------------------------------------------------- #
# equivalence check against direct IR render
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_render_for_language_pinned_verilog_case() -> None:
    opts = MuxOptions(num_inputs=4, width=8, impl="case", language="verilog")
    module = build_ir(opts)
    code = render(module, language="verilog")
    assert "always @(*) begin" in code
    assert "case (sel)" in code
    assert "out = in0;" in code
    assert "parameter WIDTH = 8" in code
