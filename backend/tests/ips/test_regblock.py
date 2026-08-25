"""AXI4-Lite register block generator (P4-02).

Structural and policy tests over the emitted IR/text. The *behavioural* proof
lives in ``test_axil_regblock_run.py``, which compiles and runs the thing —
these tests exist to pin the decisions that are easy to regress silently.
"""

from __future__ import annotations

import pytest
from semicraft_core.ips.contract import IpContractError
from semicraft_core.ips.regblock import (
    AXI_RESP_OKAY,
    AXI_RESP_SLVERR,
    axil_ports,
    build_axil_regblock,
    hardware_ports,
    hw_port_name,
    w1c_set_port_name,
    write_reserved_mask,
)
from semicraft_core.ips.regmap import Register, RegisterField, RegisterMap
from semicraft_core.render import StyleOptions, render


def _map(fields=None, **kw) -> RegisterMap:
    kw.setdefault("name", "M")
    kw.setdefault("data_width", 32)
    kw.setdefault("addr_width", 5)
    kw.setdefault(
        "registers",
        [
            Register(
                name="A",
                offset=0,
                fields=fields
                or [RegisterField(name="v", lsb=0, width=32, access="rw")],
            )
        ],
    )
    return RegisterMap(**kw)


def _sv(regmap, **kw) -> str:
    return render(
        build_axil_regblock("axil_regblock", regmap, **kw),
        language="sv",
        style=StyleOptions(),
        include_wrapper=True,
    )


# --------------------------------------------------------------------------- #
# Port surface
# --------------------------------------------------------------------------- #


def test_emits_the_axi4_lite_signal_set() -> None:
    module = build_axil_regblock("rb", _map())
    names = {p.name for p in module.ports}
    assert set(axil_ports()) <= names
    assert {"aclk", "areset"} <= names


def test_no_prot_ports() -> None:
    """Deliberate: the block enforces no protection policy, so declaring
    inputs it never reads would be dead logic and would fail the -Wall gate.

    Pinned because "add awprot for conformance" is a tempting one-line change
    that would silently break the lint gate for every configuration.
    """
    module = build_axil_regblock("rb", _map())
    names = {p.name for p in module.ports}
    assert "awprot" not in names
    assert "arprot" not in names


def test_reset_is_active_low_regardless_of_request() -> None:
    """AXI4-Lite mandates it, so there is no polarity knob to get wrong."""
    for sync in (True, False):
        module = build_axil_regblock("rb", _map(), sync_reset=sync)
        ff = next(i for i in module.items if hasattr(i, "reset") and i.reset is not None)
        assert ff.reset.active_low is True
        assert ff.reset.name == "areset"
    assert "areset_n" in _sv(_map())


@pytest.mark.parametrize(
    ("access", "direction", "extra"),
    [
        ("rw", "output", False),
        ("wo", "output", False),
        ("ro", "input", False),
        ("w1c", "output", True),
    ],
)
def test_hardware_port_direction_per_access_type(access, direction, extra) -> None:
    regmap = _map([RegisterField(name="f", lsb=0, width=4, access=access)])
    ports = dict((n, d) for n, d, _w in hardware_ports(regmap))
    assert ports["a_f"] == direction
    assert ("a_f_set" in ports) is extra
    if extra:
        assert ports["a_f_set"] == "input"


def test_hardware_port_name_collision_is_rejected() -> None:
    regmap = RegisterMap(
        name="M",
        addr_width=5,
        registers=[
            Register(name="A_B", offset=0, fields=[RegisterField(name="c", lsb=0)]),
            Register(name="A", offset=4, fields=[RegisterField(name="b_c", lsb=0)]),
        ],
    )
    with pytest.raises(IpContractError, match="produced twice"):
        build_axil_regblock("rb", regmap)


def test_empty_map_is_rejected() -> None:
    with pytest.raises(IpContractError, match="declares no registers"):
        build_axil_regblock("rb", RegisterMap(name="M", addr_width=4))


# --------------------------------------------------------------------------- #
# Decode and response policy
# --------------------------------------------------------------------------- #


def test_full_byte_address_is_decoded() -> None:
    """Not just the word index — so a byte-offset access errors rather than
    silently aliasing onto the containing word."""
    sv = _sv(_map(registers=[Register(name="A", offset=4, fields=[
        RegisterField(name="v", lsb=0, width=32, access="rw")])]))
    assert "awaddr_q == 5'h4" in sv
    assert "case (araddr)" in sv
    # No slice of the address anywhere: that is what dropping the low bits
    # would look like.
    assert "araddr[" not in sv


def test_unmapped_read_returns_slverr_and_zero() -> None:
    sv = _sv(_map())
    default = sv[sv.index("default:") :]
    assert f"rresp <= 2'b{AXI_RESP_SLVERR:02b}" in default
    assert "rdata <= 32'b0" in default


def test_write_response_covers_both_error_causes() -> None:
    """bresp must fold in the reserved-bit rejection, not just the address hit.

    An earlier revision rejected the write via ``wr_sel`` but still answered
    OKAY — the write silently vanished with a success response.
    """
    sv = _sv(_map())
    assert "bresp <= (wr_hit && (!wr_reserved)) ?" in sv


