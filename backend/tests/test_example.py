"""Example instantiations for IPs (P4-11).

The lint gate in ``backend/tests/golden/test_example_lint.py`` is what proves an
example *compiles*. These tests cover what linting cannot see: that every port
is connected exactly once, that the grouping and bundle annotations come from
the IP's own metadata, and that the naming style reaches the connections.
"""

from __future__ import annotations

import re

import pytest
from semicraft_core.example import example_filename, ungrouped_ports
from semicraft_core.generate import _style_from_options, generate_files
from semicraft_core.render.style import build_name_map
from semicraft_core.snippets import registry
from semicraft_core.version import VERSION

IP_IDS = [
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

_CONNECTION = re.compile(r"^\s+\.(\w+)\s*\((\w+)\)", re.MULTILINE)


def _example(item_id: str, options: dict | None = None) -> str:
    res = generate_files(item_id, options or {})
    return next(f.text for f in res.files if "_example." in f.path)


# --------------------------------------------------------------------------- #
# Emission
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_every_ip_emits_an_example(item_id: str) -> None:
    res = generate_files(item_id, {})
    examples = [f for f in res.files if "_example." in f.path]
    assert len(examples) == 1
    assert examples[0].kind == "rtl"


def test_the_primary_rtl_still_resolves_first() -> None:
    """A second `rtl`-kind file must not break the long-standing
    `next(f for f in files if f.kind == "rtl")` lookup every gate uses."""
    res = generate_files("axil-gpio", {})
    first = next(f for f in res.files if f.kind == "rtl")
    assert first.path == "axil_gpio.sv"


def test_modules_get_no_example() -> None:
    res = generate_files("clock-divider", {})
    assert not [f for f in res.files if "_example." in f.path]


@pytest.mark.parametrize("language,ext", [("sv", "sv"), ("verilog", "v")])
def test_filename_follows_the_language(language: str, ext: str) -> None:
    assert example_filename("axil_gpio", language) == f"axil_gpio_example.{ext}"
    res = generate_files("axil-gpio", {"language": language})
    assert any(f.path == f"axil_gpio_example.{ext}" for f in res.files)


def test_verilog_example_declares_nets_not_registers() -> None:
    """Every port of the wrapper is driven by (or drives) the instance, so
    nothing is procedurally assigned and nothing may be `reg` — unlike the DUT,
    whose registered outputs are."""
    text = _example("axil-gpio", {"language": "verilog"})
    assert " reg " not in text
    assert " wire " in text
    assert " logic " not in text


# --------------------------------------------------------------------------- #
# Connections
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_every_port_is_connected_exactly_once(item_id: str) -> None:
    """The failure a pass-through wrapper can still have: a dropped or repeated
    connection. Verilator would catch a repeat, but a *missing* one just leaves
    an input floating, which lints clean."""
    item = registry.get(item_id)
    opts = item.options_model.model_validate({})
    module = item.generate(opts)
    names_map = build_name_map(module, _style_from_options(opts))
    # Compare against *rendered* names: an active-low reset is canonically
    # `rst`/`areset` and renders as `rst_n`/`areset_n`, and the instantiation
    # necessarily connects the rendered net.
    expected = {names_map.get(p.name, p.name) for p in module.ports}

    connected = _CONNECTION.findall(_example(item_id))
    names = [port for port, _net in connected]
    assert len(names) == len(set(names)), f"{item_id}: a port is connected twice"
    assert set(names) == expected, (
        f"{item_id}: connected ports do not match the module's rendered ports"
    )


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_each_connection_is_a_pass_through(item_id: str) -> None:
    for port, net in _CONNECTION.findall(_example(item_id)):
        assert port == net, f"{item_id}: .{port}({net}) is not a pass-through"


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_port_groups_cover_every_port(item_id: str) -> None:
    """The emitter handles ungrouped ports rather than dropping them, but an IP
    reaching that path means its metadata has fallen behind its ports — and the
    datasheet's port table would be incomplete too."""
    item = registry.get(item_id)
    opts = item.options_model.model_validate({})
    missing = ungrouped_ports(item.generate(opts), list(item.port_groups(opts)))
    assert not missing, f"{item_id}: port_groups omits {missing}"


# --------------------------------------------------------------------------- #
# Metadata-derived commentary
# --------------------------------------------------------------------------- #


def test_group_names_and_bundle_annotations_come_from_metadata() -> None:
    text = _example("axil-gpio")
    assert "// Clocking" in text
    assert "// Pins" in text
    assert "// AXI4-Lite slave (bundle `s_axil`, axi4-lite target)" in text


def test_a_non_axi_bundle_is_annotated_with_its_own_protocol() -> None:
    """The annotation is read from the IP's bundle metadata, not assumed to be
    AXI: `sync-ram` declares a `sram-single` bundle and must say so."""
    text = _example("sync-ram")
    assert "(bundle `mem`, sram-single " in text


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_banner_carries_the_version_and_config_hash(item_id: str) -> None:
    text = _example(item_id)
    assert f"// SemiCraft v{VERSION}" in text
    assert re.search(r"config hash: [0-9a-f]{12}\)", text), item_id


def test_naming_style_reaches_the_connections() -> None:
    text = _example("axil-gpio", {"naming": {"convention": "camel", "prefix": "p_"}})
    assert ".p_aclk" in text
    assert ".aclk " not in text


@pytest.mark.parametrize("item_id", IP_IDS, ids=IP_IDS)
def test_example_is_deterministic(item_id: str) -> None:
    assert _example(item_id) == _example(item_id)
