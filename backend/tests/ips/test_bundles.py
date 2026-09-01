"""Port-bundle model + restyle (P4-01).

Bundles are the machine-consumable half of the IP contract, so the tests here
lean on the two things that make them safe: strict construction validation,
and the restyle step that keeps declared names in step with rendered ones.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from semicraft_core.ips.bundles import BundlePort, PortBundle, restyle_bundles


def _bundle(**kw) -> PortBundle:
    kw.setdefault("name", "s_csr")
    kw.setdefault("protocol", "native-csr")
    kw.setdefault("role", "target")
    kw.setdefault("ports", [BundlePort(signal="addr", role_name="addr")])
    return PortBundle(**kw)


def test_bundle_name_must_be_lower_snake() -> None:
    with pytest.raises(ValidationError, match="lower_snake_case"):
        _bundle(name="S_AXIL")
    _bundle(name="s_axil_0")


@pytest.mark.parametrize("protocol", ["axi4-lite", "uart", "spi", "apb3", "i2c"])
def test_protocol_accepts_conventional_spellings(protocol: str) -> None:
    assert _bundle(protocol=protocol).protocol == protocol


@pytest.mark.parametrize("protocol", ["AXI4-Lite", "axi_lite", "-axi", "axi--lite"])
def test_protocol_rejects_other_spellings(protocol: str) -> None:
    with pytest.raises(ValidationError, match="lowercase alphanumeric"):
        _bundle(protocol=protocol)


def test_role_is_restricted_to_the_two_sides() -> None:
    _bundle(role="initiator")
    with pytest.raises(ValidationError):
        _bundle(role="monitor")


def test_bundle_must_declare_ports() -> None:
    with pytest.raises(ValidationError, match="declares no ports"):
        _bundle(ports=[])


def test_bundle_rejects_duplicate_signal_and_role() -> None:
    with pytest.raises(ValidationError, match="duplicate signal"):
        _bundle(
            ports=[
                BundlePort(signal="a", role_name="x"),
                BundlePort(signal="a", role_name="y"),
            ]
        )
    with pytest.raises(ValidationError, match="duplicate role_name"):
        _bundle(
            ports=[
                BundlePort(signal="a", role_name="x"),
                BundlePort(signal="b", role_name="x"),
            ]
        )


def test_role_name_must_be_lower_snake() -> None:
    with pytest.raises(ValidationError, match="lower_snake_case"):
        BundlePort(signal="addr", role_name="AWVALID")


def test_clock_and_reset_may_not_also_be_member_ports() -> None:
    """Clocks are referenced so several bundles can share one; owning them
    would collide with the one-bundle-per-port rule."""
    ports = [BundlePort(signal="clk", role_name="aclk")]
    with pytest.raises(ValidationError, match="clock 'clk' is also listed"):
        _bundle(ports=ports, clock="clk")
    with pytest.raises(ValidationError, match="reset 'clk' is also listed"):
        _bundle(ports=ports, reset="clk")


def test_two_bundles_may_share_a_clock() -> None:
    a = _bundle(name="s_a", clock="clk", reset="rst")
    b = _bundle(name="s_b", clock="clk", reset="rst")
    assert a.clock == b.clock == "clk"


def test_signals_and_by_role() -> None:
    b = _bundle(
        ports=[
            BundlePort(signal="awvalid_i", role_name="awvalid"),
            BundlePort(signal="awready_o", role_name="awready"),
        ]
    )
    assert b.signals == ["awvalid_i", "awready_o"]
    assert b.by_role("awready").signal == "awready_o"
    with pytest.raises(KeyError, match="no port with role 'wvalid'"):
        b.by_role("wvalid")


# --------------------------------------------------------------------------- #
# restyle
# --------------------------------------------------------------------------- #


def test_restyle_rewrites_signals_clock_and_reset() -> None:
    b = _bundle(
        ports=[
            BundlePort(signal="addr", role_name="addr"),
            BundlePort(signal="wr_en", role_name="wr_en"),
        ],
        clock="clk",
        reset="rst",
    )
    rename = {"addr": "p_addr", "wr_en": "p_wrEn", "clk": "p_clk", "rst": "p_rst_n"}
    (out,) = restyle_bundles([b], rename)
    assert out.signals == ["p_addr", "p_wrEn"]
    assert (out.clock, out.reset) == ("p_clk", "p_rst_n")


def test_restyle_leaves_role_names_alone() -> None:
    """Role names are protocol vocabulary, not RTL identifiers.

    Renaming them would break the very matching bundles exist for: two IPs
    with different port prefixes must still agree that ``awvalid`` is
    ``awvalid``.
    """
    b = _bundle(ports=[BundlePort(signal="awvalid", role_name="awvalid")])
    (out,) = restyle_bundles([b], {"awvalid": "p_awvalid"})
    assert out.ports[0].signal == "p_awvalid"
    assert out.ports[0].role_name == "awvalid"


def test_restyle_passes_unknown_names_through() -> None:
    b = _bundle(clock="clk")
    (out,) = restyle_bundles([b], {})
    assert (out.signals, out.clock, out.reset) == (["addr"], "clk", None)


def test_restyle_does_not_mutate_the_input() -> None:
    b = _bundle(clock="clk")
    restyle_bundles([b], {"addr": "x", "clk": "y"})
    assert (b.signals, b.clock) == (["addr"], "clk")


def test_ports_is_a_tuple() -> None:
    assert isinstance(_bundle().ports, tuple)


def test_restyle_output_keeps_the_tuple_type() -> None:
    """``model_copy`` skips validation, so the tuple must be built explicitly —
    otherwise a restyled bundle would silently carry a list."""
    (out,) = restyle_bundles([_bundle()], {"addr": "p_addr"})
    assert isinstance(out.ports, tuple)
