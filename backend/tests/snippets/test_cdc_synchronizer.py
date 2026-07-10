"""CDC synchronizer snippet tests: generation, options, determinism, explanation.

Mirrors ``test_counter.py`` (WP-03 reference test template) adapted to the
cdc-synchronizer's option surface: stages, width, use_reset (with reset_style/
reset_polarity conditional on use_reset).
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
from semicraft_core.snippets.cdc_synchronizer import CdcSynchronizerOptions
from semicraft_core.snippets.cdc_synchronizer import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("cdc-synchronizer", {"language": language})
    assert result.code
    validate(build_ir(CdcSynchronizerOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"cdc_synchronizer.{ext}"


def test_default_sv_matches_shape() -> None:
    code = generate("cdc-synchronizer", {}).code
    assert "module cdc_synchronizer (" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "sync_ff1 <= d_async;" in code
    assert "q <= sync_ff1;" in code
    assert "endmodule" in code
    # default has no reset at all
    assert "rst" not in code


def test_verilog_infers_reg_output() -> None:
    code = generate("cdc-synchronizer", {"language": "verilog"}).code
    assert "output reg" in code
    assert "always @(posedge clk) begin" in code


# --------------------------------------------------------------------------- #
# option effects: stages
# --------------------------------------------------------------------------- #


def test_stages_changes_chain_length() -> None:
    two = generate("cdc-synchronizer", {"stages": 2}).code
    three = generate("cdc-synchronizer", {"stages": 3}).code
    four = generate("cdc-synchronizer", {"stages": 4}).code
    assert "sync_ff1" in two and "sync_ff2" not in two
    assert "sync_ff2" in three and "sync_ff3" not in three
    assert "sync_ff3" in four
    assert "sync_ff4" not in four  # stages=4 has 4 total registers: ff1..ff3 + q


def test_stages_latency_chain_is_sequential() -> None:
    code = generate("cdc-synchronizer", {"stages": 3}).code
    assert "sync_ff1 <= d_async;" in code
    assert "sync_ff2 <= sync_ff1;" in code
    assert "q <= sync_ff2;" in code


def test_stages_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("cdc-synchronizer", {"stages": 1})
    with pytest.raises(ValidationError):
        generate("cdc-synchronizer", {"stages": 5})


# --------------------------------------------------------------------------- #
# option effects: width
# --------------------------------------------------------------------------- #


def test_width_1_is_scalar() -> None:
    code = generate("cdc-synchronizer", {"width": 1}).code
    assert "[WIDTH-1:0]" not in code
    # No parameters at width 1: the chain is structurally unrolled and stage
    # count is not emitted as a param (Verilator UNUSEDPARAM).
    assert "parameter" not in code


def test_width_gt1_adds_param_and_vector_ports() -> None:
    code = generate("cdc-synchronizer", {"width": 2}).code
    assert "parameter int unsigned WIDTH = 2" in code
    assert "[WIDTH-1:0]" in code


def test_width_gt1_warns_in_assumptions_and_code_comment() -> None:
    exp = generate("cdc-synchronizer", {"width": 2}).explanation
    combined = " ".join(exp.assumptions).lower()
    assert "gray" in combined or "quasi-static" in combined
    assert "multi-bit" in combined or "independent" in combined

    code = generate("cdc-synchronizer", {"width": 2}).code
    assert "gray" in code.lower() or "quasi-static" in code.lower()


def test_width_1_has_no_multibit_warning() -> None:
    exp = generate("cdc-synchronizer", {"width": 1}).explanation
    combined = " ".join(exp.assumptions).lower()
    assert "width > 1" not in combined


def test_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("cdc-synchronizer", {"width": 0})
    with pytest.raises(ValidationError):
        generate("cdc-synchronizer", {"width": 9})


# --------------------------------------------------------------------------- #
# option effects: use_reset
# --------------------------------------------------------------------------- #


def test_use_reset_false_has_no_reset_port_or_logic() -> None:
    code = generate("cdc-synchronizer", {"use_reset": False}).code
    assert "rst" not in code
    assert "always_ff @(posedge clk) begin" in code


def test_use_reset_true_adds_reset_port_and_logic() -> None:
    code = generate("cdc-synchronizer", {"use_reset": True}).code
    assert "rst" in code
    assert "if (" in code


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_use_reset_true_all_style_polarity_combos(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "cdc-synchronizer",
        {"use_reset": True, "reset_style": reset_style, "reset_polarity": reset_polarity},
    ).code
    if reset_polarity == "active_low":
        assert "rst_n" in code
        assert "if (!rst_n)" in code
    else:
        assert "if (rst)" in code
    if reset_style == "async":
        assert " or " in code
    else:
        assert "always_ff @(posedge clk) begin" in code


def test_reset_style_polarity_ignored_when_use_reset_false() -> None:
    # reset_style/reset_polarity are still part of the validated options (and
    # therefore the config hash), but they must have zero effect on the
    # generated RTL body: no reset port, no reset logic, regardless of value.
    a = generate(
        "cdc-synchronizer",
        {"use_reset": False, "reset_style": "sync", "reset_polarity": "active_low"},
    ).code
    b = generate(
        "cdc-synchronizer",
        {"use_reset": False, "reset_style": "async", "reset_polarity": "active_high"},
    ).code
    a_body = a.split("module cdc_synchronizer", 1)[-1]
    b_body = b.split("module cdc_synchronizer", 1)[-1]
    assert a_body == b_body
    assert "rst" not in a_body


def test_explanation_documents_no_reset_when_use_reset_false() -> None:
    exp = generate("cdc-synchronizer", {"use_reset": False}).explanation
    assert "no reset" in exp.reset_behavior.lower() or "not" in exp.reset_behavior.lower()


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"stages": 3, "width": 2, "use_reset": True}
    a = generate("cdc-synchronizer", opts)
    b = generate("cdc-synchronizer", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('cdc-synchronizer', {'stages':3,'use_reset':True});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("cdc-synchronizer", {"stages": 2}).config_hash
    b = generate("cdc-synchronizer", {"stages": 3}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("cdc-synchronizer", {"stages": 3, "width": 2}).config_hash
    b = generate("cdc-synchronizer", {"width": 2, "stages": 3}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("cdc-synchronizer", {"stages": 3})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_function_matches_entry_point() -> None:
    opts = CdcSynchronizerOptions(stages=3)
    expected = config_hash("cdc-synchronizer", opts.model_dump(mode="json"))
    assert generate("cdc-synchronizer", {"stages": 3}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("cdc-synchronizer", {"nonsense": 1})


def test_bad_bool_type_raises() -> None:
    with pytest.raises(ValidationError):
        generate("cdc-synchronizer", {"use_reset": "maybe"})  # not bool-coercible


def test_bad_enum_value_raises() -> None:
    with pytest.raises(ValidationError):
        generate("cdc-synchronizer", {"reset_style": "sideways"})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("cdc-synchronizer", {"stages": 3, "width": 2, "use_reset": True}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 4  # clk, rst, d_async, (internal stages), q
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "d_async", "q"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)


def test_explanation_mentions_metastability_and_no_pulse_guarantee() -> None:
    exp = generate("cdc-synchronizer", {}).explanation
    combined = " ".join(exp.assumptions + exp.limitations).lower()
    assert "metastability" in combined
    assert "pulse" in combined


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("cdc-synchronizer", {"naming": {"prefix": "u_"}}).code
    assert "u_clk" in code
    assert "u_d_async" in code
    assert "u_q" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("cdc-synchronizer").options_model.model_json_schema()
    props = schema["properties"]
    assert props["stages"]["description"]
    assert props["width"]["description"]
    assert props["use_reset"]["description"]


# --------------------------------------------------------------------------- #
# equivalence check against direct IR render
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_render_for_reset_variant() -> None:
    opts = CdcSynchronizerOptions(
        stages=2, use_reset=True, reset_style="async", reset_polarity="active_low"
    )
    module = build_ir(opts)
    code = render(module, language="sv")
    assert "always_ff @(posedge clk or negedge rst_n) begin" in code
    assert "if (!rst_n) begin" in code
    assert "sync_ff1 <= 1'b0;" in code
    assert "q <= 1'b0;" in code
