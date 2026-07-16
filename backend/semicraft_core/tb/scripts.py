"""Deterministic sim-script emitters for a generated testbench (P3-02).

Two equivalent artifacts, both driving the exact two-stage Verilator flow that
:func:`semicraft_core.sim.runner.run_smoke` uses (same flags, same layout):

1. ``verilator --timing --binary --build-jobs 1 -Mdir obj_dir <tb> <rtl...>``
   compiles the testbench + RTL into ``obj_dir/V<top>``;
2. the produced binary is executed — it exits nonzero on any failed check
   (``$fatal``) and prints the pass banner before ``$finish`` on success.

The scripts are for users running the generated bundle *outside* SemiCraft (the
in-product sim path is the runner). Output is deterministic: identical inputs in,
identical text out — no timestamps, no environment probing. POSIX ``sh`` and
POSIX ``make`` only.
"""

from __future__ import annotations

from collections.abc import Sequence

__all__ = ["emit_run_script", "emit_makefile"]

# Verilator's -Mdir: build artefacts + the V<top> executable land here
# (mirrors the runner, which uses a temp dir for the same role).
_MDIR = "obj_dir"

_VERILATOR_FLAGS = "--timing --binary --build-jobs 1"


def _top_module(tb_filename: str) -> str:
    """The TB top-module name Verilator infers: the tb filename's stem.

    ``render_tb`` names the module after the file (``foo_tb.sv`` holds
    ``module foo_tb``), and Verilator's ``--binary`` mode drops the executable
    at ``<Mdir>/V<top>``.
    """
    name = tb_filename.rsplit(".", 1)[0]
    if not name or "/" in tb_filename or "\\" in tb_filename:
        raise ValueError(
            f"tb_filename must be a bare relative filename, got {tb_filename!r}"
        )
    return name


def emit_run_script(tb_filename: str, rtl_filenames: list[str]) -> str:
    """A POSIX ``run.sh`` compiling and executing the smoke testbench."""
    top = _top_module(tb_filename)
    sources = _sources(tb_filename, rtl_filenames)
    return (
        "#!/bin/sh\n"
        "# Compile and run the SemiCraft smoke testbench with Verilator.\n"
        "# Exits nonzero if compilation fails or any self-check $fatal()s.\n"
        "set -eu\n"
        "\n"
        f"verilator {_VERILATOR_FLAGS} -Mdir {_MDIR} {sources}\n"
        f"./{_MDIR}/V{top}\n"
    )


def emit_makefile(tb_filename: str, rtl_filenames: list[str]) -> str:
    """A POSIX ``Makefile`` equivalent of :func:`emit_run_script`."""
    top = _top_module(tb_filename)
    rtl = " ".join(_checked(f) for f in rtl_filenames)
    return (
        "# Compile and run the SemiCraft smoke testbench with Verilator.\n"
        "# `make` (or `make run`) builds and executes; `make clean` removes\n"
        "# build artefacts.\n"
        "\n"
        f"TB := {_checked(tb_filename)}\n"
        f"RTL := {rtl}\n"
        f"MDIR := {_MDIR}\n"
        f"BIN := $(MDIR)/V{top}\n"
        "\n"
        ".PHONY: run clean\n"
        "\n"
        "run: $(BIN)\n"
        "\t./$(BIN)\n"
        "\n"
        "$(BIN): $(TB) $(RTL)\n"
        f"\tverilator {_VERILATOR_FLAGS} -Mdir $(MDIR) $(TB) $(RTL)\n"
        "\n"
        "clean:\n"
        "\trm -rf $(MDIR)\n"
    )


def _checked(filename: str) -> str:
    """Reject filenames the scripts cannot safely interpolate verbatim."""
    if not filename or any(c in filename for c in ' \t\n"\'$`\\'):
        raise ValueError(f"unsafe filename for sim script: {filename!r}")
    return filename


def _sources(tb_filename: str, rtl_filenames: Sequence[str]) -> str:
    return " ".join(_checked(f) for f in (tb_filename, *rtl_filenames))
