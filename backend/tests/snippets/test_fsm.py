"""FSM hero snippet: generation, encodings, Moore/Mealy, outputs, determinism.

Deeper than the sibling snippet tests (WP-05i is the hero snippet): both
languages, all three encodings with verified Verilog localparam values,
Moore/Mealy structure, output ports, reset_state resolution, per-state TODO
coverage, the no-latch default-first pattern, and the full invalid-option set.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from pydantic import ValidationError
from semicraft_core import generate
from semicraft_core.ir import validate
from semicraft_core.snippets import registry
from semicraft_core.snippets.fsm import FsmOptions
from semicraft_core.snippets.fsm import generate as build_ir

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("fsm", {"language": language})
    assert result.code
    validate(build_ir(FsmOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"fsm.{ext}"


def test_registered() -> None:
    assert registry.get("fsm").id == "fsm"
    assert "fsm" in {s.id for s in registry.all()}


def test_default_sv_shape() -> None:
    code = generate("fsm", {}).code
    assert "module fsm (" in code
    assert "typedef enum logic [1:0] {" in code
    assert "} state_t;" in code
    assert "logic [1:0] state;" in code
    assert "logic [1:0] state_next;" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "state <= state_next;" in code
    assert "always_comb begin" in code
    assert "unique case (state)" in code
    assert "endmodule" in code


def test_verilog_uses_localparams_and_plain_always() -> None:
    code = generate("fsm", {"language": "verilog"}).code
    assert "typedef" not in code
    assert "// state_t: binary encoding" in code
    assert "localparam [1:0] idle = 2'b00;" in code
    assert "always @(posedge clk) begin" in code
    assert "always @(*) begin" in code
    assert "reg [1:0] state;" in code


# --------------------------------------------------------------------------- #
# encoding effects (Verilog localparam values verified in output text)
# --------------------------------------------------------------------------- #


def test_verilog_binary_localparam_values() -> None:
    code = generate("fsm", {"language": "verilog", "encoding": "binary"}).code
    assert "localparam [1:0] idle = 2'b00;" in code
    assert "localparam [1:0] run  = 2'b01;" in code
    assert "localparam [1:0] done = 2'b10;" in code


def test_verilog_onehot_localparam_values_and_width() -> None:
    code = generate("fsm", {"language": "verilog", "encoding": "onehot"}).code
    # 3 states -> 3-bit one-hot; one bit set per state.
    assert "localparam [2:0] idle = 3'b001;" in code
    assert "localparam [2:0] run  = 3'b010;" in code
    assert "localparam [2:0] done = 3'b100;" in code
    assert "reg [2:0] state;" in code


def test_verilog_gray_localparam_values() -> None:
    code = generate(
        "fsm",
        {
            "language": "verilog",
            "encoding": "gray",
            "states": ["a", "b", "c", "d"],
        },
    ).code
    # 4-state Gray sequence: 00, 01, 11, 10 (one bit changes per step).
    assert "localparam [1:0] a = 2'b00;" in code
    assert "localparam [1:0] b = 2'b01;" in code
    assert "localparam [1:0] c = 2'b11;" in code
    assert "localparam [1:0] d = 2'b10;" in code


def test_encoding_changes_output() -> None:
    binary = generate("fsm", {"language": "verilog", "encoding": "binary"}).code
    onehot = generate("fsm", {"language": "verilog", "encoding": "onehot"}).code
    gray = generate("fsm", {"language": "verilog", "encoding": "gray"}).code
    assert binary != onehot
    assert binary != gray
    assert onehot != gray


def test_state_width_matches_encoding() -> None:
    # 5 states: binary/gray -> 3 bits (ceil(log2 5)); onehot -> 5 bits.
    states = ["s0", "s1", "s2", "s3", "s4"]
    bin_code = generate("fsm", {"states": states, "encoding": "binary"}).code
    oh_code = generate("fsm", {"states": states, "encoding": "onehot"}).code
    assert "logic [2:0] state;" in bin_code
    assert "logic [4:0] state;" in oh_code


# --------------------------------------------------------------------------- #
# Moore / Mealy structure
# --------------------------------------------------------------------------- #


def test_moore_has_separate_output_block() -> None:
    code = generate("fsm", {"machine": "moore", "outputs": ["busy"]}).code
    # Two always_comb blocks: next-state + output logic.
    assert code.count("always_comb begin") == 2
    assert "// Moore output logic" in code
    assert "// TODO: Moore outputs for state idle" in code
    assert "busy = 1'b0;" in code


def test_mealy_defaults_outputs_in_next_state_block() -> None:
    code = generate("fsm", {"machine": "mealy", "outputs": ["valid"]}).code
    # Mealy: no separate output block; outputs defaulted in next-state comb.
    assert code.count("always_comb begin") == 1
    assert "// Moore output logic" not in code
    assert "valid = 1'b0;" in code
    assert "// TODO: Mealy outputs for this state belong here" in code


def test_no_outputs_has_no_output_block() -> None:
    code = generate("fsm", {"machine": "moore", "outputs": []}).code
    assert code.count("always_comb begin") == 1
    assert "output" not in code  # no output ports declared


# --------------------------------------------------------------------------- #
# outputs add ports
# --------------------------------------------------------------------------- #


def test_outputs_add_ports() -> None:
    code = generate("fsm", {"outputs": ["busy", "ready"]}).code
    assert "output logic busy" in code
    assert "output logic ready" in code


def test_output_verilog_is_output_reg() -> None:
    code = generate("fsm", {"language": "verilog", "outputs": ["busy"]}).code
    # Procedurally driven output -> `output reg` (rule 6).
    assert "output reg  busy" in code


# --------------------------------------------------------------------------- #
# reset_state resolution
# --------------------------------------------------------------------------- #


def test_reset_state_defaults_to_first() -> None:
    code = generate("fsm", {"states": ["boot", "work", "halt"]}).code
    assert "state <= boot;" in code


def test_reset_state_honored() -> None:
    code = generate(
        "fsm", {"states": ["boot", "work", "halt"], "reset_state": "work"}
    ).code
    assert "state <= work;" in code
    assert "state <= boot;" not in code


# --------------------------------------------------------------------------- #
# per-state TODO coverage + default-first no-latch pattern
# --------------------------------------------------------------------------- #


def test_every_state_gets_transition_todo() -> None:
    states = ["idle", "load", "run", "flush", "done"]
    code = generate("fsm", {"states": states}).code
    for s in states:
        assert f"// TODO: transition logic for {s}" in code


def test_default_first_no_latch_pattern() -> None:
    code = generate("fsm", {}).code
    # The hold-default assignment must precede the case in the next-state block.
    hold = code.index("state_next = state;")
    case = code.index("case (state)")
    assert hold < case
    assert "// default: hold current state (no-latch guarantee)" in code


def test_full_coverage_no_default_arm() -> None:
    code = generate("fsm", {}).code
    # Full enum coverage -> no default case arm needed (IR_SPEC §6 rule 5).
    # (The word "default" appears in a hold comment; check for an actual arm.)
    arm_lines = [ln.strip() for ln in code.splitlines() if ln.strip().startswith("default")]
    assert not any(ln.startswith("default:") and "//" not in ln for ln in arm_lines)


def test_five_state_fsm() -> None:
    states = ["a", "b", "c", "d", "e"]
    code = generate("fsm", {"states": states}).code
    for s in states:
        assert f"{s}: begin" in code


# --------------------------------------------------------------------------- #
# reset variants
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "fsm", {"reset_style": reset_style, "reset_polarity": reset_polarity}
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


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"states": ["a", "b", "c"], "encoding": "gray", "outputs": ["x"]}
    a = generate("fsm", opts)
    b = generate("fsm", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('fsm', {'states':['s0','s1'],'encoding':'onehot'});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_duplicate_states_raise() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"states": ["idle", "run", "idle"]})


def test_bad_state_identifier_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"states": ["idle", "2fast"]})


def test_reset_state_not_in_states_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"states": ["idle", "run"], "reset_state": "done"})


def test_output_colliding_with_state_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"states": ["idle", "run"], "outputs": ["run"]})


def test_output_colliding_with_reserved_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"outputs": ["state"]})


def test_state_colliding_with_reserved_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"states": ["idle", "state"]})


def test_too_many_states_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"states": [f"s{i}" for i in range(17)]})


def test_too_few_states_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"states": ["only"]})


def test_too_many_outputs_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"outputs": [f"o{i}" for i in range(9)]})


def test_duplicate_outputs_raise() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"outputs": ["done_o", "done_o"]})


def test_bad_encoding_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"encoding": "thermometer"})


def test_bad_machine_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"machine": "mixed"})


def test_bad_bool_raises() -> None:
    # Pydantic lax mode coerces "yes"->True, so use a non-coercible token.
    with pytest.raises(ValidationError):
        generate("fsm", {"include_wrapper": "maybe"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("fsm", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate(
        "fsm",
        {"machine": "mealy", "encoding": "onehot", "outputs": ["busy", "ready"]},
    ).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 6
    assert all(c.strip() for c in exp.configuration)
    # clk, rst, busy, ready, state, state_next
    assert len(exp.signals) >= 6
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "busy", "ready", "state", "state_next"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)


def test_explanation_documents_skeleton_nature() -> None:
    exp = generate("fsm", {}).explanation
    text = " ".join(exp.limitations).lower()
    assert "skeleton" in text or "todo" in text


def test_explanation_documents_encoding_tradeoffs() -> None:
    for enc, needle in [
        ("binary", "area-efficient"),
        ("onehot", "one bit per state"),
        ("gray", "one bit"),
    ]:
        exp = generate("fsm", {"encoding": enc}).explanation
        blob = " ".join(exp.assumptions + exp.configuration).lower()
        assert needle in blob


def test_explanation_documents_no_latch_and_cdc() -> None:
    exp = generate("fsm", {}).explanation
    text = " ".join(exp.assumptions + exp.limitations).lower()
    assert "exhaustive" in text or "never takes an undefined" in text
    assert "cdc" in text or "clock-domain" in text


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "fsm", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronous" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


# --------------------------------------------------------------------------- #
# schema fidelity (frontend forms depend on it)
# --------------------------------------------------------------------------- #


def test_options_model_json_schema_has_array_and_enums() -> None:
    schema = registry.get("fsm").options_model.model_json_schema()
    props = schema["properties"]
    assert props["states"]["type"] == "array"
    assert props["states"]["items"]["type"] == "string"
    assert props["states"]["description"]
    assert set(props["encoding"]["enum"]) == {"binary", "onehot", "gray"}
    assert set(props["machine"]["enum"]) == {"moore", "mealy"}


# --------------------------------------------------------------------------- #
# fragment mode
# --------------------------------------------------------------------------- #


def test_fragment_mode() -> None:
    result = generate("fsm", {"include_wrapper": False})
    assert result.filename == "fsm_fragment.sv"
    assert "module fsm" not in result.code
    assert "endmodule" not in result.code


# --------------------------------------------------------------------------- #
# comment verbosity
# --------------------------------------------------------------------------- #


def test_comment_verbosity_none_strips_todos() -> None:
    code = generate("fsm", {"comment_verbosity": "none"}).code
    assert "TODO" not in code
    assert "SemiCraft" in code  # banner remains (not an IR Comment node)
