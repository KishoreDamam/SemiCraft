"""Round-robin arbiter module: generation, options, determinism, explanation,
port_groups/tb_spec shape, plus arbiter-specific structural sanity of the
two-pass mask/priority logic and the pointer update (mirrors test_debouncer.py).
"""

from __future__ import annotations

import re
import subprocess
import sys

import pytest
from pydantic import ValidationError
from semicraft_core import config_hash, generate
from semicraft_core.generate import generate_files
from semicraft_core.ir import validate
from semicraft_core.modules.contract import Check, PortGroup, TbSpec
from semicraft_core.modules.rr_arbiter import RrArbiterOptions, port_groups, tb_spec
from semicraft_core.modules.rr_arbiter import generate as build_ir
from semicraft_core.render import render
from semicraft_core.snippets import registry

# --------------------------------------------------------------------------- #
# generation + validation + rendering in both languages
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("language", ["sv", "verilog"])
def test_default_generates_validates_renders(language: str) -> None:
    result = generate("rr-arbiter", {"language": language})
    assert result.code
    validate(build_ir(RrArbiterOptions(language=language)))
    ext = "sv" if language == "sv" else "v"
    assert result.filename == f"rr_arbiter.{ext}"


def test_default_sv_shape() -> None:
    code = generate("rr-arbiter", {}).code
    assert "module rr_arbiter (" in code
    assert "always_ff @(posedge clk) begin" in code
    assert "endmodule" in code
    # default N=4 -> 4-bit req/grant, 2-bit pointer.
    assert "[3:0] req" in code
    assert "[3:0] grant" in code
    assert "[1:0] ptr" in code


def test_verilog_infers_reg_and_plain_always() -> None:
    code = generate("rr-arbiter", {"language": "verilog"}).code
    assert "always @(posedge clk) begin" in code
    assert "reg " in code


# --------------------------------------------------------------------------- #
# structural sanity: two-pass mask logic + pointer update
# --------------------------------------------------------------------------- #


def test_two_pass_mask_logic_present() -> None:
    code = generate("rr-arbiter", {}).code
    # thermometer mask of requests at/above the pointer
    assert "masked_req = req & ({4{1'b1}} << ptr)" in code
    # both fixed-priority encoders (lowest-index-first, ~| reduction idiom)
    assert "masked_gnt" in code
    assert "unmasked_gnt" in code
    assert "~|masked_req" in code
    assert "~|req" in code
    # two-pass selection: masked window else wrap-around
    assert "grant_nxt = (|masked_req) ? masked_gnt : unmasked_gnt" in code
    assert "grant_valid = |grant" in code


def test_pointer_update_present() -> None:
    code = generate("rr-arbiter", {}).code
    assert "if (grant_nxt[0]) begin" in code
    assert "else if (grant_nxt[3]) begin" in code
    assert "ptr <=" in code
    # rotate (default): granting index 0 advances the pointer to 1.
    m = re.search(r"grant_nxt\[0\]\) begin\s*ptr <= 2'd(\d)", code)
    assert m is not None and m.group(1) == "1"
    # wrap-around: granting the top index (3) rotates the pointer back to 0.
    m3 = re.search(r"grant_nxt\[3\]\) begin\s*ptr <= 2'd(\d)", code)
    assert m3 is not None and m3.group(1) == "0"


# --------------------------------------------------------------------------- #
# option effects
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "n,req_range,ptr_range",
    [(2, "[1:0]", "[0:0]"), (8, "[7:0]", "[2:0]"), (16, "[15:0]", "[3:0]")],
)
def test_num_requesters_changes_widths(n: int, req_range: str, ptr_range: str) -> None:
    code = generate("rr-arbiter", {"num_requesters": n}).code
    assert f"{req_range} req" in code
    assert f"{req_range} grant" in code
    assert f"{ptr_range} ptr" in code
    # priority network is unrolled to N bits: the top bit is referenced.
    assert f"req[{n - 1}]" in code


def test_grant_style_registered_flops_grant() -> None:
    code = generate("rr-arbiter", {"grant_style": "registered"}).code
    assert "grant <= grant_nxt;" in code
    assert "assign grant = grant_nxt;" not in code


def test_grant_style_combinational_continuous_grant() -> None:
    code = generate("rr-arbiter", {"grant_style": "combinational"}).code
    assert "assign grant = grant_nxt;" in code
    assert "grant <= grant_nxt;" not in code


