"""Synchronous FIFO IP: options, RTL shape, and metadata (P4-03a).

Behaviour is proved by ``test_sync_fifo_run.py``; these pin the decisions.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from semicraft_core.generate import generate_files
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.sync_fifo import IP, SyncFifoOptions, bundles, register_map, tb_spec
from semicraft_core.render import StyleOptions, render


def _opts(**kw) -> SyncFifoOptions:
    return SyncFifoOptions(**kw)


def _sv(**kw) -> str:
    return render(IP.generate(_opts(**kw)), language="sv", style=StyleOptions(),
                  include_wrapper=True)


def test_satisfies_the_ip_protocol() -> None:
    assert isinstance(IP, IpDef)
    assert IP.kind == "ip"


@pytest.mark.parametrize("depth", [2, 4, 8, 16, 1024, 4096])
def test_powers_of_two_are_accepted(depth: int) -> None:
    assert _opts(depth=depth).depth == depth


@pytest.mark.parametrize("depth", [3, 5, 6, 12, 100, 1000])
def test_non_powers_of_two_are_rejected_with_the_nearest_legal_values(depth: int) -> None:
    """The wrap-bit comparison is only exact for a power-of-two depth, and the
    message has to be actionable — a bare "invalid" makes the user guess."""
    with pytest.raises(ValidationError, match="power of two"):
        _opts(depth=depth)


def test_addr_bits_is_clog2_of_depth() -> None:
    assert [_opts(depth=d).addr_bits for d in (2, 4, 8, 16, 1024)] == [1, 2, 3, 4, 10]


# --------------------------------------------------------------------------- #
# RTL shape
# --------------------------------------------------------------------------- #


def test_pointers_carry_an_extra_wrap_bit() -> None:
    """depth=8 needs 3 index bits, so the pointers are 4 bits wide."""
    sv = _sv(depth=8)
    assert "logic [3:0] wptr;" in sv
    assert "logic [3:0] rptr;" in sv
    assert "logic [7:0] mem [8];" in sv


def test_full_and_empty_come_from_the_wrap_bit() -> None:
    sv = _sv(depth=8)
    assert "assign empty = wptr == rptr;" in sv
    assert "assign full = (wptr[3] != rptr[3]) && (wptr[2:0] == rptr[2:0]);" in sv


def test_count_is_a_plain_subtraction() -> None:
    """The wrap bit makes this exact across a wrap; no saturating logic."""
    assert "assign count = wptr - rptr;" in _sv()


def test_count_output_can_be_omitted() -> None:
    sv = _sv(count_output=False)
    assert "count" not in sv
    assert "assign empty" in sv  # the other flags stay


def test_writes_and_reads_are_guarded_by_the_flags() -> None:
    sv = _sv()
    assert "if (wr_en && (!full)) begin" in sv
    assert "if (rd_en && (!empty)) begin" in sv


def test_reads_are_registered_from_the_read_pointer() -> None:
    sv = _sv(depth=8)
    assert "rd_data <= mem[rptr[2:0]];" in sv
    assert "mem[wptr[2:0]] <= wr_data;" in sv


def test_storage_is_not_cleared_on_reset() -> None:
    """Clearing a deep memory costs logic for no observable difference: while
    empty the entries are unreachable."""
    sv = _sv()
    reset_block = sv[sv.index("if (!rst_n) begin") : sv.index("end else begin")]
    assert "mem" not in reset_block
    assert "wptr <= 4'd0;" in reset_block
    assert "rptr <= 4'd0;" in reset_block


# --------------------------------------------------------------------------- #
# IpDef metadata — the two branches the register block could not exercise
# --------------------------------------------------------------------------- #


def test_has_no_register_map() -> None:
    """The ``RegisterMap | None`` branch of the contract: a datapath IP is not
    forced to invent software-visible registers."""
    assert register_map(_opts()) is None


def test_datasheet_omits_the_register_map_section() -> None:
    doc = next(f.text for f in generate_files("sync-fifo", {}).files if f.kind == "doc")
    assert "## Register map" not in doc
    assert "## Bus interfaces" in doc


def test_two_bundles_share_one_clock() -> None:
    """The case the "clocks are referenced, not owned" rule exists for — a port
    may belong to at most one bundle, so a member clock would make this
    illegal."""
    wr, rd = bundles(_opts())
    assert (wr.name, rd.name) == ("wr", "rd")
    assert wr.clock == rd.clock == "clk"
    assert wr.reset == rd.reset == "rst"
    assert "clk" not in wr.signals and "clk" not in rd.signals


def test_bundles_match_the_generated_module() -> None:
    opts = _opts()
    check_bundles_against_module(IP.generate(opts), bundles(opts))


def test_bundle_roles_are_protocol_names_not_port_names() -> None:
    wr, rd = bundles(_opts())
    assert {p.role_name for p in wr.ports} == {"en", "data", "full"}
    assert {p.role_name for p in rd.ports} == {"en", "data", "empty"}


# --------------------------------------------------------------------------- #
# Testbench recipe
# --------------------------------------------------------------------------- #


def test_tb_exercises_both_boundaries() -> None:
    """A FIFO test that never fills or empties proves almost nothing."""
    opts = _opts()
    spec = tb_spec(opts)
    counts = {c.expected for c in spec.checks if c.signal == "count"}
    assert opts.depth in counts  # reached full
    assert 0 in counts  # returned to empty
    assert {c.expected for c in spec.checks if c.signal == "full"} == {0, 1}
    assert {c.expected for c in spec.checks if c.signal == "empty"} == {0, 1}


def test_tb_reads_back_distinct_non_zero_values() -> None:
    """Otherwise a readback check would pass against a FIFO stuck at its reset
    value."""
    checks = tb_spec(_opts()).checks
    # Cycle 0 checks the reset value (0) before anything is driven; the ordered
    # readback is what follows it.
    assert (0, "rd_data", 0) in {(c.cycle, c.signal, c.expected) for c in checks}
    ordered = [c.expected for c in checks if c.signal == "rd_data" and c.cycle > 0][:4]
    assert len(ordered) == 4
    assert len(set(ordered)) == len(ordered)
    assert all(v != 0 for v in ordered)


@pytest.mark.parametrize(
    "options",
    [{}, {"depth": 2, "width": 1}, {"count_output": False}, {"depth": 1024, "width": 16}],
    ids=["defaults", "narrow", "no_count", "deep"],
)
def test_tb_only_touches_ports_that_exist(options) -> None:
    opts = _opts(**options)
    declared = {p.name for p in IP.generate(opts).ports}
    spec = tb_spec(opts)
    for check in spec.checks:
        assert check.signal in declared, f"{options}: checks missing port {check.signal}"
    for vector in spec.vectors:
        for signal in vector:
            assert signal in declared, f"{options}: drives missing port {signal}"


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("sync-fifo", {})
    assert [f.kind for f in res.files] == ["rtl", "doc", "tb", "tb", "tb", "doc"]
    # rtl, datasheet, SV TB, cocotb TB, verification scaffold, test plan.
    assert [f.path for f in res.files if f.kind == "tb"][-1].endswith("_checks.sv")
    assert res.files[0].path == "sync_fifo.sv"
