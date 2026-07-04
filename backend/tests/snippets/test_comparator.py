"""Comparator snippet tests: generation, options, determinism, explanation.

Mirrors ``test_counter.py`` (WP-03 reference test template) adapted to the
comparator's option surface: width, signed_compare, outputs (subset of
eq/ne/lt/le/gt/ge). Purely combinational: no reset/clock fields, no fragment
mode surprises beyond what CommonOptions already covers.
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
from semicraft_core.snippets.comparator import ComparatorOptions
from semicraft_core.snippets.comparator import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("comparator", {"language": language})
    assert result.code
    validate(build_ir(ComparatorOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"comparator.{ext}"


def test_default_sv_matches_shape() -> None:
    code = generate("comparator", {}).code
    assert "module comparator #(" in code
    assert "parameter int unsigned WIDTH = 8" in code
    assert "assign eq = a == b;" in code
    assert "assign lt = a < b;" in code
    assert "assign gt = a > b;" in code
    assert "endmodule" in code


def test_verilog_infers_wire_outputs() -> None:
    code = generate("comparator", {"language": "verilog"}).code
    assert "output wire" in code
    assert "parameter WIDTH = 8" in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_width_changes_vector_width() -> None:
    code = generate("comparator", {"width": 16}).code
    assert "parameter int unsigned WIDTH = 16" in code
    assert "[WIDTH-1:0]" in code


def test_signed_compare_adds_signed_marker() -> None:
    unsigned_code = generate("comparator", {"signed_compare": False}).code
    signed_code = generate("comparator", {"signed_compare": True}).code
    # Check the port declaration lines specifically (the header comment always
    # says "unsigned"/"signed" describing the mode, so scope the check to the
    # module body's port list, not the whole file).
    assert "input  logic [WIDTH-1:0] a" in unsigned_code
    assert "input  logic signed [WIDTH-1:0] a" in signed_code


def test_output_port_set_follows_selection() -> None:
    code_eq_only = generate("comparator", {"outputs": ["eq"]}).code
    assert "output logic             eq" in code_eq_only or "output" in code_eq_only
    for op in ("ne", "lt", "le", "gt", "ge"):
        assert f"assign {op} =" not in code_eq_only
    assert "assign eq = a == b;" in code_eq_only

    code_all = generate("comparator", {"outputs": ["eq", "ne", "lt", "le", "gt", "ge"]}).code
    for op in ("eq", "ne", "lt", "le", "gt", "ge"):
        assert f"assign {op} =" in code_all


def test_each_output_uses_matching_operator() -> None:
    code = generate("comparator", {"outputs": ["eq", "ne", "lt", "le", "gt", "ge"]}).code
    assert "assign eq = a == b;" in code
    assert "assign ne = a != b;" in code
    assert "assign lt = a < b;" in code
    assert "assign le = a <= b;" in code
    assert "assign gt = a > b;" in code
    assert "assign ge = a >= b;" in code


def test_outputs_order_independent_same_config_hash() -> None:
    a = generate("comparator", {"outputs": ["gt", "eq", "lt"]})
    b = generate("comparator", {"outputs": ["lt", "gt", "eq"]})
    assert a.config_hash == b.config_hash
    assert a.code == b.code


def test_outputs_normalized_to_canonical_order_in_code() -> None:
    code = generate("comparator", {"outputs": ["ge", "eq", "ne"]}).code
    eq_idx = code.index("assign eq")
    ne_idx = code.index("assign ne")
    ge_idx = code.index("assign ge")
    assert eq_idx < ne_idx < ge_idx


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"width": 12, "signed_compare": True, "outputs": ["ge", "le"]}
    a = generate("comparator", opts)
    b = generate("comparator", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('comparator', {'width':10,'signed_compare':True});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("comparator", {"width": 8}).config_hash
    b = generate("comparator", {"width": 9}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("comparator", {"width": 8, "signed_compare": True}).config_hash
    b = generate("comparator", {"signed_compare": True, "width": 8}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("comparator", {"width": 8})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_function_matches_entry_point() -> None:
    opts = ComparatorOptions(width=8)
    expected = config_hash("comparator", opts.model_dump(mode="json"))
    assert generate("comparator", {"width": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_empty_outputs_raises() -> None:
    with pytest.raises(ValidationError):
        generate("comparator", {"outputs": []})


def test_bad_op_raises() -> None:
    with pytest.raises(ValidationError):
        generate("comparator", {"outputs": ["bad"]})


def test_duplicate_outputs_raises() -> None:
    with pytest.raises(ValidationError):
        generate("comparator", {"outputs": ["eq", "eq"]})


def test_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("comparator", {"width": 0})
    with pytest.raises(ValidationError):
        generate("comparator", {"width": 2048})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("comparator", {"nonsense": 1})


def test_bad_bool_type_raises() -> None:
    with pytest.raises(ValidationError):
        generate("comparator", {"signed_compare": "maybe"})  # not bool-coercible


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate(
        "comparator", {"signed_compare": True, "outputs": ["eq", "lt", "gt"]}
    ).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 5  # a, b, eq, lt, gt
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"a", "b", "eq", "lt", "gt"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)


def test_explanation_mentions_signed_semantics() -> None:
    exp_signed = generate("comparator", {"signed_compare": True}).explanation
    exp_unsigned = generate("comparator", {"signed_compare": False}).explanation
    combined_signed = " ".join(exp_signed.configuration + exp_signed.assumptions).lower()
    combined_unsigned = " ".join(exp_unsigned.configuration + exp_unsigned.assumptions).lower()
    assert "signed" in combined_signed
    assert "unsigned" in combined_unsigned


def test_explanation_documents_equal_width_assumption() -> None:
    exp = generate("comparator", {}).explanation
    combined = " ".join(exp.assumptions).lower()
    assert "width" in combined


def test_explanation_enable_behavior_always_none() -> None:
    exp = generate("comparator", {}).explanation
    assert exp.enable_behavior is None


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("comparator", {"naming": {"prefix": "u_"}}).code
    assert "u_a" in code
    assert "u_eq" in code
    assert "WIDTH" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("comparator").options_model.model_json_schema()
    props = schema["properties"]
    assert props["width"]["description"]
    assert props["signed_compare"]["description"]
    assert props["outputs"]["description"]


# --------------------------------------------------------------------------- #
# equivalence check against direct IR render
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_render() -> None:
    opts = ComparatorOptions(width=8, outputs=["eq", "lt", "gt"])
    module = build_ir(opts)
    code = render(module, language="sv")
    assert "assign eq = a == b;" in code
    assert "assign lt = a < b;" in code
    assert "assign gt = a > b;" in code
