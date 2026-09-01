"""Verilator compile gate over the P3-06 checker/monitor/scoreboard scaffolds.

P3-06 landed the generators with text-golden tests only: nothing ever fed the
emitted SystemVerilog to a compiler, because the Windows dev host has no
Verilator. That gap immediately hid a real defect — the scoreboard *wrapper*
example (in both the golden fixture and docs/CHECKERS.md) referenced ``data``
from its ``push_expr``/``compare_expr`` without declaring it in
``ScoreboardWrapper.ports``, so the emitted module did not compile. The
generator was correct; the example was not. This module exists so that class of
mistake fails a test instead of shipping.

Verilator **is** available in Linux containers and in CI's lint-gate job
(``apt-get install -y verilator``), so this gate is cheap. It skips entirely
when the binary is absent, mirroring ``tests/golden/test_tb_compile.py``.

``--lint-only`` rather than ``--binary``: these scaffolds are standalone
components, not elaborable top-level designs with a stimulus process, so there
is nothing to run. Lint-only still performs full parse + elaboration checking,
which is exactly the "does the generated text compile" question this gate asks.
``--timing`` is passed for consistency with the TB gate; the scaffolds use only
event controls, which are accepted either way.

Every spec here is built locally rather than imported from ``test_golden.py``,
so a future edit to that module's fixtures cannot silently narrow this gate's
coverage.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from semicraft_core.checkers import (
    CheckerSpec,
    LatencyCheck,
    MonitorSpec,
    ResetPolarity,
    ResetValueCheck,
    ScoreboardSpec,
    ScoreboardWrapper,
    Signal,
    StabilityCheck,
    generate_checker,
    generate_monitor,
    generate_scoreboard,
)

_HAS_VERILATOR = shutil.which("verilator") is not None
_COMPILE_TIMEOUT_SECONDS = 60

pytestmark = pytest.mark.skipif(
    not _HAS_VERILATOR, reason="verilator not installed; compile gate cannot run"
)

_RST_N = ResetPolarity(signal="rst_n", active_low=True)
_RST_HIGH = ResetPolarity(signal="rst", active_low=False)


def _compile(text: str, stem: str) -> subprocess.CompletedProcess:
    """Lint-compile ``text`` as ``<stem>.sv`` in a scratch dir."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{stem}.sv"
        path.write_text(text, encoding="utf-8")
        return subprocess.run(
            [
                "verilator",
                "--timing",
                "--lint-only",
                # The generated component name need not match the filename we
                # invent here; that mismatch is not a defect in the output.
                "-Wno-DECLFILENAME",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=_COMPILE_TIMEOUT_SECONDS,
        )


def _assert_compiles(text: str, stem: str) -> None:
    result = _compile(text, stem)
    assert result.returncode == 0, (
        f"generated {stem} scaffold does not compile under verilator "
        f"(exit {result.returncode}).\n"
        f"--- stderr ---\n{result.stderr}\n"
        f"--- generated source ---\n{text}"
    )


# --------------------------------------------------------------------------- #
# monitor


def test_monitor_compiles() -> None:
    spec = MonitorSpec(
        name="req_ack_mon",
        clock="clk",
        fields=[Signal("req", 1), Signal("ack", 1), Signal("data", 8)],
        qualifier="req && ack",
    )
    _assert_compiles(generate_monitor(spec), "req_ack_mon")


def test_monitor_without_qualifier_compiles() -> None:
    """No qualifier — the sampler is unconditional."""
    spec = MonitorSpec(
        name="bus_mon",
        clock="clk",
        fields=[Signal("addr", 32), Signal("wdata", 64)],
    )
    _assert_compiles(generate_monitor(spec), "bus_mon")


def test_monitor_single_bit_field_compiles() -> None:
    spec = MonitorSpec(
        name="tiny_mon", clock="clk", fields=[Signal("flag", 1)], qualifier="flag"
    )
    _assert_compiles(generate_monitor(spec), "tiny_mon")


# --------------------------------------------------------------------------- #
# checker


def test_checker_all_families_compile() -> None:
    """One checker carrying every check family at once."""
    spec = CheckerSpec(
        name="req_ack_checker",
        clock="clk",
        reset=_RST_N,
        ports=[
            Signal("busy", 1),
            Signal("data", 8),
            Signal("en", 1),
            Signal("req", 1),
            Signal("ack", 1),
        ],
        checks=[
            ResetValueCheck("busy_reset", "busy", 0, 1),
            StabilityCheck("data_hold", "data", "en", 8),
            LatencyCheck("req_ack_latency", "req", "ack", 4),
        ],
    )
    _assert_compiles(generate_checker(spec), "req_ack_checker")


def test_checker_active_high_reset_compiles() -> None:
    """Reset polarity flips the guard expression — both must compile."""
    spec = CheckerSpec(
        name="ah_checker",
        clock="clk",
        reset=_RST_HIGH,
        ports=[Signal("q", 16), Signal("en", 1)],
        checks=[
            ResetValueCheck("q_reset", "q", 0, 16),
            StabilityCheck("q_hold", "q", "en", 16),
        ],
    )
    _assert_compiles(generate_checker(spec), "ah_checker")


def test_checker_wide_reset_value_compiles() -> None:
    """A non-zero, wide reset value sizes its literal correctly."""
    spec = CheckerSpec(
        name="wide_checker",
        clock="clk",
        reset=_RST_N,
        ports=[Signal("ctrl", 32)],
        checks=[ResetValueCheck("ctrl_reset", "ctrl", 0xDEAD_BEEF, 32)],
    )
    _assert_compiles(generate_checker(spec), "wide_checker")


def test_checker_latency_only_compiles() -> None:
    """The latency state machine on its own (no other families present)."""
    spec = CheckerSpec(
        name="lat_checker",
        clock="clk",
        reset=_RST_N,
        ports=[Signal("start", 1), Signal("done", 1)],
        checks=[LatencyCheck("start_done", "start", "done", 1)],
    )
    _assert_compiles(generate_checker(spec), "lat_checker")


# --------------------------------------------------------------------------- #
# scoreboard


def test_scoreboard_class_only_compiles() -> None:
    """No wrapper — a bare class at compilation-unit scope."""
    spec = ScoreboardSpec(name="sb_only", item_type="logic [7:0]")
    _assert_compiles(generate_scoreboard(spec), "sb_only")


def test_scoreboard_with_wrapper_compiles() -> None:
    """The regression this module was written for.

    ``push_expr``/``compare_expr`` reference ``data``, which is not one of the
    three implicit ports, so it must appear in ``ports``. Omitting it emits a
    module referencing an undeclared signal — which is precisely what the
    original P3-06 fixture and docs example did.
    """
    spec = ScoreboardSpec(
        name="req_ack_scoreboard",
        item_type="logic [7:0]",
        wrapper=ScoreboardWrapper(
            module_name="req_ack_scoreboard_wrap",
            clock="clk",
            push_signal="req",
            push_expr="data",
            compare_signal="ack",
            compare_expr="data",
            ports=[Signal("data", 8)],
        ),
    )
    _assert_compiles(generate_scoreboard(spec), "req_ack_scoreboard")


def test_scoreboard_wrapper_missing_port_does_not_compile() -> None:
    """Negative control: proves this gate actually catches the omission.

    Without it, a future change that made ``ports`` a no-op would leave every
    positive test above still passing.
    """
    spec = ScoreboardSpec(
        name="broken_sb",
        item_type="logic [7:0]",
        wrapper=ScoreboardWrapper(
            module_name="broken_sb_wrap",
            clock="clk",
            push_signal="req",
            push_expr="data",  # `data` deliberately not declared in ports
            compare_signal="ack",
            compare_expr="data",
        ),
    )
    result = _compile(generate_scoreboard(spec), "broken_sb")
    assert result.returncode != 0, (
        "expected verilator to reject a wrapper whose opaque expressions "
        "reference an undeclared signal; if this now compiles, either the "
        "generator started inferring ports or the gate has stopped working"
    )
    assert "data" in result.stderr


def test_scoreboard_wrapper_expr_beyond_bare_signal_compiles() -> None:
    """A real expression (not a bare signal name) over declared ports."""
    spec = ScoreboardSpec(
        name="expr_sb",
        item_type="logic [15:0]",
        wrapper=ScoreboardWrapper(
            module_name="expr_sb_wrap",
            clock="clk",
            push_signal="push_en",
            push_expr="{hi, lo}",
            compare_signal="pop_en",
            compare_expr="observed ^ 16'hA5A5",
            ports=[
                Signal("hi", 8),
                Signal("lo", 8),
                Signal("observed", 16),
            ],
        ),
    )
    _assert_compiles(generate_scoreboard(spec), "expr_sb")