def test_hold_grant_changes_pointer_next_value() -> None:
    rotate = generate("rr-arbiter", {"hold_grant": False}).code
    hold = generate("rr-arbiter", {"hold_grant": True}).code
    assert rotate != hold
    # In hold mode, granting index 0 holds the pointer at 0 (no rotation).
    m = re.search(r"grant_nxt\[0\]\) begin\s*ptr <= 2'd(\d)", hold)
    assert m is not None and m.group(1) == "0"
    # granting the top index holds at 3 (rotate would wrap it to 0).
    m3 = re.search(r"grant_nxt\[3\]\) begin\s*ptr <= 2'd(\d)", hold)
    assert m3 is not None and m3.group(1) == "3"


@pytest.mark.parametrize("reset_style", ["sync", "async"])
@pytest.mark.parametrize("reset_polarity", ["active_high", "active_low"])
def test_reset_variants(reset_style: str, reset_polarity: str) -> None:
    code = generate(
        "rr-arbiter",
        {"reset_style": reset_style, "reset_polarity": reset_polarity},
    ).code
    if reset_polarity == "active_low":
        assert "rst_n" in code
        assert "if (!rst_n)" in code
    else:
        assert "if (rst)" in code
    if reset_style == "async":
        assert " or " in code  # reset edge in the sensitivity list
    else:
        assert "always_ff @(posedge clk) begin" in code
    # pointer always resets to 0.
    assert "ptr <= 2'd0;" in code


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #


def test_determinism_byte_identical() -> None:
    opts = {"num_requesters": 8, "grant_style": "combinational"}
    a = generate("rr-arbiter", opts)
    b = generate("rr-arbiter", dict(opts))
    assert a.code == b.code
    assert a.config_hash == b.config_hash


def test_determinism_across_processes() -> None:
    script = (
        "import semicraft_core as sc;"
        "r=sc.generate('rr-arbiter', {'num_requesters':8,'hold_grant':True});"
        "print(r.config_hash);print(repr(r.code))"
    )
    out1 = subprocess.check_output([sys.executable, "-c", script], text=True)
    out2 = subprocess.check_output([sys.executable, "-c", script], text=True)
    assert out1 == out2


def test_config_hash_changes_when_option_changes() -> None:
    a = generate("rr-arbiter", {"num_requesters": 4}).config_hash
    b = generate("rr-arbiter", {"num_requesters": 5}).config_hash
    assert a != b


def test_config_hash_stable_across_dict_key_order() -> None:
    a = generate("rr-arbiter", {"num_requesters": 8, "hold_grant": True}).config_hash
    b = generate("rr-arbiter", {"hold_grant": True, "num_requesters": 8}).config_hash
    assert a == b


def test_config_hash_function_matches_entry_point() -> None:
    opts = RrArbiterOptions(num_requesters=8)
    expected = config_hash("rr-arbiter", opts.model_dump(mode="json"))
    assert generate("rr-arbiter", {"num_requesters": 8}).config_hash == expected


# --------------------------------------------------------------------------- #
# invalid options
# --------------------------------------------------------------------------- #


def test_num_requesters_out_of_range_raises() -> None:
    with pytest.raises(ValidationError):
        generate("rr-arbiter", {"num_requesters": 1})
    with pytest.raises(ValidationError):
        generate("rr-arbiter", {"num_requesters": 17})


def test_bad_grant_style_enum_raises() -> None:
    with pytest.raises(ValidationError):
        generate("rr-arbiter", {"grant_style": "pipelined"})


def test_bad_bool_raises() -> None:
    with pytest.raises(ValidationError):
        generate("rr-arbiter", {"hold_grant": "maybe"})


def test_unknown_field_raises() -> None:
    with pytest.raises(ValidationError):
        generate("rr-arbiter", {"nonsense": 1})


# --------------------------------------------------------------------------- #
# explanation completeness
# --------------------------------------------------------------------------- #


def test_explanation_all_fields_populated() -> None:
    exp = generate("rr-arbiter", {"num_requesters": 8}).explanation
    assert exp.purpose.strip()
    assert len(exp.configuration) >= 3
    assert all(c.strip() for c in exp.configuration)
    assert len(exp.signals) >= 5
    assert all(s.name and s.description for s in exp.signals)
    assert {s.name for s in exp.signals} >= {"clk", "req", "grant", "grant_valid"}
    assert exp.reset_behavior.strip()
    assert exp.enable_behavior is None
    assert exp.assumptions and all(a.strip() for a in exp.assumptions)
    assert exp.limitations and all(limit.strip() for limit in exp.limitations)
    # fairness bound is stated for the chosen N.
    assert "8" in exp.purpose
    # limitations mention the lack of weighting and grant/ack protocol.
    joined = " ".join(exp.limitations).lower()
    assert "weight" in joined
    assert "ack" in joined or "acknowledge" in joined


