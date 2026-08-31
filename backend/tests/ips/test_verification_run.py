"""Verilator gate for the bound verification scaffolds (P4-09).

Three things have to hold before a generated checker is worth anything, and
each is tested here rather than assumed:

1. **It attaches.** ``bind`` puts the scaffold inside the DUT with no change to
   the design or the testbench. Proven by every IP still running green with the
   scaffold file added to the compile.
2. **It can fail.** Verilator turns ``$error`` into an implicit ``$stop`` and
   aborts non-zero, so a firing check makes ``run_smoke`` report ``fail``.
   Proven by the mutation half, which also asserts the scaffold's own
   ``CHECK FAIL:`` text appears — a run that failed for some *other* reason
   would otherwise look like a working checker.
3. **It adds power.** This is the one that is easy to skip. ``rdata_churns``
   breaks a property the directed testbench structurally cannot see: it
   corrupts ``rdata`` only on cycles no directed read samples. That mutation is
   run twice — once with the scaffold and once without — and the pair is the
   evidence, because a mutation that fails both ways proves only that the
   testbench works.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from semicraft_core.generate import generate_files
from semicraft_core.ips import regblock
from semicraft_core.ir.nodes import (
    Assign,
    If,
    Ref,
    UnaryOp,
    UnaryOpKind,
)
from semicraft_core.sim import SimResult, run_smoke

_HAS_VERILATOR = shutil.which("verilator") is not None

# Every IP that splices in the AXI4-Lite register block, and therefore carries
# the shared bus scaffold. Pinned as a list so attaching an eighth is a
# deliberate edit rather than something a wildcard picks up silently.
AXI_IPS = [
    "axil-gpio",
    "axil-i2c",
    "axil-intc",
    "axil-regblock",
    "axil-spi",
    "axil-timer",
    "axil-uart",
]

# The memory-style IPs. They share a scaffold shape of their own — one monitor
# and one read-hold check — because they share a read path shape: a register
# behind an enable. No liveness check, because there is no handshake to be live
# about.
MEMORY_IPS = ["sync-fifo", "sync-ram"]

_STYLES = {
    "defaults": {},
    "camel_prefix": {"naming": {"convention": "camel", "prefix": "p_"}},
}


def _write(tmp_path: Path, item_id: str, options: dict) -> tuple[Path, Path, Path | None]:
    """Generate an IP and write its RTL, TB and scaffold; return the paths."""
    res = generate_files(item_id, options)
    rtl = next(f for f in res.files if f.kind == "rtl")
    tb = next(f for f in res.files if f.kind == "tb" and f.path.endswith("_tb.sv"))
    checks = next((f for f in res.files if f.path.endswith("_checks.sv")), None)

    tmp_path.mkdir(parents=True, exist_ok=True)
    rtl_path = tmp_path / rtl.path
    tb_path = tmp_path / tb.path
    rtl_path.write_text(rtl.text, encoding="utf-8")
    tb_path.write_text(tb.text, encoding="utf-8")
    checks_path = None
    if checks is not None:
        checks_path = tmp_path / checks.path
        checks_path.write_text(checks.text, encoding="utf-8")
    return rtl_path, tb_path, checks_path


def _run(tmp_path: Path, item_id: str, options: dict, *, with_checks: bool = True) -> SimResult:
    rtl_path, tb_path, checks_path = _write(tmp_path, item_id, options)
    sources = [rtl_path]
    if with_checks and checks_path is not None:
        sources.append(checks_path)
    return run_smoke(tb_path, sources)


# --------------------------------------------------------------------------- #
# The scaffold exists, attaches, and does not break a correct design
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("item_id", AXI_IPS, ids=AXI_IPS)
def test_every_axi_ip_emits_a_scaffold(item_id: str) -> None:
    res = generate_files(item_id, {})
    checks = [f for f in res.files if f.path.endswith("_checks.sv")]
    assert len(checks) == 1, f"{item_id} emitted {len(checks)} scaffold files"
    text = checks[0].text
    assert f"bind {item_id.replace('-', '_')} " in text
    assert "CHECK FAIL: write_response_arrives" in text


def test_verilog_builds_get_no_scaffold() -> None:
    """`bind` has no Verilog-2001 equivalent, so a Verilog build must not be
    handed a file it cannot compile."""
    res = generate_files("axil-gpio", {"language": "verilog"})
    assert not [f for f in res.files if f.path.endswith("_checks.sv")]


@pytest.mark.parametrize("item_id", MEMORY_IPS, ids=MEMORY_IPS)
def test_memory_ips_check_the_read_hold(item_id: str) -> None:
    res = generate_files(item_id, {})
    (checks,) = [f for f in res.files if f.path.endswith("_checks.sv")]
    assert "CHECK FAIL: read_data_holds_between_reads" in checks.text
    assert f"bind {item_id.replace('-', '_')} " in checks.text


def test_a_ram_without_a_read_enable_gets_no_scaffold() -> None:
    """There is no hold property without an enable to hold against, and a
    scaffold that checked nothing would be worse than none."""
    res = generate_files("sync-ram", {"read_enable": False})
    assert not [f for f in res.files if f.path.endswith("_checks.sv")]


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("item_id", AXI_IPS + MEMORY_IPS, ids=AXI_IPS + MEMORY_IPS)
@pytest.mark.parametrize("style", sorted(_STYLES), ids=sorted(_STYLES))
def test_bound_scaffold_runs_clean(item_id: str, style: str, tmp_path: Path) -> None:
    """A correct DUT stays green with the scaffold bound in.

    The naming-style axis is not decoration: the scaffold is authored in
    canonical names and restyled through the render name map, and AXI4-Lite
    fixes its reset active-low, so ``areset`` -> ``areset_n`` happens at the
    *default* configuration. A scaffold that skipped restyling would bind to
    undefined nets here, not only under the camel case.
    """
    result = _run(tmp_path, item_id, _STYLES[style])
    assert result.status == "pass", (
        f"{item_id} failed with its verification scaffold bound "
        f"(style={style}, status={result.status!r}).\n"
        f"--- stdout tail ---\n{result.stdout_tail}\n"
        f"--- stderr tail ---\n{result.stderr_tail}"
    )


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #

# Captured at import time. Looking the original up through the module inside
# the mutation would find the *patched* function once monkeypatch has run, so
# the mutation would call itself - the trap that made the P4-06 SPI
# `clock_never_toggles` mutation silently pass.
_ORIGINAL_READ_BODY = regblock._read_body


def _read_body_that_churns_rdata(regmap, data_width, addr_width):
    """Corrupt ``rdata`` on exactly the cycles no directed read is looking.

    The real read body is kept intact, so a read still returns the right word
    at the cycle the directed testbench samples it (``rvalid`` is high then,
    and this only fires while ``rvalid`` is low). Every *other* cycle, ``rdata``
    inverts. No directed check can see that; the stability check can.
    """
    body = _ORIGINAL_READ_BODY(regmap, data_width, addr_width)
    assert isinstance(body, If), "read body is no longer a single If - update this mutation"
    churn = If(
        UnaryOp(UnaryOpKind.NOT_LOGICAL, Ref("rvalid")),
        then=[Assign(Ref("rdata"), UnaryOp(UnaryOpKind.NOT_BITWISE, Ref("rdata")))],
    )
    return If(body.cond, then=body.then, else_=[churn])


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
def test_rdata_churn_is_caught_only_by_the_scaffold(tmp_path: Path, monkeypatch) -> None:
    """The headline result: the scaffold catches what the testbench cannot.

    Same broken DUT, run twice. Without the scaffold the directed testbench is
    perfectly happy - it reads ``rdata`` on the one cycle the value is still
    correct and never looks again. With the scaffold bound, the read-data
    stability check fires. If both runs failed, the mutation would prove
    nothing about the scaffold; if both passed, the scaffold would be
    decoration.
    """
    generate_files("axil-regblock", {})  # force the registry's lazy import first
    monkeypatch.setattr(regblock, "_read_body", _read_body_that_churns_rdata)

    without = _run(tmp_path / "bare", "axil-regblock", {}, with_checks=False)
    assert without.status == "pass", (
        "the directed testbench caught the rdata churn on its own, so this "
        "mutation cannot show what the scaffold adds - pick a property the "
        "directed vectors really do not sample.\n"
        f"--- stdout tail ---\n{without.stdout_tail}"
    )

    with_checks = _run(tmp_path / "bound", "axil-regblock", {})
    assert with_checks.status != "pass", (
        "the bound scaffold did not catch rdata changing between reads"
    )
    assert "CHECK FAIL: rdata_holds_between_reads" in with_checks.stdout_tail, (
        "the run failed, but not because the stability check fired.\n"
        f"--- stdout tail ---\n{with_checks.stdout_tail}"
    )


# Breaking the response path stalls the bus. The directed testbench also
# notices - it checks the response cycle of *every* transaction, so on
# SemiCraft's own sequences it always notices first, and the liveness check
# adds nothing to the smoke gate. That is worth stating plainly rather than
# dressing up: the liveness check earns its place in the file a user reuses in
# their own, more sparsely checked bench.
#
# So to show the check works at all, the testbench's own checks are silenced
# first: every `$fatal` becomes a `$display`, which turns the directed TB into
# a pure stimulus generator that always reports SMOKE PASS. The scaffold is
# then the only thing in the compile that can stop the run.
_TEXT_MUTATIONS = {
    "write_response_lost": ("bvalid <= 1'b1;", "bvalid <= 1'b0;", "write_response_arrives"),
    "read_response_lost": ("rvalid <= 1'b1;", "rvalid <= 1'b0;", "read_data_arrives"),
}


def _silence_tb_checks(tb_path: Path) -> None:
    """Turn the generated testbench's own `$fatal` checks into prints."""
    text = tb_path.read_text(encoding="utf-8")
    assert "$fatal(1, " in text, "the testbench no longer reports failures with $fatal"
    tb_path.write_text(text.replace("$fatal(1, ", "$display("), encoding="utf-8")


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("name", sorted(_TEXT_MUTATIONS), ids=sorted(_TEXT_MUTATIONS))
def test_a_stalled_bus_trips_the_liveness_check(name: str, tmp_path: Path) -> None:
    """Break the response path, silence the testbench, require the checker to speak."""
    old, new, check_name = _TEXT_MUTATIONS[name]
    rtl_path, tb_path, checks_path = _write(tmp_path, "axil-regblock", {})
    assert checks_path is not None

    text = rtl_path.read_text(encoding="utf-8")
    assert text.count(old) == 1, (
        f"mutation {name!r} expected exactly one {old!r} in the generated RTL, "
        f"found {text.count(old)} - the generator changed shape"
    )
    rtl_path.write_text(text.replace(old, new), encoding="utf-8")
    _silence_tb_checks(tb_path)

    # Control: with its checks silenced the testbench cannot fail, so a pass
    # here is what makes the next assertion attributable to the scaffold.
    bare = run_smoke(tb_path, [rtl_path])
    assert bare.status == "pass", (
        "the silenced testbench still failed, so the scaffold run below would "
        f"prove nothing.\n--- stdout tail ---\n{bare.stdout_tail}"
    )

    result = run_smoke(tb_path, [rtl_path, checks_path])
    assert result.status != "pass", f"mutation {name!r} did not trip the scaffold"
    assert f"CHECK FAIL: {check_name}" in result.stdout_tail, (
        f"the run failed, but the {check_name!r} check never fired - the "
        f"scaffold may be compiling without being evaluated.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )


# The memory scaffold gets the same honest treatment as the AXI liveness check,
# and for the same reason: two separate attempts to find a mutation the RAM's
# directed testbench could not see both failed, because it genuinely checks the
# hold.
#
# The first attempt deleted the `if (re)` gate outright: with no gate the next
# cycle's address overwrites the word about to be sampled, so the read returns
# the wrong value. Fair enough - too broad. The second narrowed it to inverting
# `dout` only while `re` is low, so every read still returns the right word at
# the cycle it is sampled. That failed too, and the failure is what the
# testbench should be given credit for: it reads `dout` on a cycle whose
# previous cycle had `re` low, which is a hold check, deliberate or not.
#
# So the read-hold scaffold adds nothing to the smoke gate for these two IPs.
# Its value is the same as the liveness check's - the file a user reuses in
# their own, more sparsely checked bench - and it is proven functional the same
# way: silence the testbench's own checks, then require the scaffold to speak.
_HOLD_BROKEN = (
    "        if (re) begin\n            dout <= mem[addr];\n        end",
    "        if (re) begin\n            dout <= mem[addr];\n"
    "        end else begin\n            dout <= ~dout;\n        end",
)


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
def test_a_read_register_that_does_not_hold_trips_the_scaffold(tmp_path: Path) -> None:
    """Break the hold, silence the testbench, require the read-hold check to fire."""
    old, new = _HOLD_BROKEN
    rtl_path, tb_path, checks_path = _write(tmp_path, "sync-ram", {})
    assert checks_path is not None
    text = rtl_path.read_text(encoding="utf-8")
    assert text.count(old) == 1, "the RAM read path changed shape - update this mutation"
    rtl_path.write_text(text.replace(old, new), encoding="utf-8")
    _silence_tb_checks(tb_path)

    bare = run_smoke(tb_path, [rtl_path])
    assert bare.status == "pass", (
        "the silenced testbench still failed, so the scaffold run below would "
        f"prove nothing.\n--- stdout tail ---\n{bare.stdout_tail}"
    )

    result = run_smoke(tb_path, [rtl_path, checks_path])
    assert result.status != "pass", "the bound scaffold did not catch the broken hold"
    assert "CHECK FAIL: read_data_holds_between_reads" in result.stdout_tail, (
        f"the run failed, but not because the read-hold check fired.\n"
        f"--- stdout tail ---\n{result.stdout_tail}"
    )
