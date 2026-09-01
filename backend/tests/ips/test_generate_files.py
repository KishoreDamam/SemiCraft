"""End-to-end: an IP through the registry and the whole file pipeline (P4-01).

The claim P4-01 makes is that an IP is a module plus metadata, so nothing in
the Phase-2/Phase-3 pipeline needs to know about IPs. These tests check that
claim by running the reference IP through ``generate_files``.

The claim has been *narrowed*, not broken, as Phase 4 went on: an IP no longer
gets the identical file set a module gets, it gets that set plus artifacts only
an IP has — two datasheet sections (P4-01), a verification scaffold when it
attaches one (P4-09), a timing diagram (P4-10) and an example instantiation
(P4-11). What still holds, and what these tests assert, is that every file a
module emits is still emitted, in the same relative order, by the same code
path.
"""

from __future__ import annotations

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips.contract import IpContractError
from semicraft_core.snippets import registry

from .reference_ip import REFERENCE_IP


def _files(registered_ip, options=None):
    return generate_files(registered_ip.id, options or {})


def _of_kind(res, kind: str) -> list[str]:
    return [f.text for f in res.files if f.kind == kind]


def test_ip_produces_the_module_file_set_plus_its_own(registered_ip) -> None:
    """An IP is a module plus IP-specific artifacts, in a pinned order.

    This test used to assert an IP produced *exactly* a module's file set. That
    stopped being true as Phase 4 added artifacts only an IP has, and the
    honest statement now is the containment one: every file a module emits is
    here, in the same relative order, plus the example instantiation (P4-11).

    The reference IP attaches no ``verification_spec``, so it gets no
    ``_checks.sv`` — which is the point of checking the reference IP as well as
    the catalog: the scaffold is opt-in, and the example is not. An example is
    derivable from any IP's ports, groups and bundles, so a new IP should not
    have to remember to ask for one.
    """
    res = _files(registered_ip)
    assert [f.kind for f in res.files] == ["rtl", "doc", "tb", "tb", "rtl", "doc"]
    assert [f.path for f in res.files] == [
        "csr_block.sv",
        "csr_block.md",
        "csr_block_tb.sv",
        "test_csr_block.py",
        "csr_block_example.sv",
        "csr_block_testplan.md",
    ]

    module_files = [f.path for f in generate_files("gray-counter", {}).files]
    suffixes = [p.split("gray_counter")[-1] for p in module_files]
    ip_suffixes = [
        f.path.split("csr_block")[-1]
        for f in res.files
        if not f.path.endswith("_example.sv")
    ]
    assert suffixes == [s for s in ip_suffixes if s in suffixes], (
        "an IP no longer emits the module file set in the module's own order"
    )


def test_ip_datasheet_carries_both_interface_sections(registered_ip) -> None:
    doc = _of_kind(_files(registered_ip), "doc")[0]
    assert "## Register map" in doc
    assert "## Bus interfaces" in doc
    # Between the port table and the configuration list: the whole interface
    # surface stays together.
    assert doc.index("## Ports") < doc.index("## Register map")
    assert doc.index("## Bus interfaces") < doc.index("## Configuration")


def test_module_datasheet_gains_no_ip_sections() -> None:
    """The IP path must not leak into the module path."""
    doc = _of_kind(generate_files("gray-counter", {}), "doc")[0]
    assert "## Register map" not in doc
    assert "## Bus interfaces" not in doc


def test_register_map_follows_the_options(registered_ip) -> None:
    with_status = _of_kind(_files(registered_ip), "doc")[0]
    without = _of_kind(_files(registered_ip, {"status_register": False}), "doc")[0]
    assert "`STATUS`" in with_status
    assert "`STATUS`" not in without
    assert "`CTRL`" in without


def test_bundle_ports_are_named_as_the_rtl_declares_them(registered_ip) -> None:
    """The P3-05a lesson applied to bundles: metadata is written canonically,
    so it must be restyled before anyone reads it.

    Under a prefix + camelCase style the RTL declares ``p_wrEn``; a datasheet
    that still said ``wr_en`` would document a port that does not exist.
    """
    options = {"naming": {"convention": "camel", "prefix": "p_"}}
    res = _files(registered_ip, options)
    rtl = _of_kind(res, "rtl")[0]
    doc = _of_kind(res, "doc")[0]
    section = doc[doc.index("## Bus interfaces") :]

    for rendered in ("p_addr", "p_wrEn", "p_wdata", "p_rdEn", "p_rdata"):
        assert rendered in rtl
        assert f"| `{rendered}` |" in section
    assert "Timing: clocked by `p_clk`, reset by `p_rst_n`." in section
    # Role names stay protocol vocabulary regardless of style.
    assert "| `wr_en` | `p_wrEn` |" in section


