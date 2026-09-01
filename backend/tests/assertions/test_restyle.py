"""Tests for :func:`semicraft_core.assertions.restyle.restyle_spec` (P3-05a).

The bug this closes: ``generate_assertions`` documents that the names it is
handed are "already styled by the caller", but ``generate_tb`` passed a
module's ``TbSpec.assertion_spec`` through untouched. A ``ModuleDef`` can only
write *canonical* names (``tb_spec(opts)`` never sees the render style), so
every emitted property referenced identifiers that need not exist in the
rendered RTL — including at the **default** configuration, where an active-low
reset renders ``rst_n`` while the canonical name is ``rst``.
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
    restyle_spec,
)


def _upper(name: str) -> str:
    return name.upper()


def _prefixed(name: str) -> str:
    return f"u_{name}"


def test_reset_context_signal_is_renamed() -> None:
    spec = AssertionSpec(
        clock="clk",
        items=[ResetKnownValue("q_reset", "q", 0, 8)],
        reset=ResetContext(signal="rst", active_low=True, sync=True),
    )
    out = restyle_spec(spec, lambda n: "rst_n" if n == "rst" else n)
    assert out.reset is not None
    assert out.reset.signal == "rst_n"
    # Polarity/sync carry through untouched.
    assert out.reset.active_low is True
    assert out.reset.sync is True


def test_active_low_default_case_reaches_property_text() -> None:
    """The end-to-end symptom: the guard must name the rendered reset net.

    This is the regression that made wiring assertions unsafe — it bites at the
    default configuration, not only under a custom naming convention.
    """
    spec = AssertionSpec(
        clock="clk",
        items=[Stability("q_hold", "q", "en")],
        reset=ResetContext(signal="rst", active_low=True, sync=True),
    )
    unstyled = generate_assertions(spec)[0]
    assert unstyled.disable_iff is not None
    assert "rst_n" not in unstyled.disable_iff  # the broken behavior

    styled = generate_assertions(
        restyle_spec(spec, lambda n: {"rst": "rst_n"}.get(n, n))
    )[0]
    assert styled.disable_iff is not None
    assert "rst_n" in styled.disable_iff


def test_clock_is_renamed() -> None:
    spec = AssertionSpec(clock="clk", items=[ResetKnownValue("a", "q", 0, 1)])
    assert restyle_spec(spec, _prefixed).clock == "u_clk"


def test_stability_renames_signal_and_enable() -> None:
    spec = AssertionSpec(clock="clk", items=[Stability("s", "data", "en")])
    item = restyle_spec(spec, _prefixed).items[0]
    assert isinstance(item, Stability)
    assert (item.signal, item.enable) == ("u_data", "u_en")


def test_handshake_renames_valid_ready_and_data() -> None:
    spec = AssertionSpec(
        clock="clk", items=[Handshake("h", "valid", "ready", data="payload")]
    )
    item = restyle_spec(spec, _prefixed).items[0]
    assert isinstance(item, Handshake)
    assert (item.valid, item.ready, item.data) == ("u_valid", "u_ready", "u_payload")


def test_handshake_without_data_stays_none() -> None:
    spec = AssertionSpec(clock="clk", items=[Handshake("h", "valid", "ready")])
    item = restyle_spec(spec, _prefixed).items[0]
    assert isinstance(item, Handshake)
    assert item.data is None


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        (OneHot("o", "grant"), "u_grant"),
        (ValueRange("v", "count", 9, 4), "u_count"),
        (NoUnknown("n", "data"), "u_data"),
        (ResetKnownValue("r", "q", 0, 8), "u_q"),
    ],
)
def test_single_signal_families_are_renamed(item, expected: str) -> None:
    spec = AssertionSpec(clock="clk", items=[item])
    assert restyle_spec(spec, _prefixed).items[0].signal == expected


def test_opaque_when_text_is_left_alone() -> None:
    """`when` is raw SV text; renaming inside it would require parsing SV.

    Documented limitation, asserted so the behavior is deliberate rather than
    accidental — a spec author must not rely on `when` being restyled.
    """
    spec = AssertionSpec(
        clock="clk",
        items=[
            OneHot("o", "grant", when="req != 0"),
            NoUnknown("n", "data", when="valid"),
        ],
    )
    out = restyle_spec(spec, _prefixed)
    assert out.items[0].when == "req != 0"
    assert out.items[1].when == "valid"
    # ...while the structured field beside it *is* renamed.
    assert out.items[0].signal == "u_grant"


def test_assertion_names_are_not_renamed() -> None:
    """Names are labels (T8 uniqueness, $fatal text), not signals."""
    spec = AssertionSpec(
        clock="clk",
        items=[ResetKnownValue("q_reset_value", "q", 0, 8)],
        reset=ResetContext(signal="rst", active_low=False, sync=True),
    )
    assert restyle_spec(spec, _upper).items[0].name == "q_reset_value"


def test_identity_rename_is_a_faithful_copy() -> None:
    spec = AssertionSpec(
        clock="clk",
        items=[
            ResetKnownValue("r", "q", 3, 8),
            Stability("s", "q", "en", guarded=False),
            Handshake("h", "v", "r2", data="d"),
            OneHot("o", "g", allow_zero=True, when="x"),
            ValueRange("vr", "c", 9, 4, min_value=2),
            NoUnknown("nu", "d"),
        ],
        reset=ResetContext(signal="rst", active_low=True, sync=False),
    )
    assert generate_assertions(restyle_spec(spec, lambda n: n)) == generate_assertions(spec)


def test_original_spec_is_not_mutated() -> None:
    reset = ResetContext(signal="rst", active_low=True, sync=True)
    spec = AssertionSpec(clock="clk", items=[Stability("s", "q", "en")], reset=reset)
    restyle_spec(spec, _prefixed)
    assert spec.clock == "clk"
    assert spec.reset is reset and spec.reset.signal == "rst"
    assert spec.items[0].signal == "q"


def test_no_reset_stays_none() -> None:
    spec = AssertionSpec(clock="clk", items=[OneHot("o", "grant")])
    assert restyle_spec(spec, _prefixed).reset is None


def test_item_order_is_preserved() -> None:
    spec = AssertionSpec(
        clock="clk",
        items=[
            ResetKnownValue("first", "a", 0, 1),
            OneHot("second", "b"),
            NoUnknown("third", "c"),
        ],
    )
    out = restyle_spec(spec, _prefixed)
    assert [i.name for i in out.items] == ["first", "second", "third"]


def test_restyle_is_deterministic() -> None:
    spec = AssertionSpec(
        clock="clk",
        items=[Stability("s", "q", "en"), Handshake("h", "v", "r", data="d")],
        reset=ResetContext(signal="rst", active_low=True, sync=True),
    )
    assert generate_assertions(restyle_spec(spec, _prefixed)) == generate_assertions(
        restyle_spec(spec, _prefixed)
    )
