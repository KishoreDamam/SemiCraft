"""Encoder snippet tests: generation, options, determinism, explanation.

Mirrors ``test_counter.py`` / ``test_register.py`` (WP-03 reference test
template) adapted to the encoder's option surface: kind (priority/onehot),
num_inputs (4/8/16), valid_output. Purely combinational: no clock/reset.
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
from semicraft_core.snippets.encoder import EncoderOptions
from semicraft_core.snippets.encoder import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("encoder", {"language": language})
    assert result.code
    validate(build_ir(EncoderOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"encoder.{ext}"


def test_default_sv_matches_shape() -> None:
    code = generate("encoder", {}).code
    assert "module encoder #(" in code
    assert "parameter int unsigned NUM_INPUTS = 8" in code
    assert "localparam int unsigned OUT_WIDTH = 3" in code
    assert "always_comb begin" in code
    assert "endmodule" in code


def test_verilog_infers_output_reg_and_plain_always() -> None:
    code = generate("encoder", {"language": "verilog"}).code
    assert "output reg  [OUT_WIDTH-1:0]  dout" in code
    assert "always @(*) begin" in code
    assert "parameter NUM_INPUTS = 8" in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_kind_switches_if_chain_vs_case() -> None:
    priority = generate("encoder", {"kind": "priority"}).code
    onehot = generate("encoder", {"kind": "onehot"}).code
    assert "if (din[7])" in priority
    assert "else if" in priority
    assert "case (din)" in onehot
    assert "case (din)" not in priority
    assert "if (din[7])" not in onehot


@pytest.mark.parametrize("n", [4, 8, 16])
def test_num_inputs_changes_widths(n: int) -> None:
    code = generate("encoder", {"num_inputs": n}).code
    out_w = {4: 2, 8: 3, 16: 4}[n]
    assert f"parameter int unsigned NUM_INPUTS = {n}" in code
    assert f"localparam int unsigned OUT_WIDTH = {out_w}" in code
    assert f"din[{n - 1}]" in code  # highest-priority bit tested first


def test_num_inputs_bad_value_raises() -> None:
    with pytest.raises(ValidationError):
        generate("encoder", {"num_inputs": 5})


def test_valid_output_toggles_port() -> None:
    with_valid = generate("encoder", {"valid_output": True}).code
    without_valid = generate("encoder", {"valid_output": False}).code
    assert any(_is_port_line(ln, "valid") for ln in with_valid.splitlines())
    assert not any(_is_port_line(ln, "valid") for ln in without_valid.splitlines())
    assert "valid = 1'b1;" in with_valid
    assert "valid = 1'b1;" not in without_valid


def test_priority_order_documented_in_explanation() -> None:
    exp = generate("encoder", {"kind": "priority", "num_inputs": 8}).explanation
    combined = " ".join(exp.assumptions).lower()
    assert "din[7]" in combined
    assert "din[0]" in combined
    assert "priority" in combined


def test_onehot_explanation_notes_no_priority_resolution() -> None:
    exp = generate("encoder", {"kind": "onehot"}).explanation
    combined = " ".join(exp.assumptions).lower()
    assert "one-hot" in combined or "onehot" in combined


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"kind": "onehot", "num_inputs": 16, "valid_output": False}
    a = generate("encoder", opts)
    b = generate("encoder", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('encoder', {'kind':'onehot','num_inputs':4});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("encoder", {"num_inputs": 8}).config_hash
    b = generate("encoder", {"num_inputs": 16}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("encoder", {"kind": "onehot", "num_inputs": 8}).config_hash
    b = generate("encoder", {"num_inputs": 8, "kind": "onehot"}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("encoder", {"num_inputs": 8})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_function_matches_entry_point() -> None:
    opts = EncoderOptions(num_inputs=8)
    expected = config_hash("encoder", opts.model_dump(mode="json"))
    assert generate("encoder", {"num_inputs": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_bad_enum_value_raises() -> None:
    with pytest.raises(ValidationError):
        generate("encoder", {"kind": "weird"})


def test_num_inputs_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("encoder", {"num_inputs": 5})
    with pytest.raises(ValidationError):
        generate("encoder", {"num_inputs": 32})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("encoder", {"nonsense": 1})


def test_bad_bool_type_raises() -> None:
    with pytest.raises(ValidationError):
        generate("encoder", {"valid_output": "maybe"})  # not bool-coercible


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("encoder", {"kind": "priority", "valid_output": True}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 4
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 3  # din, dout, valid
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"din", "dout", "valid"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)


def test_enable_behavior_none_always() -> None:
    """Encoder is purely combinational: enable_behavior is always None."""
    exp = generate("encoder", {}).explanation
    assert exp.enable_behavior is None


def test_valid_output_false_removes_valid_signal_doc() -> None:
    exp = generate("encoder", {"valid_output": False}).explanation
    assert "valid" not in {s.name for s in exp.signals}


# --------------------------------------------------------------------------- #
# fragment mode
# --------------------------------------------------------------------------- #


def test_fragment_mode_filename_and_no_wrapper() -> None:
    result = generate("encoder", {"include_wrapper": False})
    assert result.filename == "encoder_fragment.sv"
    assert "module encoder" not in result.code
    assert "endmodule" not in result.code
    assert "Fragment mode" in result.code


def test_fragment_mode_verilog_extension() -> None:
    result = generate("encoder", {"include_wrapper": False, "language": "verilog"})
    assert result.filename == "encoder_fragment.v"


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("encoder", {"naming": {"prefix": "u_"}}).code
    assert "u_din" in code
    assert "u_dout" in code
    assert "NUM_INPUTS" in code


def test_comment_verbosity_none_strips_docs() -> None:
    code = generate("encoder", {"comment_verbosity": "none"}).code
    assert "Priority encoder: highest-indexed" not in code
    assert "SemiCraft" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("encoder").options_model.model_json_schema()
    props = schema["properties"]
    assert props["kind"]["description"]
    assert props["num_inputs"]["description"]
    assert set(props["kind"]["enum"]) == {"priority", "onehot"}
    assert set(props["num_inputs"]["enum"]) == {4, 8, 16}


# --------------------------------------------------------------------------- #
# direct IR render checks
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_render_for_onehot() -> None:
    opts = EncoderOptions(kind="onehot", num_inputs=4, valid_output=True)
    module = build_ir(opts)
    code = render(module, language="sv")
    assert "case (din)" in code
    assert "default: begin" in code
    assert "valid = 1'b0;" in code


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _is_port_line(line: str, port_name: str) -> bool:
    """True for the ANSI port row declaring the standalone port ``port_name``."""
    stripped = line.strip()
    return stripped.startswith("output") and (
        stripped.split()[-1] == port_name
        or f" {port_name} " in f" {stripped} "
        or f"{port_name}," in stripped
    )
