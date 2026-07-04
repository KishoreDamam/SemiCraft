"""Shift-register snippet tests: generation, options, determinism, explanation.

Mirrors ``test_counter.py`` / ``test_register.py`` (WP-03 reference test
template) adapted to the shift-register's option surface: depth, direction,
parallel_load, serial_out_only, enable.
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
from semicraft_core.snippets.shift_register import ShiftRegisterOptions
from semicraft_core.snippets.shift_register import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("shift-register", {"language": language})
    assert result.code
    validate(build_ir(ShiftRegisterOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"shift_register.{ext}"


def test_default_sv_matches_shape() -> None:
    code = generate("shift-register", {}).code
    assert "module shift_register #(" in code
    assert "parameter int unsigned DEPTH = 8" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "q <= {si, q[DEPTH-1:1]};" in code
    assert "assign so = q[0:0];" in code
    assert "endmodule" in code


def test_verilog_infers_output_reg_and_plain_always() -> None:
    code = generate("shift-register", {"language": "verilog"}).code
    assert "output reg  [DEPTH-1:0] q" in code
    assert "always @(posedge clk) begin" in code
    assert "parameter DEPTH = 8" in code


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


def test_depth_changes_vector_width() -> None:
    code = generate("shift-register", {"depth": 16}).code
    assert "parameter int unsigned DEPTH = 16" in code
    assert "[DEPTH-1:0]" in code


def test_direction_flips_concat_order() -> None:
    right_code = generate("shift-register", {"direction": "right"}).code
    left_code = generate("shift-register", {"direction": "left"}).code
    # right: si enters at MSB side, drains toward LSB.
    assert "q <= {si, q[DEPTH-1:1]};" in right_code
    assert "assign so = q[0:0];" in right_code
    # left: si enters at LSB side, drains toward MSB.
    assert "q <= {q[DEPTH-2:0], si};" in left_code
    assert "assign so = q[DEPTH-1:DEPTH-1];" in left_code


def test_parallel_load_adds_load_and_d_ports() -> None:
    without = generate("shift-register", {"parallel_load": False}).code
    with_load = generate("shift-register", {"parallel_load": True}).code
    assert not any(_is_port_line(ln, "load") for ln in without.splitlines())
    assert not any(_is_port_line(ln, "d") for ln in without.splitlines())
    assert any(_is_port_line(ln, "load") for ln in with_load.splitlines())
    assert any(_is_port_line(ln, "d") for ln in with_load.splitlines())
    assert "if (load)" in with_load


def test_parallel_load_beats_shift() -> None:
    code = generate("shift-register", {"parallel_load": True, "enable": True}).code
    assert "if (load) begin" in code
    load_idx = code.index("if (load)")
    q_load = code.index("q <= d;")
    assert load_idx < q_load


def test_serial_out_only_removes_q_port() -> None:
    with_q = generate("shift-register", {"serial_out_only": False}).code
    without_q = generate("shift-register", {"serial_out_only": True}).code
    assert any(_is_port_line(ln, "q") for ln in with_q.splitlines())
    assert not any(_is_port_line(ln, "q") for ln in without_q.splitlines())
    # so is always present.
    assert any(_is_port_line(ln, "so") for ln in with_q.splitlines())
    assert any(_is_port_line(ln, "so") for ln in without_q.splitlines())
    # The internal register 'q' must still be declared (as a Signal) so the
    # shift logic and 'so' tap resolve.
    assert "q" in without_q  # internal signal declaration line + usages


def test_serial_out_only_still_validates_and_renders_in_both_languages() -> None:
    """Regression test: serial_out_only used to leave 'q' as an unresolved Ref
    once its port was dropped (IR validation rule 2 failure) because there was
    no internal Signal declaration for it. Must render clean in both languages
    and across parallel_load / enable combos."""
    for language in ("sv", "verilog"):
        for parallel_load in (True, False):
            for enable in (True, False):
                result = generate(
                    "shift-register",
                    {
                        "serial_out_only": True,
                        "parallel_load": parallel_load,
                        "enable": enable,
                        "language": language,
                    },
                )
                assert result.code


def test_enable_false_removes_en_port() -> None:
    with_en = generate("shift-register", {"enable": True}).code
    without_en = generate("shift-register", {"enable": False}).code
    assert any(_is_port_line(ln, "en") for ln in with_en.splitlines())
    assert not any(_is_port_line(ln, "en") for ln in without_en.splitlines())
    assert "if (en)" in with_en
    assert "if (en)" not in without_en


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "shift-register", {"reset_style": reset_style, "reset_polarity": reset_polarity}
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


def test_depth_changes_reset_range() -> None:
    code8 = generate("shift-register", {"depth": 8}).code
    code32 = generate("shift-register", {"depth": 32}).code
    assert "parameter int unsigned DEPTH = 8" in code8
    assert "parameter int unsigned DEPTH = 32" in code32
    # Reset value composes against DEPTH regardless of its numeric value.
    assert "q <= {DEPTH{1'b0}};" in code8
    assert "q <= {DEPTH{1'b0}};" in code32


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"depth": 12, "direction": "left", "parallel_load": True}
    a = generate("shift-register", opts)
    b = generate("shift-register", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('shift-register', {'depth':10,'direction':'left'});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# config hash
# --------------------------------------------------------------------------- #


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("shift-register", {"depth": 8}).config_hash
    b = generate("shift-register", {"depth": 9}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("shift-register", {"depth": 8, "direction": "left"}).config_hash
    b = generate("shift-register", {"direction": "left", "depth": 8}).config_hash
    assert a == b


def test_config_hash_in_header() -> None:
    result = generate("shift-register", {"depth": 8})
    assert f"config hash: {result.config_hash}" in result.code


def test_config_hash_function_matches_entry_point() -> None:
    opts = ShiftRegisterOptions(depth=8)
    expected = config_hash("shift-register", opts.model_dump(mode="json"))
    assert generate("shift-register", {"depth": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_depth_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("shift-register", {"depth": 1})  # below ge=2
    with pytest.raises(ValidationError):
        generate("shift-register", {"depth": 257})  # above le=256


def test_bad_enum_value_raises() -> None:
    with pytest.raises(ValidationError):
        generate("shift-register", {"direction": "sideways"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("shift-register", {"nonsense": 1})


def test_bad_bool_type_raises() -> None:
    with pytest.raises(ValidationError):
        generate("shift-register", {"parallel_load": "maybe"})  # not bool-coercible


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate(
        "shift-register", {"parallel_load": True, "enable": True}
    ).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 5
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 6  # clk, rst, en, load, d, si, so (q too)
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "en", "load", "d", "si", "so"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is not None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    assert any("CDC" in limit or "clock-domain" in limit for limit in exp.limitations)


def test_enable_behavior_none_when_disabled() -> None:
    exp = generate("shift-register", {"enable": False}).explanation
    assert exp.enable_behavior is None
    assert "en" not in {s.name for s in exp.signals}


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "shift-register", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronous" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


def test_explanation_documents_serial_out_only() -> None:
    exp = generate("shift-register", {"serial_out_only": True}).explanation
    assert "q" not in {s.name for s in exp.signals}
    combined = " ".join(exp.configuration).lower()
    assert "serial-out only" in combined or "serial out" in combined


# --------------------------------------------------------------------------- #
# fragment mode
# --------------------------------------------------------------------------- #


def test_fragment_mode_filename_and_no_wrapper() -> None:
    result = generate("shift-register", {"include_wrapper": False})
    assert result.filename == "shift_register_fragment.sv"
    assert "module shift_register" not in result.code
    assert "endmodule" not in result.code
    assert "Fragment mode" in result.code


def test_fragment_mode_verilog_extension() -> None:
    result = generate("shift-register", {"include_wrapper": False, "language": "verilog"})
    assert result.filename == "shift_register_fragment.v"


# --------------------------------------------------------------------------- #
# naming / style options flow through
# --------------------------------------------------------------------------- #


def test_naming_prefix_applied() -> None:
    code = generate("shift-register", {"naming": {"prefix": "u_"}}).code
    assert "u_clk" in code
    assert "u_q" in code
    assert "DEPTH" in code


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("shift-register").options_model.model_json_schema()
    props = schema["properties"]
    assert props["depth"]["description"]
    assert props["direction"]["description"]
    assert set(props["direction"]["enum"]) == {"left", "right"}


# --------------------------------------------------------------------------- #
# equivalence check against direct IR render
# --------------------------------------------------------------------------- #


def test_generated_ir_matches_render_for_async_active_low() -> None:
    opts = ShiftRegisterOptions(
        depth=8, reset_style="async", reset_polarity="active_low", enable=True
    )
    module = build_ir(opts)
    code = render(module, language="sv")
    assert "always_ff @(posedge clk or negedge rst_n) begin" in code
    assert "if (!rst_n) begin" in code
    assert "q <= {DEPTH{1'b0}};" in code
    assert "if (en) begin" in code
    assert "q <= {si, q[DEPTH-1:1]};" in code


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
    ) or (
        stripped.startswith("output")
        and (
            stripped.split()[-1] == port_name
            or f" {port_name} " in f" {stripped} "
            or f"{port_name}," in stripped
        )
    )
