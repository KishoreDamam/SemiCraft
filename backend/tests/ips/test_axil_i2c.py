"""AXI4-Lite I2C master: bus drivers, register map, composition (P4-07)."""

from __future__ import annotations

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips.axil_i2c import (
    _ACK,
    _BIT,
    _CMD_ACK,
    _CMD_READ,
    _CMD_START,
    _CMD_STOP,
    _CMD_WRITE,
    _IDLE,
    _START,
    _STOP,
    IP,
    AxilI2cOptions,
    _expected_drive,
    _quarter_plan,
    bundles,
    register_map,
    tb_spec,
)
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.regblock import axil_ports, write_strobe_name
from semicraft_core.render import StyleOptions, render


def _opts(**kw) -> AxilI2cOptions:
    return AxilI2cOptions(**kw)


def _sv(**kw) -> str:
    return render(IP.generate(_opts(**kw)), language="sv", style=StyleOptions(),
                  include_wrapper=True)


def test_satisfies_the_ip_protocol() -> None:
    assert isinstance(IP, IpDef)
    assert IP.kind == "ip"


# --------------------------------------------------------------------------- #
# Open drain
# --------------------------------------------------------------------------- #


def test_no_bidirectional_ports_and_no_driven_highs() -> None:
    """I2C lines are pulled low or released; nothing ever drives a one. The
    module exposes pull-down enables and sensed levels instead of an inout."""
    sv = _sv()
    assert "inout" not in sv
    names = {p.name for p in IP.generate(_opts()).ports}
    assert {"scl_oe", "sda_oe", "scl_in", "sda_in"} <= names
    assert "scl_out" not in names and "sda_out" not in names


def test_bus_is_released_out_of_reset() -> None:
    """A master must not come up holding a shared bus."""
    spec = tb_spec(_opts())
    at_zero = {(c.signal, c.expected) for c in spec.checks if c.cycle == 0}
    assert ("scl_oe", 0) in at_zero
    assert ("sda_oe", 0) in at_zero


def test_drivers_are_continuous_functions_of_state() -> None:
    """Not assigned inside the FSM: an I2C bit is four quarter-phases, and
    writing the line behaviour as per-transition side effects is where these
    state machines go wrong."""
    sv = _sv()
    assert "assign scl_oe = " in sv
    assert "assign sda_oe = " in sv


# --------------------------------------------------------------------------- #
# Bus conditions
# --------------------------------------------------------------------------- #


def test_start_drops_sda_while_scl_is_high() -> None:
    """That edge *is* the START condition; with SCL low it is just a data bit."""
    cmd = _CMD_START | _CMD_WRITE
    # Phases 0 and 1: both released. Phase 2: SDA pulled low, SCL still released.
    assert _expected_drive(_START, 0, cmd, 0, 0) == (0, 0)
    assert _expected_drive(_START, 1, cmd, 0, 0) == (0, 0)
    assert _expected_drive(_START, 2, cmd, 0, 0) == (0, 1)
    # Only then is SCL pulled low.
    assert _expected_drive(_START, 3, cmd, 0, 0) == (1, 1)


def test_stop_releases_sda_while_scl_is_high() -> None:
    cmd = _CMD_STOP
    assert _expected_drive(_STOP, 0, cmd, 0, 0) == (1, 1)  # SCL low, SDA low
    assert _expected_drive(_STOP, 1, cmd, 0, 0) == (0, 1)  # SCL released
    assert _expected_drive(_STOP, 2, cmd, 0, 0) == (0, 1)  # SCL high, SDA still low
    assert _expected_drive(_STOP, 3, cmd, 0, 0) == (0, 0)  # SDA rises = STOP


def test_written_bits_pull_low_for_zero_and_release_for_one() -> None:
    cmd = _CMD_WRITE
    # 0x80 = MSB set, so the first bit is a one -> released.
    assert _expected_drive(_BIT, 1, cmd, 0x80, 0)[1] == 0
    # ...and a zero bit pulls low.
    assert _expected_drive(_BIT, 1, cmd, 0x00, 0)[1] == 1


def test_master_releases_sda_for_the_slaves_ack_on_a_write() -> None:
    assert _expected_drive(_ACK, 1, _CMD_WRITE, 0, 0)[1] == 0


@pytest.mark.parametrize(("ack", "driven"), [(0, 0), (_CMD_ACK, 1)])
def test_master_answers_the_ack_itself_on_a_read(ack: int, driven: int) -> None:
    """NACK is a released line — which is how a master ends a read."""
    assert _expected_drive(_ACK, 1, _CMD_READ | ack, 0, 0)[1] == driven


def test_scl_is_low_around_the_sda_transition_of_a_data_bit() -> None:
    """SDA may only change while SCL is low, or it would look like START/STOP."""
    for phase, expected in ((0, 1), (1, 0), (2, 0), (3, 1)):
        assert _expected_drive(_BIT, phase, _CMD_WRITE, 0, 0)[0] == expected


