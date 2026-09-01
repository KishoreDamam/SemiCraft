"""Every example instantiation lints `-Wall` clean against its IP (P4-11).

This is the gate that makes an example worth shipping. A copy-pasteable snippet
with a wrong port name, a stale width, or a dropped connection is worse than no
snippet, because a reader trusts it — and nothing about generating one into a
markdown file would ever catch that.

So the example is a real HDL file and this gate compiles it *with* the IP it
instantiates, at the same zero-warning bar the RTL itself has to clear. If a
port is renamed, retyped, or dropped, the example stops linting and CI goes
red.

Both files are copied into a temp directory under **module-matching names**
before Verilator sees them. Golden files are named by case
(``defaults.sv_example.sv``), and Verilator's `DECLFILENAME` warning fires when
a file's name does not match the module it declares — a warning about this
harness, not about the generated code, and one that would otherwise mask every
real finding at `-Wall`.

Skips when Verilator is absent (the Windows dev host).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from .conftest import GOLDEN_ROOT

_HAS_VERILATOR = shutil.which("verilator") is not None
_MODULE_NAME_RE = re.compile(r"^\s*module\s+(\w+)", re.MULTILINE)
_TIMEOUT_S = 90


def discover_example_goldens() -> list[Path]:
    """Every committed ``<case>.<ext>_example.<ext>`` golden."""
    return sorted(
        p
        for p in GOLDEN_ROOT.glob("*/*_example.*")
        if p.suffix in (".sv", ".v")
    )


def _matching_rtl(example_path: Path) -> Path:
    """The IP golden an example pairs with.

    ``<case>.<ext>_example.<ext>`` pairs with ``<case>.<ext>`` beside it — the
    same pairing rule the TB compile gate uses.
    """
    stem = example_path.name
    marker = f"_example{example_path.suffix}"
    assert stem.endswith(marker)
    return example_path.with_name(stem[: -len(marker)])


def _module_name(path: Path) -> str:
    match = _MODULE_NAME_RE.search(path.read_text(encoding="utf-8"))
    assert match is not None, f"{path} declares no module"
    return match.group(1)


_EXAMPLES = discover_example_goldens()
_IDS = [str(p.relative_to(GOLDEN_ROOT)) for p in _EXAMPLES]


def test_examples_are_actually_committed() -> None:
    """A glob that silently matches nothing turns this whole file into a no-op."""
    assert _EXAMPLES, (
        "no example goldens found under backend/tests/golden/*/; run "
        "test_snapshots.py --update-golden"
    )


@pytest.mark.skipif(not _HAS_VERILATOR, reason="verilator not installed on this host")
@pytest.mark.parametrize("example_path", _EXAMPLES, ids=_IDS)
def test_golden_example_lints_clean(example_path: Path) -> None:
    rtl_path = _matching_rtl(example_path)
    assert rtl_path.is_file(), (
        f"{example_path} has no matching IP golden at {rtl_path} "
        "(example/rtl goldens must be regenerated together)"
    )

    verilator = shutil.which("verilator")
    assert verilator is not None  # guarded by skipif

    suffix = example_path.suffix
    language_flags = ["-sv"] if suffix == ".sv" else []

    with tempfile.TemporaryDirectory(prefix="semicraft-example-") as tmpdir:
        tmp = Path(tmpdir)
        top = _module_name(example_path)
        example_copy = tmp / f"{top}{suffix}"
        rtl_copy = tmp / f"{_module_name(rtl_path)}{suffix}"
        example_copy.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
        rtl_copy.write_text(rtl_path.read_text(encoding="utf-8"), encoding="utf-8")

        proc = subprocess.run(
            [
                verilator,
                "--lint-only",
                "-Wall",
                *language_flags,
                "--top-module",
                top,
                str(example_copy),
                str(rtl_copy),
            ],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_S,
        )

    assert proc.returncode == 0, (
        f"{example_path.relative_to(GOLDEN_ROOT)} did not lint clean against "
        f"{rtl_path.name}:\n{proc.stderr}"
    )
    assert "%Warning" not in proc.stderr, (
        f"{example_path.relative_to(GOLDEN_ROOT)} produced warnings:\n{proc.stderr}"
    )
