"""Assertion generator (P3-05) coverage.

Exact-text expectations per template family, determinism (same spec -> identical
output), name uniqueness, and ``disable iff`` guard composition across the four
reset combinations (sync/async x active-high/low). Every generated tuple is fed
through ``validate_tb`` inside a real ``TbModule`` to prove the T8 semantics
hold (unique names, non-empty text, resolvable clock).
"""

from __future__ import annotations

import pytest
from semicraft_core.assertions import (
    AssertionSpec,
    Handshake,
    NoUnknown,
    OneHot,
    ResetContext,
    ResetKnownValue,
    Stability,
    ValueRange,
    generate_assertions,
)
from semicraft_core.tb.nodes import (
    ClockGen,
    Decl,
    DutInstance,
    Finish,
    Initial,
    TbModule,
)
from semicraft_core.tb.validate import validate_tb

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

RST_N = ResetContext(signal="rst_n", active_low=True, sync=False)
RST = ResetContext(signal="rst", active_low=False, sync=False)


def _guard_map(props) -> dict[str, str | None]:
    return {p.name: p.disable_iff for p in props}


def _text_map(props) -> dict[str, str]:
    return {p.name: p.property_text for p in props}


def _wrap_in_tb(props) -> TbModule:
    """Embed generated properties in a minimal valid TbModule for validate_tb.

    The clock net (``clk``) and both reset nets are declared so the T8 clock
    resolution passes; the Initial has a lone ``$finish`` to satisfy T6.
    """
    return TbModule(
        name="dut_tb",
        decls=[Decl("clk", 1), Decl("rst_n", 1), Decl("rst", 1)],
        clock=ClockGen("clk"),
        dut=DutInstance("dut", "dut_i", (("clk", "clk"),)),
        initial=Initial([Finish()]),
        asserts=props,
    )


# --------------------------------------------------------------------------- #
# exact-text expectations per family
# --------------------------------------------------------------------------- #


def test_reset_known_value_active_low() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[ResetKnownValue("done_reset", "done", 0, 1)],
    )
    (p,) = generate_assertions(spec)
    assert p.name == "done_reset"
    assert p.clock == "clk"
    assert p.property_text == "$rose(rst_n) |-> done == 1'd0"
    # reset-behaviour assertion is never disabled by reset
    assert p.disable_iff is None


def test_reset_known_value_active_high() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST,
        items=[ResetKnownValue("count_reset", "count", 0, 8)],
    )
    (p,) = generate_assertions(spec)
    assert p.property_text == "$fell(rst) |-> count == 8'd0"
    assert p.disable_iff is None


def test_reset_known_value_without_reset_raises() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=None,
        items=[ResetKnownValue("done_reset", "done", 0, 1)],
    )
    with pytest.raises(ValueError, match="requires a reset context"):
        generate_assertions(spec)


def test_stability() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[Stability("data_hold", "data_out", "en")],
    )
    (p,) = generate_assertions(spec)
    assert p.property_text == "!en |=> $stable(data_out)"
    assert p.disable_iff == "!rst_n"


def test_handshake_valid_only() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[Handshake("hs", "valid", "ready")],
    )
    (p,) = generate_assertions(spec)
    assert p.name == "hs"
    assert p.property_text == "valid && !ready |=> valid"
    assert p.disable_iff == "!rst_n"


def test_handshake_with_data_expands_to_two() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[Handshake("hs", "valid", "ready", data="data")],
    )
    props = generate_assertions(spec)
    assert [p.name for p in props] == ["hs", "hs_data"]
    texts = _text_map(props)
    assert texts["hs"] == "valid && !ready |=> valid"
    assert texts["hs_data"] == "valid && !ready |=> $stable(data)"
    # both share the same reset guard
    assert {p.disable_iff for p in props} == {"!rst_n"}


def test_onehot() -> None:
    spec = AssertionSpec(
        clock="clk", reset=RST_N, items=[OneHot("state_oh", "state")]
    )
    (p,) = generate_assertions(spec)
    assert p.property_text == "$onehot(state)"
    assert p.disable_iff == "!rst_n"


def test_onehot0_with_when() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[OneHot("grant_oh0", "grant", allow_zero=True, when="grant_valid")],
    )
    (p,) = generate_assertions(spec)
    assert p.property_text == "grant_valid |-> $onehot0(grant)"


def test_value_range_max_only() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[ValueRange("ptr_range", "ptr", max_value=7, width=3)],
    )
    (p,) = generate_assertions(spec)
    assert p.property_text == "ptr <= 3'd7"


def test_value_range_min_and_max() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[ValueRange("ptr_range", "ptr", max_value=7, width=4, min_value=2)],
    )
    (p,) = generate_assertions(spec)
    assert p.property_text == "ptr >= 4'd2 && ptr <= 4'd7"


def test_no_unknown_bare() -> None:
    spec = AssertionSpec(
        clock="clk", reset=RST_N, items=[NoUnknown("data_known", "data_out")]
    )
    (p,) = generate_assertions(spec)
    assert p.property_text == "!$isunknown(data_out)"