def test_active_low_reset_is_named_rst_n_in_the_bundle_section(registered_ip) -> None:
    """Default options already exercise the renaming: active-low is the default."""
    doc = _of_kind(_files(registered_ip), "doc")[0]
    section = doc[doc.index("## Bus interfaces") :]
    assert "reset by `rst_n`" in section


def test_generation_fails_when_a_bundle_names_a_port_that_is_gone(
    registered_ip, monkeypatch
) -> None:
    """The cross-check runs during generation, not only in a unit test.

    A bundle entry left behind after an option removed its port must break
    generation loudly rather than produce a datasheet documenting a signal
    nobody emits.
    """
    from semicraft_core.ips.bundles import BundlePort, PortBundle

    stale = PortBundle(
        name="s_csr",
        protocol="native-csr",
        role="target",
        ports=[BundlePort(signal="status_busy", role_name="busy")],
    )
    monkeypatch.setattr(
        type(REFERENCE_IP), "bundles", lambda self, opts: [stale], raising=True
    )
    with pytest.raises(IpContractError, match="declares port 'status_busy'"):
        _files(registered_ip, {"status_register": False})


def test_ip_generation_is_deterministic(registered_ip) -> None:
    a = _files(registered_ip)
    b = _files(registered_ip)
    assert [(f.path, f.text) for f in a.files] == [(f.path, f.text) for f in b.files]
    assert a.config_hash == b.config_hash


def test_both_languages_generate(registered_ip) -> None:
    sv = _files(registered_ip, {"language": "sv"})
    v = _files(registered_ip, {"language": "verilog"})
    assert sv.files[0].path == "csr_block.sv"
    assert v.files[0].path == "csr_block.v"
    assert "always_ff" in sv.files[0].text
    assert "always_ff" not in v.files[0].text


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #


def test_registry_routes_the_ip_to_kind_ip(registered_ip) -> None:
    ids = [item.id for item in registry.by_kind("ip")]
    assert registered_ip.id in ids
    assert registered_ip.id not in [item.id for item in registry.by_kind("module")]


#: IPs the catalog actually ships. Pinned so that adding or removing one is a
#: deliberate edit rather than a silent catalog change — this list started
#: empty at P4-01, and P4-02 adding the first entry is what made the guard
#: earn its place.
SHIPPED_IPS = [
    "axil-gpio",
    "axil-i2c",
    "axil-intc",
    "axil-regblock",
    "axil-spi",
    "axil-timer",
    "axil-uart",
    "sync-fifo",
    "sync-ram",
]


def test_catalog_ships_exactly_the_expected_ips() -> None:
    assert sorted(item.id for item in registry.by_kind("ip")) == sorted(SHIPPED_IPS)


def test_ips_package_is_discovered_without_a_registry_edit() -> None:
    """IP files are found structurally; the package's helper modules are not.

    ``regmap``/``bundles``/``doc``/``contract`` hold models and renderers, not
    catalog items, so discovery must skip them by name and still pick up every
    real IP with no registry edit.
    """
    import semicraft_core.ips as ips_pkg
    from semicraft_core.snippets.registry import _IP_SKIP_MODULES, _discover_package

    found: dict = {}
    _discover_package(ips_pkg, found, skip=_IP_SKIP_MODULES)
    assert sorted(found) == sorted(SHIPPED_IPS)


def test_api_maps_a_contract_violation_to_500(registered_ip, monkeypatch) -> None:
    """`IpContractError` is a generator bug, so the v2 endpoint must return the
    same 500 envelope invalid IR gets — not escape as an unhandled exception.

    Without the explicit handler this raised straight out of the route: still a
    500 in production, but with a different body and a traceback, and the
    docstring claiming otherwise would have been wrong.
    """
    from api.main import app
    from fastapi.testclient import TestClient
    from semicraft_core.ips.bundles import BundlePort, PortBundle

    stale = PortBundle(
        name="s_csr",
        protocol="native-csr",
        role="target",
        ports=[BundlePort(signal="not_a_port", role_name="addr")],
    )
    monkeypatch.setattr(type(REFERENCE_IP), "bundles", lambda self, opts: [stale])

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        "/api/v2/generate", json={"item_id": registered_ip.id, "options": {}}
    )
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal error generating code."}
