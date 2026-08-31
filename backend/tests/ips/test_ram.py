"""Synchronous RAM IP: options, RTL shape, metadata (P4-04).

Behaviour is proved by ``test_ram_run.py``.
"""

from __future__ import annotations

import re as _re

import pytest
from pydantic import ValidationError
from semicraft_core.generate import generate_files
from semicraft_core.ips.contract import IpDef, check_bundles_against_module
from semicraft_core.ips.ram import IP, RamOptions, bundles, register_map, tb_spec
from semicraft_core.render import StyleOptions, render


def _opts(**kw) -> RamOptions:
    return RamOptions(**kw)


def _has_identifier(text: str, name: str) -> bool:
    """Whole-identifier search.

    A bare substring test is not enough here: the license banner contains
    "Free", so `"re" in sv` is true for every module ever generated.
    """
    return _re.search(rf"\b{_re.escape(name)}\b", text) is not None


def _sv(**kw) -> str:
    return render(IP.generate(_opts(**kw)), language="sv", style=StyleOptions(),
                  include_wrapper=True)


def test_satisfies_the_ip_protocol() -> None:
    assert isinstance(IP, IpDef)
    assert IP.kind == "ip"


def test_has_no_reset_option_or_port() -> None:
    """No reset at all: storage must not be cleared, and resetting only the
    output register is what usually blocks block-RAM inference."""
    assert "reset_style" not in RamOptions.model_fields
    assert "reset_polarity" not in RamOptions.model_fields
    sv = _sv()
    assert not _has_identifier(sv, "rst")
    assert not _has_identifier(sv, "rst_n")
    assert "always_ff @(posedge clk) begin" in sv
    assert tb_spec(_opts()).reset is None


@pytest.mark.parametrize("depth", [3, 100, 1000])
def test_non_power_of_two_depth_is_rejected(depth: int) -> None:
    with pytest.raises(ValidationError, match="power of two"):
        _opts(depth=depth)


def test_address_width_is_clog2_of_depth() -> None:
    assert [_opts(depth=d).addr_bits for d in (2, 4, 256, 65536)] == [1, 2, 8, 16]
    assert "input  logic [7:0] addr" in _sv(depth=256)


# --------------------------------------------------------------------------- #
# Port modes
# --------------------------------------------------------------------------- #


def test_single_port_shares_one_address() -> None:
    sv = _sv(port_mode="single")
    assert _has_identifier(sv, "addr")
    assert not _has_identifier(sv, "waddr")
    assert not _has_identifier(sv, "raddr")
    assert "mem[addr] <= din;" in sv
    assert "dout <= mem[addr];" in sv


def test_simple_dual_port_has_independent_addresses() -> None:
    sv = _sv(port_mode="simple_dual")
    assert "mem[waddr] <= din;" in sv
    assert "dout <= mem[raddr];" in sv


def test_read_enable_can_be_omitted() -> None:
    gated = _sv(read_enable=True)
    ungated = _sv(read_enable=False)
    assert "if (re) begin" in gated
    assert _has_identifier(gated, "re")
    assert not _has_identifier(ungated, "re")
    assert "dout <= mem[addr];" in ungated


def test_storage_is_declared_but_never_reset() -> None:
    sv = _sv(depth=256, width=8)
    assert "logic [7:0] mem [256];" in sv
    # A reset skeleton would show up as an `if (!rst_n)` around the body.
    assert "if (!" not in sv.split("always_ff")[1].split("\n")[0]


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #


def test_has_no_register_map() -> None:
    assert register_map(_opts()) is None


def test_single_port_is_one_bundle_because_addr_cannot_be_in_two() -> None:
    (bundle,) = bundles(_opts(port_mode="single"))
    assert bundle.name == "mem"
    assert "addr" in bundle.signals


def test_simple_dual_port_splits_into_two_bundles() -> None:
    wr, rd = bundles(_opts(port_mode="simple_dual"))
    assert (wr.name, rd.name) == ("wr", "rd")
    assert wr.clock == rd.clock == "clk"
    assert wr.reset is None and rd.reset is None  # the RAM has no reset


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"port_mode": "simple_dual"},
        {"read_enable": False},
        {"port_mode": "simple_dual", "read_enable": False},
        {"depth": 2, "width": 1},
    ],
    ids=["single", "dual", "single_no_re", "dual_no_re", "tiny"],
)
def test_bundles_match_the_generated_module(options) -> None:
    opts = _opts(**options)
    check_bundles_against_module(IP.generate(opts), bundles(opts))


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"port_mode": "simple_dual"},
        {"read_enable": False},
        {"depth": 2, "width": 1},
        {"depth": 1024, "width": 64},
    ],
    ids=["single", "dual", "no_re", "tiny", "wide"],
)
def test_tb_only_touches_ports_that_exist(options) -> None:
    opts = _opts(**options)
    declared = {p.name for p in IP.generate(opts).ports}
    spec = tb_spec(opts)
    for check in spec.checks:
        assert check.signal in declared, f"{options}: checks missing {check.signal}"
    for vector in spec.vectors:
        for signal in vector:
            assert signal in declared, f"{options}: drives missing {signal}"


def test_tiny_depth_uses_distinct_addresses() -> None:
    """A depth-2 RAM has only two locations; a fixed three-address plan would
    write two values to the same one and then check for the first."""
    from semicraft_core.ips.ram import _test_addresses

    assert _test_addresses(_opts(depth=2)) == [0, 1]
    assert _test_addresses(_opts(depth=4)) == [0, 1, 3]


# --------------------------------------------------------------------------- #
# Testbench recipe
# --------------------------------------------------------------------------- #


def test_tb_checks_read_before_write() -> None:
    """The read-during-write cycle must expect the OLD value.

    This is the behaviour nothing in the port list reveals, so if the check
    ever stopped expecting old data the RAM could silently become write-first.
    """
    opts = _opts()
    spec = tb_spec(opts)
    mask = (1 << opts.width) - 1
    first_value = 0x11 & mask
    rewritten = first_value ^ mask

    dout_checks = [c.expected for c in spec.checks if c.signal == "dout"]
    # ...the old value appears again after the rewrite cycle, then the new one.
    assert first_value in dout_checks
    assert rewritten in dout_checks
    assert dout_checks.index(rewritten) > dout_checks.index(first_value)


def test_tb_never_checks_dout_before_a_read_completes() -> None:
    """With no reset, dout is X in a four-state simulator and zero in
    Verilator; checking it early would encode one simulator's convention."""
    spec = tb_spec(_opts())
    first_dout = min(c.cycle for c in spec.checks if c.signal == "dout")
    reads_before = [
        i for i, v in enumerate(spec.vectors) if i < first_dout and v.get("re") == 1
    ]
    assert reads_before, "no read was issued before the first dout check"


def test_tb_attaches_no_assertion_spec() -> None:
    """Deliberate: with no reset there is no reset-value property, and every
    other RAM property is data-dependent (same reasoning as pwm)."""
    assert tb_spec(_opts()).assertion_spec is None


def test_generates_the_full_ip_file_set() -> None:
    res = generate_files("sync-ram", {})
    assert [f.kind for f in res.files] == ["rtl", "doc", "tb", "tb", "tb", "doc"]
    # rtl, datasheet, SV TB, cocotb TB, verification scaffold, test plan.
    assert [f.path for f in res.files if f.kind == "tb"][-1].endswith("_checks.sv")
    doc = next(f.text for f in res.files if f.kind == "doc")
    assert "## Register map" not in doc
    assert "## Bus interfaces" in doc
