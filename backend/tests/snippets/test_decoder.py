"""Decoder snippet tests: generation, options, determinism, explanation.

Mirrors ``test_counter.py`` / ``test_register.py`` (WP-03 reference test
template) adapted to the decoder's option surface: num_outputs
(2/4/8/16), enable, output_polarity. Purely combinational: no clock/reset.
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
from semicraft_core.snippets.decoder import DecoderOptions
from semicraft_core.snippets.decoder import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("decoder", {"language": language})
    assert result.code
    validate(build_ir(DecoderOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"decoder.{ext}"


def test_default_sv_matches_shape() -> None:
    code = generate("decoder", {}).code
    assert "module decoder #(" in code
    assert "parameter int unsigned NUM_OUTPUTS = 8" in code
    assert "assign dout = en ? (" in code
    assert "<< sel" in code
    assert "endmodule" in code


def test_verilog_infers_output_wire_and_plain_ports() -> None:
    code = generate("decoder", {"language": "verilog"}).code
    assert "output wire [NUM_OUTPUTS-1:0] dout" in code
    assert "parameter NUM_OUTPUTS = 8" in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("n", [2, 4, 8, 16])
def test_num_outputs_changes_widths(n: int) -> None:
    code = generate("decoder", {"num_outputs": n}).code
    sel_w = {2: 1, 4: 2, 8: 3, 16: 4}[n]
    assert f"parameter int unsigned NUM_OUTPUTS = {n}" in code
    assert "sel," in code or "sel" in code
    assert f"[{sel_w - 1}:0]" in code


def test_num_outputs_bad_value_raises() -> None:
    with pytest.raises(ValidationError):
        generate("decoder", {"num_outputs": 3})


def test_enable_toggles_port_and_gating() -> None:
    with_en = generate("decoder", {"enable": True}).code
    without_en = generate("decoder", {"enable": False}).code
    assert any(_is_input_port_line(ln, "en") for ln in with_en.splitlines())
    assert not any(_is_input_port_line(ln, "en") for ln in without_en.splitlines())
    assert "en ?" in with_en
    assert "en ?" not in without_en


def test_output_polarity_adds_inversion() -> None:
    active_high = generate("decoder", {"output_polarity": "active_high"}).code
    active_low = generate("decoder", {"output_polarity": "active_low"}).code
    assert "assign dout = ~(" in active_low
    assert "assign dout = ~(" not in active_high


def test_active_low_disabled_state_is_documented() -> None:
    exp = generate("decoder", {"output_polarity": "active_low", "enable": True}).explanation
    assert "all-one" in exp.enable_behavior.lower()


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"num_outputs": 16, "enable": False, "output_polarity": "active_low"}
    a = generate("decoder", opts)
    b = generate("decoder", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('decoder', {'num_outputs':4,'output_polarity':'active_low'});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("decoder", {"num_outputs": 8}).config_hash
    b = generate("decoder", {"num_outputs": 16}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("decoder", {"num_outputs": 8, "enable": True}).config_hash
    b = generate("decoder", {"enable": True, "num_outputs": 8}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("decoder", {"num_outputs": 8})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_function_matches_entry_point() -> None:
    opts = DecoderOptions(num_outputs=8)
    expected = config_hash("decoder", opts.model_dump(mode="json"))
    assert generate("decoder", {"num_outputs": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_bad_enum_value_raises() -> None:
    with pytest.raises(ValidationError):
        generate("decoder", {"output_polarity": "weird"})


def test_num_outputs_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("decoder", {"num_outputs": 3})
    with pytest.raises(ValidationError):
        generate("decoder", {"num_outputs": 32})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("decoder", {"nonsense": 1})


def test_bad_bool_type_raises() -> None:
    with pytest.raises(ValidationError):
        generate("decoder", {"enable": "maybe"})  # not bool-coercible


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("decoder", {"enable": True, "output_polarity": "active_low"}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 3  # sel, en, dout
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"sel", "en", "dout"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is not None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any(
        "clock-domain" in limit or "CDC" in limit or "no clock" in limit.lower()
        for limit in exp.limitations
    )


def test_enable_behavior_none_when_disabled() -> None:
    exp = generate("decoder", {"enable": False}).explanation
    assert exp.enable_behavior is None
    assert "en" not in {s.name for s in exp.signals}


def test_explanation_reflects_polarity_choice() -> None:
    exp = generate("decoder", {"output_polarity": "active_low"}).explanation
    combined = " ".join(exp.limitations).lower()
    assert "active-low" in combined


# --------------------------------------------------------------------------- #
# fragment mode
# --------------------------------------------------------------------------- #


def test_fragment_mode_filename_and_no_wrapper() -> None:
    result = generate("decoder", {"include_wrapper": False})
    assert result.filename == "decoder_fragment.sv"
    assert "module decoder" not in result.code
    assert "endmodule" not in result.code
    assert "Fragment mode" in result.code


def test_fragment_mode_verilog_extension() -> None:
    result = generate("decoder", {"include_wrapper": False, "language": "verilog"})
    assert result.filename == "decoder_fragment.v"


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("decoder", {"naming": {"prefix": "u_"}}).code
    assert "u_sel" in code
    assert "u_dout" in code
    assert "NUM_OUTPUTS" in code


def test_comment_verbosity_none_strips_docs() -> None:
    code = generate("decoder", {"comment_verbosity": "none"}).code
    assert "SemiCraft" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("decoder").options_model.model_json_schema()
    props = schema["properties"]
    assert props["num_outputs"]["description"]
    assert props["enable"]["description"]
    assert props["output_polarity"]["description"]
    assert set(props["num_outputs"]["enum"]) == {2, 4, 8, 16}
    assert set(props["output_polarity"]["enum"]) == {"active_high", "active_low"}


# --------------------------------------------------------------------------- #
# direct IR render checks
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_render_for_active_low_no_enable() -> None:
    opts = DecoderOptions(num_outputs=4, enable=False, output_polarity="active_low")
    module = build_ir(opts)
    code = render(module, language="sv")
    assert "assign dout = ~(" in code
    assert "en ?" not in code


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _is_input_port_line(line: str, port_name: str) -> bool:
    """True for the ANSI port row declaring the standalone input port ``port_name``."""
    stripped = line.strip()
    return stripped.startswith("input") and (
        stripped.split()[-1] == port_name
        or f" {port_name} " in f" {stripped} "
        or f"{port_name}," in stripped
    )
