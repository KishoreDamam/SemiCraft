"""AXI4-Lite UART: register map, composition, framing metadata (P4-05b)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from semicraft_core.generate import generate_files
from semicraft_core.ips.axil_uart import (
    IP,
    AxilUartOptions,
    _tx_frame_bits,
    bundles,
    register_map,
    tb_spec,
)
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.regblock import axil_ports, write_strobe_name
from semicraft_core.render import StyleOptions, render


def _opts(**kw) -> AxilUartOptions:
    return AxilUartOptions(**kw)


def _sv(**kw) -> str:
    return render(IP.generate(_opts(**kw)), language="sv", style=StyleOptions(),
                  include_wrapper=True)


def test_satisfies_the_ip_protocol() -> None:
    assert isinstance(IP, IpDef)
    assert IP.kind == "ip"


def test_divisor_below_two_is_rejected() -> None:
    """The receiver waits half a divisor to reach mid-bit, and half of one is
    zero — so 1 is not a usable rate, it is a broken receiver."""
    with pytest.raises(ValidationError):
        _opts(default_divisor=1)
    assert _opts(default_divisor=2).default_divisor == 2


# --------------------------------------------------------------------------- #
# Register map
# --------------------------------------------------------------------------- #


def test_register_map_layout() -> None:
    regmap = register_map(_opts())
    assert [(r.name, r.offset) for r in regmap.registers] == [
        ("STATUS", 0x0), ("TXDATA", 0x4), ("RXDATA", 0x8), ("BAUDDIV", 0xC)
    ]


def test_status_flags_are_write_one_to_clear() -> None:
    """Not read-to-clear: the register block has no read-side effect, and
    adding an access type for a single user was not worth it."""
    status = register_map(_opts()).register("STATUS")
    assert status.field("tx_busy").access == "ro"
    for flag in ("rx_valid", "rx_overrun", "frame_error"):
        assert status.field(flag).access == "w1c"


def test_txdata_is_write_only_and_rxdata_read_only() -> None:
    regmap = register_map(_opts())
    assert regmap.register("TXDATA").field("data").access == "wo"
    assert regmap.register("RXDATA").field("data").access == "ro"


def test_baud_divisor_reset_follows_the_option() -> None:
    assert register_map(_opts(default_divisor=434)).register("BAUDDIV").field("div").reset == 434


# --------------------------------------------------------------------------- #
# Composition
# --------------------------------------------------------------------------- #


def test_is_one_flat_module() -> None:
    sv = _sv()
    assert sv.count("module ") == 1 and sv.count("endmodule") == 1


def test_only_the_serial_pins_are_added() -> None:
    extra = {p.name for p in IP.generate(_opts()).ports}
    extra -= set(axil_ports()) | {"aclk", "areset"}
    assert extra == {"uart_rx", "uart_tx"}


def test_transmit_is_triggered_by_the_register_write_strobe() -> None:
    """Storage alone cannot say *when* a write happened; the block already
    computes a one-cycle strobe, so the transmitter uses it."""
    sv = _sv()
    strobe = write_strobe_name("TXDATA")
    assert f"tx_go <= {strobe};" in sv
    assert "if (tx_go) begin" in sv


def test_transmit_uses_the_delayed_strobe_not_the_raw_one() -> None:
    """txdata_data only takes the new byte on the same edge the strobe is
    sampled, so starting on the raw strobe would transmit the previous byte."""
    sv = _sv()
    # The renderer emits minimal-width constants, so the IDLE arm is `2'b0:`
    # and the START arm `2'b1:`.
    idle_arm = sv[sv.index("2'b0: begin") :].split("2'b1:")[0]
    assert "if (tx_go)" in idle_arm
    assert "wr_sel_txdata" not in idle_arm


def test_rx_line_passes_through_a_synchroniser() -> None:
    sv = _sv(input_sync_stages=3)
    assert "rx_sync0 <= uart_rx;" in sv
    assert "rx_sync1 <= rx_sync0;" in sv
    assert "rx_sync2 <= rx_sync1;" in sv


def test_line_and_synchroniser_reset_high() -> None:
    """Coming out of reset low would look exactly like a start bit and the
    receiver would frame on noise."""
    sv = _sv()
    # There are two clocked blocks — the spliced register block and this
    # module's own — so take the last reset body, which is the UART's.
    start = sv.rindex("if (!areset_n) begin")
    reset_block = sv[start : sv.index("end else begin", start)]
    assert "uart_tx <= 1'b1;" in reset_block
    assert "rx_sync0 <= 1'b1;" in reset_block
    assert "rx_sync1 <= 1'b1;" in reset_block


def test_fsms_have_a_recovery_default() -> None:
    sv = _sv()
    assert sv.count("default: begin") >= 2 or sv.count("default:") >= 2


def test_status_flag_pulses_default_low() -> None:
    """The set inputs are one-cycle pulses, so they are defaulted low at the
    top of the block and raised below."""
    sv = _sv()
    body = sv[sv.index("end else begin") :]
    assert "status_rx_valid_set <= 1'b0;" in body
    assert "status_rx_valid_set <= 1'b1;" in body


# --------------------------------------------------------------------------- #
# Framing
# --------------------------------------------------------------------------- #


def test_frame_is_start_lsb_first_stop() -> None:
    assert _tx_frame_bits(0x01) == [0, 1, 0, 0, 0, 0, 0, 0, 0, 1]
    assert _tx_frame_bits(0x80) == [0, 0, 0, 0, 0, 0, 0, 0, 1, 1]


def test_frame_length_is_ten_bits() -> None:
    assert len(_tx_frame_bits(0x00)) == 10


# --------------------------------------------------------------------------- #
# Testbench recipe
# --------------------------------------------------------------------------- #


def test_test_bytes_are_not_bit_palindromes() -> None:
    """0xA5 and 0x3C both read the same backwards, so an MSB-first shift bug
    would transmit an identical frame and the checks would pass against
    reversed hardware. Pinned because both are the obvious things to reach for.
    """
    spec = tb_spec(_opts())
    tx_levels = [c.expected for c in spec.checks if c.signal == "uart_tx"]
    data = tx_levels[1:9]  # between start and stop
    assert data != data[::-1], "the transmitted byte is a bit-palindrome"


def test_tb_checks_every_bit_of_the_transmitted_frame() -> None:
    tx_checks = [c for c in tb_spec(_opts()).checks if c.signal == "uart_tx"]
    # cycle 0 idle check, plus ten frame bits, plus the return to idle
    assert len(tx_checks) >= 11
    assert tx_checks[1].expected == 0, "the start bit must be checked low"


def test_tb_bit_checks_are_one_divisor_apart() -> None:
    """The spacing is the framing: checks bunched at one instant would pass
    against a transmitter with completely wrong bit timing."""
    div = 8
    spec = tb_spec(_opts(default_divisor=div))
    cycles = sorted(c.cycle for c in spec.checks if c.signal == "uart_tx" and c.cycle > 0)
    frame = cycles[:10]
    gaps = {b - a for a, b in zip(frame[:-1], frame[1:], strict=True)}
    assert gaps == {div}


@pytest.mark.parametrize(
    "options",
    [{}, {"default_divisor": 2}, {"default_divisor": 13}, {"input_sync_stages": 4}],
    ids=["defaults", "div2", "div13", "sync4"],
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


def test_bundles_match_the_generated_module() -> None:
    opts = _opts()
    check_bundles_against_module(IP.generate(opts), bundles(opts))


def test_serial_link_is_its_own_bundle() -> None:
    axi, serial = bundles(_opts())
    assert axi.protocol == "axi4-lite"
    assert serial.protocol == "uart"
    assert {p.role_name for p in serial.ports} == {"tx", "rx"}


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("axil-uart", {})
    assert [f.kind for f in res.files] == [
        "rtl", "doc", "tb", "tb", "tb", "rtl", "doc"
    ]
    # rtl, datasheet, SV TB, cocotb TB, verification scaffold, example
    # instantiation, test plan. The two `rtl` and two `doc` entries are
    # distinguished by path, not kind (GeneratedFile.kind is frozen).
    assert [f.path for f in res.files if f.kind == "tb"][-1].endswith("_checks.sv")
    assert [f.path for f in res.files if f.kind == "rtl"][-1].endswith(
        ("_example.sv", "_example.v")
    )
    doc = next(f.text for f in res.files if f.kind == "doc")
    assert "`BAUDDIV`" in doc and "`STATUS`" in doc
