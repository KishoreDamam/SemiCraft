"""Register snippet tests: generation, options, determinism, explanation.

Mirrors ``test_counter.py`` (WP-03 reference test template) adapted to the
register's option surface: width, enable, reset_value, clear_input.
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
from semicraft_core.snippets.register import RegisterOptions
from semicraft_core.snippets.register import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("register", {"language": language})
    assert result.code
    validate(build_ir(RegisterOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"register.{ext}"


def test_default_sv_matches_shape() -> None:
    code = generate("register", {}).code
    assert "module register #(" in code
    assert "parameter int unsigned WIDTH = 8" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "q <= d;" in code
    assert "endmodule" in code


def test_verilog_infers_output_reg_and_plain_always() -> None:
    code = generate("register", {"language": "verilog"}).code
    assert "output reg  [WIDTH-1:0] q" in code
    assert "always @(posedge clk) begin" in code
    assert "parameter WIDTH = 8" in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_width_changes_vector_width() -> None:
    code = generate("register", {"width": 16}).code
    assert "parameter int unsigned WIDTH = 16" in code
    assert "[WIDTH-1:0]" in code


def test_enable_false_removes_en_port() -> None:
    with_en = generate("register", {"enable": True}).code
    without_en = generate("register", {"enable": False}).code
    assert any(_is_port_line(ln, "en") for ln in with_en.splitlines())
    assert not any(_is_port_line(ln, "en") for ln in without_en.splitlines())
    assert "if (en)" in with_en
    assert "if (en)" not in without_en


def test_clear_input_adds_clr_port() -> None:
    without_clr = generate("register", {"clear_input": False}).code
    with_clr = generate("register", {"clear_input": True}).code
    assert not any(_is_port_line(ln, "clr") for ln in without_clr.splitlines())
    assert any(_is_port_line(ln, "clr") for ln in with_clr.splitlines())
    assert "if (clr)" in with_clr


def test_clear_beats_enable_priority_order() -> None:
    """When both clear_input and enable are on, clr must be the outer/first
    condition and en only gates the else-branch load — visible in the
    if-structure as `if (clr) ... else if (en) ...`."""
    code = generate("register", {"clear_input": True, "enable": True}).code
    assert "if (clr) begin" in code
    # en is nested inside the else branch, not checked before clr.
    clr_idx = code.index("if (clr)")
    en_idx = code.index("if (en)")
    assert clr_idx < en_idx


def test_clear_only_no_enable_loads_d_unconditionally_otherwise() -> None:
    code = generate("register", {"clear_input": True, "enable": False}).code
    assert "if (clr) begin" in code
    assert "if (en)" not in code
    # else branch loads d unconditionally when clr is not asserted.
    assert "q <= d;" in code


def test_enable_only_no_clear_holds_when_low() -> None:
    code = generate("register", {"clear_input": False, "enable": True}).code
    assert "if (en) begin" in code
    assert "if (clr)" not in code


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "register", {"reset_style": reset_style, "reset_polarity": reset_polarity}
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


def test_reset_value_loaded() -> None:
    code = generate("register", {"width": 8, "reset_value": 5}).code
    assert "2'b11" not in code
    assert "3'b101" in code


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"width": 12, "clear_input": True, "enable": True}
    a = generate("register", opts)
    b = generate("register", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('register', {'width':10,'clear_input':True});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("register", {"width": 8}).config_hash
    b = generate("register", {"width": 9}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("register", {"width": 8, "enable": True}).config_hash
    b = generate("register", {"enable": True, "width": 8}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("register", {"width": 8})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_function_matches_entry_point() -> None:
    opts = RegisterOptions(width=8)
    expected = config_hash("register", opts.model_dump(mode="json"))
    assert generate("register", {"width": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_reset_value_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("register", {"width": 4, "reset_value": 16})  # 16 >= 2^4


def test_reset_value_at_boundary_ok() -> None:
    result = generate("register", {"width": 4, "reset_value": 15})
    assert result.code


def test_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("register", {"width": 0})
    with pytest.raises(ValidationError):
        generate("register", {"width": 2048})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("register", {"nonsense": 1})


def test_bad_bool_type_raises() -> None:
    with pytest.raises(ValidationError):
        generate("register", {"clear_input": "maybe"})  # not bool-coercible


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("register", {"clear_input": True, "enable": True}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 5
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 5  # clk, rst, clr, en, d, q
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "clr", "en", "d", "q"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is not None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any("CDC" in limit or "clock-domain" in limit for limit in exp.limitations)
    # clear-beats-enable priority must be documented somewhere in the text.
    assert "clr" in exp.enable_behavior.lower() or "clear" in exp.enable_behavior.lower()


def test_enable_behavior_none_when_disabled() -> None:
    exp = generate("register", {"enable": False}).explanation
    assert exp.enable_behavior is None
    assert "en" not in {s.name for s in exp.signals}


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "register", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronous" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


def test_explanation_documents_clear_priority() -> None:
    exp = generate("register", {"clear_input": True, "enable": True}).explanation
    combined = " ".join(exp.limitations + [exp.enable_behavior or ""]).lower()
    assert "clr" in combined or "clear" in combined
    assert "priority" in combined or "beats" in combined or "wins" in combined


# --------------------------------------------------------------------------- #
# fragment mode
# --------------------------------------------------------------------------- #


def test_fragment_mode_filename_and_no_wrapper() -> None:
    result = generate("register", {"include_wrapper": False})
    assert result.filename == "register_fragment.sv"
    assert "module register" not in result.code
    assert "endmodule" not in result.code
    assert "Fragment mode" in result.code


def test_fragment_mode_verilog_extension() -> None:
    result = generate("register", {"include_wrapper": False, "language": "verilog"})
    assert result.filename == "register_fragment.v"


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("register", {"naming": {"prefix": "u_"}}).code
    assert "u_clk" in code
    assert "u_q" in code
    assert "WIDTH" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("register").options_model.model_json_schema()
    props = schema["properties"]
    assert props["width"]["description"]
    assert props["clear_input"]["description"]
    assert props["enable"]["description"]


# --------------------------------------------------------------------------- #
# equivalence check against direct IR render
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_render_for_async_active_low() -> None:
    opts = RegisterOptions(
        width=8, reset_style="async", reset_polarity="active_low", enable=True
    )
    module = build_ir(opts)
    code = render(module, language="sv")
    assert "always_ff @(posedge clk or negedge rst_n) begin" in code
    assert "if (!rst_n) begin" in code
    assert "q <= {WIDTH{1'b0}};" in code
    assert "if (en) begin" in code
    assert "q <= d;" in code


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def _is_port_line(line: str, port_name: str) -> bool:
    """True for the ANSI port row declaring the standalone port ``port_name``."""
    stripped = line.strip()
    return stripped.startswith("input") and (
        stripped.split()[-1] == port_name
        or f" {port_name} " in f" {stripped} "
        or f"{port_name}," in stripped
    )
