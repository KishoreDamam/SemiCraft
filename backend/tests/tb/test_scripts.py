"""P3-02 sim-script emitter tests (``semicraft_core.tb.scripts``).

The emitted run.sh / Makefile must drive the exact two-stage Verilator flow the
sim runner uses (``--timing --binary --build-jobs 1``), be deterministic, and
carry no timestamps.
"""

from __future__ import annotations

import pytest
from semicraft_core.tb import emit_makefile, emit_run_script

_TB = "edge_detector_tb.sv"
_RTL = ["edge_detector.sv"]


# --------------------------------------------------------------------------- #
# run.sh
# --------------------------------------------------------------------------- #


def test_run_script_exact_text() -> None:
    assert emit_run_script(_TB, _RTL) == (
        "#!/bin/sh\n"
        "# Compile and run the SemiCraft smoke testbench with Verilator.\n"
        "# Exits nonzero if compilation fails or any self-check $fatal()s.\n"
        "set -eu\n"
        "\n"
        "verilator --timing --binary --build-jobs 1 -Mdir obj_dir "
        "edge_detector_tb.sv edge_detector.sv\n"
        "./obj_dir/Vedge_detector_tb\n"
    )


def test_run_script_multiple_rtl_files_keep_order() -> None:
    text = emit_run_script("top_tb.sv", ["top.sv", "sub_a.sv", "sub_b.v"])
    assert "-Mdir obj_dir top_tb.sv top.sv sub_a.sv sub_b.v\n" in text
    assert "./obj_dir/Vtop_tb\n" in text


def test_run_script_mirrors_runner_flags() -> None:
    # Same invocation as semicraft_core.sim.runner.run_smoke's compile step.
    text = emit_run_script(_TB, _RTL)
    assert "verilator --timing --binary --build-jobs 1 -Mdir" in text


# --------------------------------------------------------------------------- #
# Makefile
# --------------------------------------------------------------------------- #


def test_makefile_exact_text() -> None:
    assert emit_makefile(_TB, _RTL) == (
        "# Compile and run the SemiCraft smoke testbench with Verilator.\n"
        "# `make` (or `make run`) builds and executes; `make clean` removes\n"
        "# build artefacts.\n"
        "\n"
        "TB := edge_detector_tb.sv\n"
        "RTL := edge_detector.sv\n"
        "MDIR := obj_dir\n"
        "BIN := $(MDIR)/Vedge_detector_tb\n"
        "\n"
        ".PHONY: run clean\n"
        "\n"
        "run: $(BIN)\n"
        "\t./$(BIN)\n"
        "\n"
        "$(BIN): $(TB) $(RTL)\n"
        "\tverilator --timing --binary --build-jobs 1 -Mdir $(MDIR) "
        "$(TB) $(RTL)\n"
        "\n"
        "clean:\n"
        "\trm -rf $(MDIR)\n"
    )


def test_makefile_recipes_are_tab_indented() -> None:
    for line in emit_makefile(_TB, _RTL).splitlines():
        if line.startswith((" ",)):
            pytest.fail(f"space-indented Makefile line: {line!r}")


# --------------------------------------------------------------------------- #
# determinism + input validation
# --------------------------------------------------------------------------- #


def test_emitters_deterministic() -> None:
    assert emit_run_script(_TB, _RTL) == emit_run_script(_TB, _RTL)
    assert emit_makefile(_TB, _RTL) == emit_makefile(_TB, _RTL)


@pytest.mark.parametrize("bad", ["", "dir/tb.sv", "dir\\tb.sv"])
def test_rejects_pathlike_tb_filename(bad: str) -> None:
    with pytest.raises(ValueError):
        emit_run_script(bad, _RTL)
    with pytest.raises(ValueError):
        emit_makefile(bad, _RTL)


@pytest.mark.parametrize("bad", ["a b.sv", 'x"y.sv', "x$y.sv", "x`y.sv"])
def test_rejects_shell_unsafe_rtl_filename(bad: str) -> None:
    with pytest.raises(ValueError):
        emit_run_script(_TB, [bad])
    with pytest.raises(ValueError):
        emit_makefile(_TB, [bad])