def test_no_unknown_with_when() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[NoUnknown("data_known", "data_out", when="valid")],
    )
    (p,) = generate_assertions(spec)
    assert p.property_text == "valid |-> !$isunknown(data_out)"


# --------------------------------------------------------------------------- #
# disable-iff guard composition across sync/async x active-high/low
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("sync", [True, False])
@pytest.mark.parametrize(
    ("active_low", "signal", "expected_guard"),
    [(True, "rst_n", "!rst_n"), (False, "rst", "rst")],
)
def test_guard_polarity_is_sync_invariant(
    sync: bool, active_low: bool, signal: str, expected_guard: str
) -> None:
    reset = ResetContext(signal=signal, active_low=active_low, sync=sync)
    spec = AssertionSpec(
        clock="clk", reset=reset, items=[Stability("s", "sig", "en")]
    )
    (p,) = generate_assertions(spec)
    # guard is polarity-determined and identical for sync and async resets
    assert p.disable_iff == expected_guard


def test_no_reset_means_no_guard() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=None,
        items=[
            Stability("s", "sig", "en"),
            Handshake("hs", "valid", "ready", data="data"),
            OneHot("oh", "state"),
        ],
    )
    props = generate_assertions(spec)
    assert all(p.disable_iff is None for p in props)


def test_item_can_opt_out_of_guard() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[
            Stability("guarded", "sig", "en"),
            Stability("unguarded", "sig2", "en", guarded=False),
        ],
    )
    guards = _guard_map(generate_assertions(spec))
    assert guards == {"guarded": "!rst_n", "unguarded": None}


def test_reset_deassert_edge_active_high_vs_low() -> None:
    lo = generate_assertions(
        AssertionSpec("clk", [ResetKnownValue("r", "s", 0, 1)], RST_N)
    )[0]
    hi = generate_assertions(
        AssertionSpec("clk", [ResetKnownValue("r", "s", 0, 1)], RST)
    )[0]
    assert lo.property_text.startswith("$rose(rst_n)")
    assert hi.property_text.startswith("$fell(rst)")


# --------------------------------------------------------------------------- #
# determinism, ordering, name uniqueness, T8 validity
# --------------------------------------------------------------------------- #


def _full_spec() -> AssertionSpec:
    return AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[
            ResetKnownValue("done_reset", "done", 0, 1),
            Stability("data_hold", "data_out", "en"),
            Handshake("hs", "valid", "ready", data="data_out"),
            OneHot("grant_oh0", "grant", allow_zero=True, when="grant_valid"),
            ValueRange("ptr_range", "ptr", max_value=7, width=3),
            NoUnknown("data_known", "data_out", when="valid"),
        ],
    )


def test_determinism_same_spec_same_output() -> None:
    a = generate_assertions(_full_spec())
    b = generate_assertions(_full_spec())
    assert a == b
    # and structurally: same names, texts, clocks, guards in the same order
    assert [(p.name, p.property_text, p.clock, p.disable_iff) for p in a] == [
        (p.name, p.property_text, p.clock, p.disable_iff) for p in b
    ]


def test_output_order_follows_item_order() -> None:
    props = generate_assertions(_full_spec())
    assert [p.name for p in props] == [
        "done_reset",
        "data_hold",
        "hs",
        "hs_data",
        "grant_oh0",
        "ptr_range",
        "data_known",
    ]


def test_names_are_unique() -> None:
    props = generate_assertions(_full_spec())
    names = [p.name for p in props]
    assert len(names) == len(set(names))


def test_duplicate_names_rejected() -> None:
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[
            Stability("dup", "a", "en"),
            OneHot("dup", "b"),
        ],
    )
    with pytest.raises(ValueError, match="duplicate assertion name: 'dup'"):
        generate_assertions(spec)


def test_handshake_data_suffix_collision_rejected() -> None:
    # a Handshake('hs', data=...) emits 'hs_data'; an explicit 'hs_data' collides
    spec = AssertionSpec(
        clock="clk",
        reset=RST_N,
        items=[
            Handshake("hs", "valid", "ready", data="d"),
            OneHot("hs_data", "state"),
        ],
    )
    with pytest.raises(ValueError, match="duplicate assertion name: 'hs_data'"):
        generate_assertions(spec)


def test_generated_properties_pass_validate_tb_t8() -> None:
    props = generate_assertions(_full_spec())
    # must not raise: unique names, non-empty text, clock resolves to the ClockGen
    validate_tb(_wrap_in_tb(props))


def test_empty_spec_yields_empty_tuple() -> None:
    props = generate_assertions(AssertionSpec("clk", [], RST_N))
    assert props == ()
    validate_tb(_wrap_in_tb(props))


def test_property_text_never_empty() -> None:
    props = generate_assertions(_full_spec())
    assert all(p.property_text.strip() for p in props)
