"""Counter reference snippet: generation, options, determinism, explanation.

Mirrors IMPLEMENTATION_PLAN §3 WP-03 task 5 required coverage. These tests are
also the template WP-05 snippet WPs copy.
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
from semicraft_core.snippets.counter import CounterOptions
from semicraft_core.snippets.counter import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("counter", {"language": language})
    assert result.code
    # IR is valid (render already validated, but assert explicitly on the IR).
    validate(build_ir(CounterOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"counter.{ext}"


def test_default_sv_matches_ir_spec_shape() -> None:
    code = generate("counter", {}).code
    assert "module counter #(" in code
    assert "parameter int unsigned WIDTH = 8" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "count <= count + 1'b1;" in code
    assert "endmodule" in code


def test_verilog_infers_output_reg_and_plain_always() -> None:
    code = generate("counter", {"language": "verilog"}).code
    assert "output reg  [WIDTH-1:0] count" in code
    assert "always @(posedge clk) begin" in code
    assert "parameter WIDTH = 8" in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_width_changes_vector_width() -> None:
    code = generate("counter", {"width": 16}).code
    assert "parameter int unsigned WIDTH = 16" in code
    # WIDTH is parameterized, so the range stays [WIDTH-1:0]; the param value moves.
    assert "[WIDTH-1:0]" in code


def test_direction_down_uses_subtraction() -> None:
    code = generate("counter", {"direction": "down"}).code
    assert "count - 1'b1" in code
    assert "count + 1'b1" not in code


def test_updown_adds_up_dn_port() -> None:
    code = generate("counter", {"direction": "updown"}).code
    assert "up_dn" in code
    assert "count + 1'b1" in code
    assert "count - 1'b1" in code


def test_saturate_emits_comparison_logic() -> None:
    overflow = generate("counter", {"wrap": "overflow"}).code
    saturate = generate("counter", {"wrap": "saturate"}).code
    # Overflow needs no comparison; saturate compares against the boundary.
    assert "!=" not in overflow
    assert "!=" in saturate


def test_saturate_down_compares_against_zero() -> None:
    code = generate("counter", {"wrap": "saturate", "direction": "down"}).code
    assert "count != {WIDTH{1'b0}}" in code


def test_enable_false_removes_en_port() -> None:
    with_en = generate("counter", {"enable": True}).code
    without_en = generate("counter", {"enable": False}).code
    # The 'en' port declaration line is present only when enable is on.
    assert any(_is_en_port_line(ln) for ln in with_en.splitlines())
    assert not any(_is_en_port_line(ln) for ln in without_en.splitlines())
    # And the enable gate disappears from the body.
    assert "if (en)" in with_en
    assert "if (en)" not in without_en


def _is_en_port_line(line: str) -> bool:
    """True for the ANSI port row declaring the standalone 'en' port."""
    stripped = line.strip()
    return stripped.startswith("input") and (
        stripped.split()[-1] == "en" or " en " in f" {stripped} " or "en," in stripped
    )


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "counter", {"reset_style": reset_style, "reset_polarity": reset_polarity}
    ).code
    if reset_polarity == "active_low":
        assert "rst_n" in code
        assert "if (!rst_n)" in code
    else:
        assert "if (rst)" in code
    if reset_style == "async":
        assert " or " in code  # reset edge added to sensitivity list
    else:
        assert "always_ff @(posedge clk) begin" in code


def test_reset_value_loaded() -> None:
    code = generate("counter", {"width": 8, "reset_value": 5}).code
    # Non-zero reset value composes a sized literal against WIDTH.
    assert "2'b11" not in code  # sanity: this is 5, not 3
    assert "3'b101" in code


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"width": 12, "direction": "updown", "wrap": "saturate"}
    a = generate("counter", opts)
    b = generate("counter", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('counter', {'width':10,'direction':'down'});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("counter", {"width": 8}).config_hash
    b = generate("counter", {"width": 9}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("counter", {"width": 8, "direction": "up"}).config_hash
    b = generate("counter", {"direction": "up", "width": 8}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("counter", {"width": 8})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_length_and_hex() -> None:
    h = generate("counter", {}).config_hash
    assert len(h) == 12
    int(h, 16)  # valid hex


def test_config_hash_uses_validated_defaults() -> None:
    """Omitting a defaulted field yields the same hash as passing its default."""
    a = generate("counter", {}).config_hash
    b = generate(
        "counter",
        {
            "width": 8,
            "direction": "up",
            "enable": True,
            "wrap": "overflow",
            "reset_value": 0,
            "language": "sv",
            "reset_style": "sync",
            "reset_polarity": "active_low",
            "include_wrapper": True,
            "comment_verbosity": "normal",
        },
    ).config_hash
    assert a == b


def test_config_hash_function_matches_entry_point() -> None:
    opts = CounterOptions(width=8)
    expected = config_hash("counter", opts.model_dump(mode="json"))
    assert generate("counter", {"width": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_reset_value_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("counter", {"width": 4, "reset_value": 16})  # 16 >= 2^4


def test_reset_value_at_boundary_ok() -> None:
    # 15 == 2^4 - 1 is the max legal value.
    result = generate("counter", {"width": 4, "reset_value": 15})
    assert result.code


def test_bad_enum_value_raises() -> None:
    with pytest.raises(ValidationError):
        generate("counter", {"direction": "sideways"})


def test_width_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("counter", {"width": 0})
    with pytest.raises(ValidationError):
        generate("counter", {"width": 2048})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("counter", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("counter", {"direction": "updown", "wrap": "saturate"}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 5
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 4  # clk, rst, en, up_dn, count
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "en", "up_dn", "count"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is not None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    # No-CDC statement is mandatory content.
    assert any("CDC" in limit or "clock-domain" in limit for limit in exp.limitations)


def test_enable_behavior_none_when_disabled() -> None:
    exp = generate("counter", {"enable": False}).explanation
    assert exp.enable_behavior is None
    assert "en" not in {s.name for s in exp.signals}


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "counter", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronous" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


# --------------------------------------------------------------------------- #
# fragment mode
# --------------------------------------------------------------------------- #


def test_fragment_mode_filename_and_no_wrapper() -> None:
    result = generate("counter", {"include_wrapper": False})
    assert result.filename == "counter_fragment.sv"
    assert "module counter" not in result.code
    assert "endmodule" not in result.code
    assert "Fragment mode" in result.code


def test_fragment_mode_verilog_extension() -> None:
    result = generate("counter", {"include_wrapper": False, "language": "verilog"})
    assert result.filename == "counter_fragment.v"


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("counter", {"naming": {"prefix": "u_"}}).code
    assert "u_clk" in code
    assert "u_count" in code
    # Params render verbatim (UPPER_SNAKE by convention).
    assert "WIDTH" in code


def test_comment_verbosity_none_strips_docs() -> None:
    code = generate("counter", {"comment_verbosity": "none"}).code
    assert "// Clock" not in code
    # Banner comments always remain (they are not IR Comment nodes).
    assert "SemiCraft" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("counter").options_model.model_json_schema()
    props = schema["properties"]
    assert props["width"]["description"]
    assert props["direction"]["description"]
    # Enum survives for the frontend segmented control.
    assert set(props["direction"]["enum"]) == {"up", "down", "updown"}


# --------------------------------------------------------------------------- #
# equivalence to the golden hand-built IR (WP-02 test_golden_counter)
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_golden_render_for_async_active_low() -> None:
    """The generator's IR renders to the same body as the WP-02 golden counter
    for the async/active-low/enable/up default-ish case."""
    opts = CounterOptions(
        width=8, reset_style="async", reset_polarity="active_low", enable=True
    )
    module = build_ir(opts)
    code = render(module, language="sv")
    assert "always_ff @(posedge clk or negedge rst_n) begin" in code
    assert "if (!rst_n) begin" in code
    assert "count <= {WIDTH{1'b0}};" in code
    assert "count <= count + 1'b1;" in code
