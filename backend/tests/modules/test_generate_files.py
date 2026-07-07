"""Multi-file generation entry point (API v2, Appendix A.1/A.3).

Covers generate_files() for a snippet (one rtl file) and a module (rtl + doc,
no tb while EMIT_TB is off), plus the doc file's port-table content.
"""

from __future__ import annotations

from semicraft_core import generate
from semicraft_core.generate import (
    EMIT_TB,
    GeneratedFile,
    GenerateFilesResult,
    generate_files,
)

# --------------------------------------------------------------------------- #
# snippet path: a single rtl file
# --------------------------------------------------------------------------- #


def test_snippet_yields_single_rtl_file() -> None:
    res = generate_files("counter", {})
    assert isinstance(res, GenerateFilesResult)
    assert len(res.files) == 1
    (rtl,) = res.files
    assert isinstance(rtl, GeneratedFile)
    assert rtl.kind == "rtl"
    assert rtl.path == "counter.sv"
    assert "module counter" in rtl.text


def test_snippet_rtl_matches_single_file_generate() -> None:
    """The rtl file text is byte-identical to the v1 generate() output."""
    v1 = generate("counter", {"width": 16})
    files = generate_files("counter", {"width": 16})
    (rtl,) = files.files
    assert rtl.text == v1.code
    assert files.config_hash == v1.config_hash


def test_snippet_fragment_mode_filename() -> None:
    res = generate_files("counter", {"include_wrapper": False})
    (rtl,) = res.files
    assert rtl.path == "counter_fragment.sv"


def test_snippet_verilog_language_reported() -> None:
    res = generate_files("counter", {"language": "verilog"})
    assert res.language == "verilog"
    assert res.files[0].path == "counter.v"


# --------------------------------------------------------------------------- #
# module path: rtl + doc, no tb (EMIT_TB off)
# --------------------------------------------------------------------------- #


def test_module_yields_rtl_and_doc_no_tb() -> None:
    res = generate_files("edge-detector", {})
    kinds = [f.kind for f in res.files]
    assert kinds == ["rtl", "doc"]  # rtl first, then doc; no tb
    assert not EMIT_TB  # sanity: TB emission is still feature-flagged off
    assert all(f.kind != "tb" for f in res.files)


def test_module_rtl_file() -> None:
    res = generate_files("edge-detector", {})
    rtl = next(f for f in res.files if f.kind == "rtl")
    assert rtl.path == "edge_detector.sv"
    assert "module edge_detector" in rtl.text


def test_module_doc_file_basics() -> None:
    res = generate_files("edge-detector", {})
    doc = next(f for f in res.files if f.kind == "doc")
    assert doc.path == "edge_detector.md"
    text = doc.text
    # title, purpose, config hash stamp
    assert text.startswith("# Edge Detector")
    assert res.config_hash in text
    # section headers
    assert "## Ports" in text
    assert "## Configuration" in text
    assert "## Assumptions" in text
    assert "## Limitations" in text


def test_module_doc_contains_grouped_port_table() -> None:
    res = generate_files("edge-detector", {})
    doc = next(f for f in res.files if f.kind == "doc").text
    # Grouped headings from port_groups.
    assert "### Clocking" in doc
    assert "### Data" in doc
    # A markdown table with every port, direction filled from the explanation.
    assert "| Port | Direction | Description |" in doc
    for port in ("clk", "rst_n", "d", "pulse"):
        assert f"| `{port}` |" in doc
    # The reset row is not empty (port_groups reset name joins the explanation).
    rst_row = next(line for line in doc.splitlines() if "| `rst_n` |" in line)
    assert rst_row.count("|") == 4
    cells = [c.strip() for c in rst_row.strip("|").split("|")]
    assert cells[2]  # description cell populated


def test_module_doc_reflects_options() -> None:
    combo = generate_files(
        "edge-detector", {"detect": "falling", "registered_output": False}
    )
    doc = next(f for f in combo.files if f.kind == "doc").text
    assert "falling" in doc
    assert "combinational" in doc.lower()


def test_module_config_hash_matches_v1_generate() -> None:
    v1 = generate("edge-detector", {"detect": "both"})
    res = generate_files("edge-detector", {"detect": "both"})
    assert res.config_hash == v1.config_hash
    rtl = next(f for f in res.files if f.kind == "rtl")
    assert rtl.text == v1.code


def test_generate_files_is_deterministic() -> None:
    a = generate_files("edge-detector", {"detect": "both", "width": 4})
    b = generate_files("edge-detector", {"detect": "both", "width": 4})
    assert [(f.path, f.kind, f.text) for f in a.files] == [
        (f.path, f.kind, f.text) for f in b.files
    ]
