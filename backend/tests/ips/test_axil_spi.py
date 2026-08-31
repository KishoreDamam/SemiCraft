"""AXI4-Lite SPI master: modes, register map, composition (P4-06)."""

from __future__ import annotations

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips.axil_spi import (
    IP,
    AxilSpiOptions,
    _rx_bits,
    bundles,
    register_map,
    tb_spec,
)
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.regblock import axil_ports, write_strobe_name
from semicraft_core.render import StyleOptions, render

_MODES = [(0, 0), (0, 1), (1, 0), (1, 1)]


def _opts(**kw) -> AxilSpiOptions:
    return AxilSpiOptions(**kw)


def _sv(**kw) -> str:
    return render(IP.generate(_opts(**kw)), language="sv", style=StyleOptions(),
                  include_wrapper=True)


def test_satisfies_the_ip_protocol() -> None:
    assert isinstance(IP, IpDef)
    assert IP.kind == "ip"


# --------------------------------------------------------------------------- #
# Clock mode
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("cpol", "cpha"), _MODES)
def test_all_four_modes_generate(cpol: int, cpha: int) -> None:
    sv = _sv(cpol=cpol, cpha=cpha)
    assert "module axil_spi" in sv


@pytest.mark.parametrize("cpol", [0, 1])
def test_cpol_inverts_the_emitted_clock(cpol: int) -> None:
    """sclk_int always idles low and leads with a rising edge; CPOL is a single
    inversion on the way out, so the FSM does not need two edge polarities."""
    sv = _sv(cpol=cpol)
    assert ("assign sclk = !sclk_int;" in sv) is (cpol == 1)
    assert ("assign sclk = sclk_int;" in sv) is (cpol == 0)


@pytest.mark.parametrize("cpha", [0, 1])
def test_cpha_selects_the_sampling_edge_parity(cpha: int) -> None:
    sv = _sv(cpha=cpha)
    assert f"edge_cnt[0] == 1'b{cpha}" in sv


def test_cpha_zero_preloads_the_first_bit_before_the_leading_edge() -> None:
    """With CPHA=0 the leading edge samples rather than shifts, so the MSB has
    to be on the wire already when the transfer starts."""
    assert "mosi <= txdata_data[7];" in _sv(cpha=0)
    assert "mosi <= txdata_data[7];" not in _sv(cpha=1)


@pytest.mark.parametrize(("cpha", "bits"), [(0, 8), (1, 7)])
def test_receive_register_width_follows_the_phase(cpha: int, bits: int) -> None:
    """With CPHA=1 the last sample goes straight into RXDATA, so only seven
    earlier bits are ever re-read — an eighth would be written and never used,
    which the -Wall gate refuses.
    """
    assert _rx_bits(_opts(cpha=cpha)) == bits
    assert f"logic [{bits - 1}:0] rx_shift;" in _sv(cpha=cpha)


# --------------------------------------------------------------------------- #
# Register map and wiring
# --------------------------------------------------------------------------- #


def test_register_map_layout() -> None:
    regmap = register_map(_opts())
    assert [(r.name, r.offset) for r in regmap.registers] == [
        ("STATUS", 0x0), ("CTRL", 0x4), ("TXDATA", 0x8), ("RXDATA", 0xC), ("CLKDIV", 0x10)
    ]


def test_chip_select_is_manual_not_pulsed_by_the_transfer() -> None:
    """Multi-byte transactions need cs_n held across several exchanges; a
    master that deasserted between bytes could not talk to a flash or a
    sensor."""
    sv = _sv()
    assert "assign cs_n = !ctrl_cs_assert;" in sv


def test_transfer_is_triggered_by_the_register_write_strobe() -> None:
    sv = _sv()
    assert f"spi_go <= {write_strobe_name('TXDATA')};" in sv
    assert "if (spi_go) begin" in sv


def test_clkdiv_reset_follows_the_option() -> None:
    assert register_map(_opts(default_divisor=99)).register("CLKDIV").field("div").reset == 99


def test_miso_passes_through_a_synchroniser() -> None:
    sv = _sv(input_sync_stages=3)
    assert "miso_sync0 <= miso;" in sv
    assert "miso_sync2 <= miso_sync1;" in sv


