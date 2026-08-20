"""``check_bundles_against_module`` and the ``IpDef`` protocol (P4-01).

This is the enforcement that keeps bundle metadata honest: rules B1-B4 in
``ips/contract.py``. Each is checked against a *real* generated module (the
reference IP's), not a stub, so a change in how modules declare ports would
surface here.
"""

from __future__ import annotations

import pytest
from semicraft_core.ips.bundles import BundlePort, PortBundle
from semicraft_core.ips.contract import (
    IpContractError,
    IpDef,
    check_bundles_against_module,
)

from .reference_ip import REFERENCE_IP, ReferenceIpOptions, bundles, generate


@pytest.fixture
def module():
    return generate(ReferenceIpOptions())


def _bundle(name="b", ports=(("addr", "addr"),), **kw) -> PortBundle:
    return PortBundle(
        name=name,
        protocol="native-csr",
        role="target",
        ports=[BundlePort(signal=s, role_name=r) for s, r in ports],
        **kw,
    )


def test_reference_ip_bundles_pass_the_check(module) -> None:
    check_bundles_against_module(module, bundles(ReferenceIpOptions()))


def test_no_bundles_is_fine(module) -> None:
    """An IP with no protocol interface (a bare FIFO) declares none."""
    check_bundles_against_module(module, [])


def test_b1_duplicate_bundle_name(module) -> None:
    with pytest.raises(IpContractError, match="duplicate bundle name 'b'"):
        check_bundles_against_module(module, [_bundle(), _bundle()])


def test_b2_unknown_port_is_rejected(module) -> None:
    with pytest.raises(IpContractError) as exc:
        check_bundles_against_module(module, [_bundle(ports=(("nope", "addr"),))])
    message = str(exc.value)
    assert "declares port 'nope'" in message
    # The message must be enough to fix the declaration without opening the
    # generator, so it lists the ports that do exist.
    assert "its ports are:" in message
    assert "wdata" in message


def test_b3_a_port_belongs_to_at_most_one_bundle(module) -> None:
    with pytest.raises(IpContractError, match="claimed by both bundle 'a' and bundle 'b'"):
        check_bundles_against_module(
            module, [_bundle(name="a"), _bundle(name="b", ports=(("addr", "x"),))]
        )


def test_b4_unknown_clock_or_reset_is_rejected(module) -> None:
    with pytest.raises(IpContractError, match="references clock 'nope'"):
        check_bundles_against_module(module, [_bundle(clock="nope")])
    with pytest.raises(IpContractError, match="references reset 'nope'"):
        check_bundles_against_module(module, [_bundle(reset="nope")])


def test_a_port_dropped_by_an_option_is_caught(module) -> None:
    """The realistic failure: an option removes a port but not its bundle entry.

    ``status_busy`` exists only when ``status_register`` is set, so a bundle
    that named it would be valid in one configuration and broken in another —
    exactly the kind of defect that survives a defaults-only test suite.
    """
    narrow = generate(ReferenceIpOptions(status_register=False))
    bundle = _bundle(ports=(("status_busy", "busy"),))
    check_bundles_against_module(module, [bundle])  # fine when the port exists
    with pytest.raises(IpContractError, match="declares port 'status_busy'"):
        check_bundles_against_module(narrow, [bundle])


# --------------------------------------------------------------------------- #
# Protocol conformance
# --------------------------------------------------------------------------- #


def test_reference_ip_satisfies_the_ip_protocol() -> None:
    assert isinstance(REFERENCE_IP, IpDef)


def test_reference_ip_satisfies_the_module_protocol_too() -> None:
    """An IP is a strict superset of a module, so the whole Phase-2/3 pipeline
    applies to it unchanged."""
    from semicraft_core.modules.contract import ModuleDef

    assert isinstance(REFERENCE_IP, ModuleDef)


def test_a_module_is_not_an_ip() -> None:
    """The extra two methods are what distinguish the contracts."""
    from semicraft_core.modules import gray_counter

    assert not isinstance(gray_counter.MODULE, IpDef)


def test_reference_ip_declares_kind_ip() -> None:
    assert REFERENCE_IP.kind == "ip"