def test_explanation_reflects_grant_style() -> None:
    reg = generate("rr-arbiter", {"grant_style": "registered"}).explanation
    comb = generate("rr-arbiter", {"grant_style": "combinational"}).explanation
    assert "registered" in " ".join(reg.configuration).lower()
    assert "combinational" in " ".join(comb.configuration).lower()
    # combinational adds a critical-path caveat to the limitations.
    assert any("critical path" in limit.lower() for limit in comb.limitations)


def test_explanation_reflects_hold_grant() -> None:
    hold = generate("rr-arbiter", {"hold_grant": True}).explanation
    rotate = generate("rr-arbiter", {"hold_grant": False}).explanation
    assert "hold" in " ".join(hold.configuration).lower()
    assert "rotate" in " ".join(rotate.configuration).lower()


def test_explanation_reflects_reset_choice() -> None:
    exp = generate(
        "rr-arbiter", {"reset_style": "async", "reset_polarity": "active_high"}
    ).explanation
    assert "asynchronously" in exp.reset_behavior.lower()
    assert "active-high" in exp.reset_behavior.lower()


# --------------------------------------------------------------------------- #
# port_groups shape
# --------------------------------------------------------------------------- #


def test_port_groups_shape() -> None:
    groups = port_groups(RrArbiterOptions())
    assert all(isinstance(g, PortGroup) for g in groups)
    names = [g.name for g in groups]
    assert names == ["Clocking", "Arbitration"]
    all_ports = [p for g in groups for p in g.ports]
    assert set(all_ports) == {"clk", "rst_n", "req", "grant", "grant_valid"}
    for g in groups:
        assert g.description.strip()
        assert g.ports


def test_port_groups_reset_name_tracks_polarity() -> None:
    low = port_groups(RrArbiterOptions(reset_polarity="active_low"))
    high = port_groups(RrArbiterOptions(reset_polarity="active_high"))
    assert "rst_n" in low[0].ports
    assert "rst" in high[0].ports and "rst_n" not in high[0].ports


def test_port_groups_names_match_explanation_signals() -> None:
    opts = RrArbiterOptions()
    exp_names = {s.name for s in generate("rr-arbiter", {}).explanation.signals}
    for group in port_groups(opts):
        for port_name in group.ports:
            assert port_name in exp_names, port_name


# --------------------------------------------------------------------------- #
# tb_spec shape (checks are recipes; NOT executed yet — P2-13)
# --------------------------------------------------------------------------- #


def test_tb_spec_shape() -> None:
    spec = tb_spec(RrArbiterOptions())
    assert isinstance(spec, TbSpec)
    assert spec.clock == "clk"
    assert spec.reset == "rst"
    assert spec.reset_cycles == 2
    assert len(spec.vectors) == 10
    assert all(set(v) == {"req"} for v in spec.vectors)
    assert len(spec.checks) == 3
    assert all(isinstance(c, Check) for c in spec.checks)


def test_tb_spec_latency_tracks_grant_style() -> None:
    reg = tb_spec(RrArbiterOptions(grant_style="registered"))
    comb = tb_spec(RrArbiterOptions(grant_style="combinational"))
    # the "single requester 0 pending" check fires one cycle later when registered.
    reg_cycle = next(c.cycle for c in reg.checks if c.signal == "grant")
    comb_cycle = next(c.cycle for c in comb.checks if c.signal == "grant")
    assert reg_cycle == comb_cycle + 1


def test_tb_spec_signals_reference_real_ports() -> None:
    spec = tb_spec(RrArbiterOptions())
    code = generate("rr-arbiter", {}).code
    assert spec.clock in code and spec.reset in code
    for v in spec.vectors:
        for sig in v:
            assert sig in code
    for check in spec.checks:
        assert check.signal in code


# --------------------------------------------------------------------------- #
# registry / options schema
# --------------------------------------------------------------------------- #


def test_options_model_json_schema_has_descriptions() -> None:
    schema = registry.get("rr-arbiter").options_model.model_json_schema()
    props = schema["properties"]
    assert props["num_requesters"]["description"]
    assert props["grant_style"]["description"]
    assert props["hold_grant"]["description"]
    assert set(props["grant_style"]["enum"]) == {"registered", "combinational"}


def test_generated_ir_is_valid() -> None:
    for opts in (
        RrArbiterOptions(),
        RrArbiterOptions(num_requesters=16, grant_style="combinational"),
        RrArbiterOptions(num_requesters=2, hold_grant=True),
        RrArbiterOptions(reset_style="async", reset_polarity="active_high"),
    ):
        code = render(build_ir(opts), language="sv")
        assert "endmodule" in code


# --------------------------------------------------------------------------- #
# generate_files: rtl + doc
# --------------------------------------------------------------------------- #


def test_generate_files_yields_rtl_and_doc() -> None:
    res = generate_files("rr-arbiter", {})
    kinds = {f.kind for f in res.files}
    assert "rtl" in kinds
    assert "doc" in kinds