def test_is_one_flat_module() -> None:
    sv = _sv()
    assert sv.count("module ") == 1 and sv.count("endmodule") == 1


def test_only_the_spi_pins_are_added() -> None:
    extra = {p.name for p in IP.generate(_opts()).ports}
    extra -= set(axil_ports()) | {"aclk", "areset"}
    assert extra == {"sclk", "mosi", "miso", "cs_n"}


# --------------------------------------------------------------------------- #
# Testbench recipe
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("cpol", "cpha"), _MODES)
def test_tb_checks_every_transmitted_bit(cpol: int, cpha: int) -> None:
    checks = [c for c in tb_spec(_opts(cpol=cpol, cpha=cpha)).checks if c.signal == "mosi"]
    assert len(checks) == 8


@pytest.mark.parametrize(("cpol", "cpha"), _MODES)
def test_tb_mosi_checks_are_one_full_period_apart(cpol: int, cpha: int) -> None:
    """A full sclk period is two half periods, so consecutive data bits sit
    2*div apart. Checks bunched together would pass against a master with
    entirely wrong bit timing."""
    div = 5
    spec = tb_spec(_opts(cpol=cpol, cpha=cpha, default_divisor=div))
    cycles = sorted(c.cycle for c in spec.checks if c.signal == "mosi")
    gaps = {b - a for a, b in zip(cycles[:-1], cycles[1:], strict=True)}
    assert gaps == {2 * div}


@pytest.mark.parametrize(("cpol", "cpha"), _MODES)
def test_tb_expects_the_idle_clock_level_to_be_cpol(cpol: int, cpha: int) -> None:
    spec = tb_spec(_opts(cpol=cpol, cpha=cpha))
    at_zero = [c for c in spec.checks if c.signal == "sclk" and c.cycle == 0]
    assert at_zero and at_zero[0].expected == cpol


def test_tb_falls_back_to_a_constant_line_when_timing_is_too_tight() -> None:
    """A per-bit miso pattern needs a level to settle through the synchroniser
    inside one half period. When it cannot, the testbench holds the line and
    expects the byte that produces, rather than claiming a resolution the
    configuration does not have."""
    tight = tb_spec(_opts(default_divisor=1, input_sync_stages=4))
    miso_drives = {v["miso"] for v in tight.vectors if "miso" in v}
    assert miso_drives == {1}

    roomy = tb_spec(_opts(default_divisor=8, input_sync_stages=2))
    assert len({v["miso"] for v in roomy.vectors if "miso" in v}) == 2


@pytest.mark.parametrize(
    "options",
    [{}, {"cpha": 1}, {"cpol": 1, "cpha": 1}, {"default_divisor": 1}, {"input_sync_stages": 4}],
    ids=["mode00", "mode01", "mode11", "div1", "sync4"],
)
def test_tb_only_touches_ports_that_exist(options) -> None:
    opts = _opts(**options)
    declared = {p.name for p in IP.generate(opts).ports}
    spec = tb_spec(opts)
    for check in spec.checks:
        assert check.signal in declared
    for vector in spec.vectors:
        for signal in vector:
            assert signal in declared


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("cpol", "cpha"), _MODES)
def test_bundles_match_the_generated_module(cpol: int, cpha: int) -> None:
    opts = _opts(cpol=cpol, cpha=cpha)
    check_bundles_against_module(IP.generate(opts), bundles(opts))


def test_spi_link_is_its_own_bundle() -> None:
    axi, spi = bundles(_opts())
    assert axi.protocol == "axi4-lite" and axi.role == "target"
    assert spi.protocol == "spi" and spi.role == "initiator"
    assert {p.role_name for p in spi.ports} == {"sclk", "mosi", "miso", "cs_n"}


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("axil-spi", {})
    assert [f.kind for f in res.files] == ["rtl", "doc", "tb", "tb", "tb", "doc"]
    # rtl, datasheet, SV TB, cocotb TB, verification scaffold, test plan.
    assert [f.path for f in res.files if f.kind == "tb"][-1].endswith("_checks.sv")
    doc = next(f.text for f in res.files if f.kind == "doc")
    assert "`CLKDIV`" in doc and "`TXDATA`" in doc