def test_idle_releases_everything() -> None:
    assert _expected_drive(_IDLE, 0, 0, 0, 0) == (0, 0)


# --------------------------------------------------------------------------- #
# Command plan
# --------------------------------------------------------------------------- #


def test_quarter_plan_covers_start_byte_ack_stop() -> None:
    plan = _quarter_plan(_CMD_START | _CMD_WRITE | _CMD_STOP)
    assert len(plan) == 4 + 8 * 4 + 4 + 4
    assert plan[0][0] == _START
    assert [q for q, (s, _p) in enumerate(plan) if s == _ACK] == [36, 37, 38, 39]
    assert [q for q, (s, _p) in enumerate(plan) if s == _STOP] == [40, 41, 42, 43]


def test_command_flags_select_the_primitives() -> None:
    assert len(_quarter_plan(_CMD_START)) == 4
    assert len(_quarter_plan(_CMD_STOP)) == 4
    assert len(_quarter_plan(_CMD_START | _CMD_STOP)) == 8
    assert len(_quarter_plan(_CMD_READ)) == 36  # eight bits plus the ACK


# --------------------------------------------------------------------------- #
# Register map and composition
# --------------------------------------------------------------------------- #


def test_register_map_layout() -> None:
    regmap = register_map(_opts())
    assert [(r.name, r.offset) for r in regmap.registers] == [
        ("STATUS", 0x0), ("CMD", 0x4), ("TXDATA", 0x8), ("RXDATA", 0xC), ("CLKDIV", 0x10)
    ]


def test_command_is_triggered_by_the_register_write_strobe() -> None:
    sv = _sv()
    assert f"cmd_go <= {write_strobe_name('CMD')};" in sv


def test_both_bus_lines_are_synchronised() -> None:
    sv = _sv(input_sync_stages=3)
    for line in ("scl", "sda"):
        assert f"{line}_sync0 <= {line}_in;" in sv
        assert f"{line}_sync2 <= {line}_sync1;" in sv


def test_quarter_counter_holds_while_the_clock_is_stretched() -> None:
    """A free-running counter would wrap all the way round before the advance
    condition came true again, so the master would hang for 2**16 cycles."""
    sv = _sv()
    assert sv.count("q_cnt <= q_cnt + 16'b1;") == 1
    stall_guard = sv[: sv.index("q_cnt <= q_cnt + 16'b1;")]
    assert "clkdiv_div - 16'b1" in stall_guard


def test_is_one_flat_module() -> None:
    sv = _sv()
    assert sv.count("module ") == 1 and sv.count("endmodule") == 1


# --------------------------------------------------------------------------- #
# Testbench recipe
# --------------------------------------------------------------------------- #


def test_tb_stretches_the_clock() -> None:
    """Clock stretching is the feature most easily left untested — a bus that
    never stalls exercises none of the wait logic."""
    spec = tb_spec(_opts())
    scl_drives = [v["scl_in"] for v in spec.vectors if "scl_in" in v]
    assert 0 in scl_drives, "the testbench never pulls SCL low"
    assert scl_drives.count(1) >= 2


def test_tb_covers_both_a_write_and_a_read() -> None:
    spec = tb_spec(_opts())
    rdata = [c.expected for c in spec.checks if c.signal == "rdata"]
    assert 0x2D in rdata, "no read transaction checks the received byte"


def test_tb_read_byte_is_not_a_bit_palindrome() -> None:
    """An MSB/LSB shift bug would otherwise produce the same byte."""
    byte = 0x2D
    assert int(f"{byte:08b}"[::-1], 2) != byte


@pytest.mark.parametrize(
    "options",
    [{}, {"default_divisor": 1}, {"default_divisor": 9}, {"input_sync_stages": 4}],
    ids=["defaults", "div1", "div9", "sync4"],
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


def test_i2c_bus_is_its_own_bundle() -> None:
    axi, i2c = bundles(_opts())
    assert axi.protocol == "axi4-lite"
    assert i2c.protocol == "i2c" and i2c.role == "initiator"
    assert {p.role_name for p in i2c.ports} == {"scl_oe", "scl_in", "sda_oe", "sda_in"}


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("axil-i2c", {})
    assert [f.kind for f in res.files] == ["rtl", "doc", "tb", "tb", "tb", "doc"]
    # rtl, datasheet, SV TB, cocotb TB, verification scaffold, test plan.
    assert [f.path for f in res.files if f.kind == "tb"][-1].endswith("_checks.sv")
    doc = next(f.text for f in res.files if f.kind == "doc")
    assert "`CMD`" in doc and "`CLKDIV`" in doc
    assert set(axil_ports()) <= set(doc.split())  or "awvalid" in doc
