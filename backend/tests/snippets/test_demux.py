"""Demux snippet tests: generation, options, determinism, explanation.

Mirrors ``test_counter.py`` / ``test_register.py`` (WP-03 reference test
template) adapted to the demux's option surface: num_outputs, width. Purely
combinational: no reset/clock fields, no reset-matrix test.
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
from semicraft_core.snippets.demux import DemuxOptions
from semicraft_core.snippets.demux import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("demux", {"language": language})
    assert result.code
    validate(build_ir(DemuxOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"demux.{ext}"


def test_default_sv_matches_shape() -> None:
    code = generate("demux", {}).code
    assert "module demux #(" in code
    assert "parameter int unsigned WIDTH = 8" in code
    assert "localparam int unsigned SEL_WIDTH = 2" in code
    assert "always_comb begin" in code
    assert "case (sel)" in code
    assert "endmodule" in code


def test_verilog_infers_output_reg_and_plain_always() -> None:
    code = generate("demux", {"language": "verilog"}).code
    assert "output reg  [WIDTH-1:0]     out0" in code
    assert "always @(*) begin" in code
    assert "parameter WIDTH = 8" in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_num_outputs_changes_port_list() -> None:
    code4 = generate("demux", {"num_outputs": 4}).code
    code8 = generate("demux", {"num_outputs": 8}).code
    for i in range(4):
        assert f"out{i}" in code4
    assert "out4" not in code4
    for i in range(8):
        assert f"out{i}" in code8


def test_width_changes_ranges() -> None:
    code8 = generate("demux", {"width": 8}).code
    code32 = generate("demux", {"width": 32}).code
    assert "parameter int unsigned WIDTH = 8" in code8
    assert "parameter int unsigned WIDTH = 32" in code32
    assert "[WIDTH-1:0]" in code8
    assert "[WIDTH-1:0]" in code32


def test_sel_width_derived_from_num_outputs() -> None:
    code3 = generate("demux", {"num_outputs": 3}).code  # ceil(log2(3)) = 2
    code5 = generate("demux", {"num_outputs": 5}).code  # ceil(log2(5)) = 3
    code2 = generate("demux", {"num_outputs": 2}).code  # ceil(log2(2)) = 1
    assert "localparam int unsigned SEL_WIDTH = 2" in code3
    assert "localparam int unsigned SEL_WIDTH = 3" in code5
    assert "localparam int unsigned SEL_WIDTH = 1" in code2


def test_defaults_assigned_first_structure() -> None:
    """All outputs must default to zero *before* the routing Case (no latches)."""
    code = generate("demux", {"num_outputs": 4}).code
    zero_idx = code.index("out0 = {WIDTH{1'b0}};")
    case_idx = code.index("case (sel)")
    assert zero_idx < case_idx
    # every output has a zero-default assignment above the case.
    for i in range(4):
        assert code.index(f"out{i} = {{WIDTH{{1'b0}}}};") < case_idx


def test_case_has_explicit_default_arm() -> None:
    """Regression test: a non-enum Case without a default arm fails IR
    validation rule 5. The demux Case must declare an explicit (no-op)
    default even though outputs are already zero-defaulted."""
    code = generate("demux", {}).code
    assert "default: ;" in code or "default:" in code


def test_non_pow2_num_outputs_documented_in_assumptions() -> None:
    exp3 = generate("demux", {"num_outputs": 3}).explanation
    exp4 = generate("demux", {"num_outputs": 4}).explanation
    combined3 = " ".join(exp3.assumptions).lower()
    combined4 = " ".join(exp4.assumptions).lower()
    assert "not a power of two" in combined3
    assert "not a power of two" not in combined4


def test_num_outputs_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("demux", {"num_outputs": 1})  # below ge=2
    with pytest.raises(ValidationError):
        generate("demux", {"num_outputs": 17})  # above le=16


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"num_outputs": 6, "width": 12}
    a = generate("demux", opts)
    b = generate("demux", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('demux', {'num_outputs':6,'width':12});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("demux", {"num_outputs": 4}).config_hash
    b = generate("demux", {"num_outputs": 8}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("demux", {"width": 8, "num_outputs": 4}).config_hash
    b = generate("demux", {"num_outputs": 4, "width": 8}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("demux", {"width": 8})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_function_matches_entry_point() -> None:
    opts = DemuxOptions(num_outputs=4)
    expected = config_hash("demux", opts.model_dump(mode="json"))
    assert generate("demux", {"num_outputs": 4}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("demux", {"width": 0})
    with pytest.raises(ValidationError):
        generate("demux", {"width": 1024})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("demux", {"nonsense": 1})


def test_bad_bool_type_raises() -> None:
    with pytest.raises(ValidationError):
        generate("demux", {"include_wrapper": "maybe"})  # not bool-coercible


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("demux", {"num_outputs": 8}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 4
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 10  # din, sel, 8 outputs
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"din", "sel", "out0", "out7"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None  # no clock/reset/enable concept
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any("CDC" in limit or "clock-domain" in limit for limit in exp.limitations)


def test_reset_behavior_states_no_reset() -> None:
    exp = generate("demux", {}).explanation
    assert "no reset" in exp.reset_behavior.lower() or "combinational" in exp.reset_behavior.lower()


def test_explanation_documents_zeros_only_hold_dropped() -> None:
    """The IMPLEMENTATION_PLAN 'default_value: zeros|hold' option was
    intentionally reduced to zeros-only for the combinational MVP; this must
    be documented, not silently dropped."""
    exp = generate("demux", {}).explanation
    combined = " ".join(exp.assumptions).lower()
    assert "hold" in combined


# --------------------------------------------------------------------------- #
# fragment mode
# --------------------------------------------------------------------------- #


def test_fragment_mode_filename_and_no_wrapper() -> None:
    result = generate("demux", {"include_wrapper": False})
    assert result.filename == "demux_fragment.sv"
    assert "module demux" not in result.code
    assert "endmodule" not in result.code
    assert "Fragment mode" in result.code


def test_fragment_mode_verilog_extension() -> None:
    result = generate("demux", {"include_wrapper": False, "language": "verilog"})
    assert result.filename == "demux_fragment.v"


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("demux", {"naming": {"prefix": "u_"}}).code
    assert "u_din" in code
    assert "u_out0" in code
    assert "WIDTH" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("demux").options_model.model_json_schema()
    props = schema["properties"]
    assert props["num_outputs"]["description"]
    assert props["width"]["description"]


# --------------------------------------------------------------------------- #
# equivalence check against direct IR render
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_render_for_language_pinned_verilog_case() -> None:
    opts = DemuxOptions(num_outputs=4, width=8, language="verilog")
    module = build_ir(opts)
    code = render(module, language="verilog")
    assert "always @(*) begin" in code
    assert "case (sel)" in code
    assert "out0 = din;" in code
    assert "parameter WIDTH = 8" in code