def test_reserved_bit_check_has_no_combinational_loop() -> None:
    """``wr_sel`` depends on ``wr_reserved``, so the reserved mask must be
    selected by the address-only decode, never by ``wr_sel`` itself."""
    sv = _sv(_map([RegisterField(name="f", lsb=0, width=4, access="rw")]))
    mask_line = next(x for x in sv.splitlines() if "wr_rsvd_mask =" in x)
    assert "wr_addr_a" in mask_line
    assert "wr_sel_a" not in mask_line
    sel_line = next(x for x in sv.splitlines() if "assign wr_sel_a =" in x)
    assert "wr_addr_a" in sel_line and "wr_reserved" in sel_line


@pytest.mark.parametrize(
    ("access", "reserved"),
    [("rw", 0xFFFFFFF0), ("wo", 0xFFFFFFF0), ("w1c", 0xFFFFFFF0), ("ro", 0xFFFFFFFF)],
)
def test_write_reserved_mask_counts_read_only_bits_as_reserved(access, reserved) -> None:
    """An ``ro`` field has no storage for a write to land in, so its bits are
    write-reserved even though they are perfectly readable."""
    reg = Register(name="A", offset=0, fields=[
        RegisterField(name="f", lsb=0, width=4, access=access)])
    assert write_reserved_mask(reg, 32) == reserved


def test_no_write_select_for_a_read_only_register() -> None:
    """It would be a signal nothing reads — an instant -Wall failure."""
    regmap = _map([RegisterField(name="f", lsb=0, width=32, access="ro")])
    sv = _sv(regmap)
    assert "wr_addr_a" in sv  # still decoded, so writes to it return OKAY
    assert "wr_sel_a" not in sv


# --------------------------------------------------------------------------- #
# Field semantics
# --------------------------------------------------------------------------- #


def test_write_only_field_reads_back_as_zero() -> None:
    sv = _sv(_map([RegisterField(name="go", lsb=0, width=1, access="wo")]))
    assert "rdata <= {31'b0, 1'b0}" in sv
    assert "rdata <= {31'b0, a_go}" not in sv


def test_read_only_field_is_muxed_in_from_its_input() -> None:
    sv = _sv(_map([RegisterField(name="busy", lsb=0, width=1, access="ro")]))
    assert "rdata <= {31'b0, a_busy}" in sv


def test_rw_field_merges_against_the_byte_mask() -> None:
    sv = _sv(_map([RegisterField(name="f", lsb=0, width=4, access="rw")]))
    assert "a_f <= (wdata_q[3:0] & wmask[3:0]) | (a_f & (~wmask[3:0]))" in sv


def test_w1c_set_beats_a_same_cycle_clear() -> None:
    """The hardware set is OR-ed in *after* the software clear, so an event
    arriving in the same cycle as its clear is not lost."""
    sv = _sv(_map([RegisterField(name="f", lsb=0, width=4, access="w1c")]))
    assert "a_f <= (a_f & (~(wdata_q[3:0] & wmask[3:0]))) | a_f_set" in sv
    # ...and it still applies on cycles with no write to this register.
    assert "a_f <= a_f | a_f_set" in sv


def test_reset_values_come_from_the_field_declarations() -> None:
    sv = _sv(_map([
        RegisterField(name="a", lsb=0, width=1, access="rw", reset=1),
        RegisterField(name="b", lsb=1, width=3, access="rw", reset=5),
    ]))
    assert "a_a <= 1'd1" in sv
    assert "a_b <= 3'd5" in sv


def test_byte_mask_expands_every_strobe_bit() -> None:
    sv = _sv(_map())
    assert "wmask = {{8{wstrb_q[3]}}, {8{wstrb_q[2]}}, {8{wstrb_q[1]}}, {8{wstrb_q[0]}}}" in sv


def test_single_byte_bus_has_a_one_bit_strobe() -> None:
    regmap = RegisterMap(name="M", data_width=8, addr_width=4, registers=[
        Register(name="A", offset=0, fields=[
            RegisterField(name="v", lsb=0, width=8, access="rw")])])
    sv = _sv(regmap)
    # A one-byte bus still gets a one-bit *vector* strobe rather than a scalar:
    # the mask expansion indexes it (`wstrb_q[0]`), which is illegal on a
    # scalar in strict Verilog-2001.
    assert "logic [0:0] wstrb;" in sv or "input  logic [0:0] wstrb," in sv
    assert "wmask = {8{wstrb_q[0]}}" in sv


# --------------------------------------------------------------------------- #
# Handshake shape
# --------------------------------------------------------------------------- #


def test_ready_never_depends_on_valid() -> None:
    """A combinational valid->ready path is an AXI violation and deadlocks
    against a master that waits for ready before asserting valid."""
    sv = _sv(_map())
    for ready, forbidden in (("awready", "awvalid"), ("wready", "wvalid"), ("arready", "arvalid")):
        line = next(x for x in sv.splitlines() if f"assign {ready} =" in x)
        assert forbidden not in line, f"{ready} depends on {forbidden}: {line}"


def test_okay_response_code_is_zero() -> None:
    assert AXI_RESP_OKAY == 0
    assert AXI_RESP_SLVERR == 0b10


def test_helper_names_match_the_emitted_ports() -> None:
    reg = Register(name="IRQ0", offset=0, fields=[
        RegisterField(name="flags", lsb=0, width=4, access="w1c")])
    regmap = _map(registers=[reg])
    module = build_axil_regblock("rb", regmap)
    names = {p.name for p in module.ports}
    assert hw_port_name(reg, reg.fields[0]) == "irq0_flags"
    assert w1c_set_port_name(reg, reg.fields[0]) == "irq0_flags_set"
    assert {"irq0_flags", "irq0_flags_set"} <= names
