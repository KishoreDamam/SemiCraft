"""Golden-matrix pytest plumbing (IMPLEMENTATION_PLAN.md §5 WP-08).

Auto-discovers every ``backend/tests/golden/<snippet-id>/cases.py`` present at
test-collection time and exposes them to ``test_snapshots.py`` /
``test_determinism.py`` / ``test_lint_gate.py`` via the fixtures/functions
below. Sibling WP-05x agents drop in ``cases.py`` files continuously; nothing
here hard-codes a snippet list.

``cases.py`` contract (fixed, do not change): a module-level ``CASES: dict[str,
dict]`` mapping case-name -> options dict, exactly as it would be POSTed to
``/api/v1/generate`` (e.g. ``{"language": "sv", "width": 16}``). A case may
pin ``"language"`` explicitly; if it omits it, the runner exercises the case
for *both* languages under distinct snapshot names.

``--update-golden``: pytest flag that makes the snapshot test (re)write the
golden file instead of asserting equality. Never set in CI (WP-04 wires the
CI lint gate over the committed goldens; regenerating them is a local,
reviewed action).
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

import pytest

GOLDEN_ROOT = Path(__file__).parent


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help=(
            "(Re)write golden snapshot files under backend/tests/golden/<id>/ "
            "instead of asserting against them. Never use in CI."
        ),
    )


@dataclass(frozen=True, slots=True)
class GoldenCase:
    """One (snippet, case, language) triple to snapshot/lint/determinism-check."""

    snippet_id: str
    case_name: str
    options: dict
    language: str  # "sv" | "verilog" — always resolved, even if the case omitted it
    snapshot_name: str  # e.g. "defaults.sv" — filename within tests/golden/<id>/

    @property
    def snapshot_path(self) -> Path:
        return GOLDEN_ROOT / self.snippet_id / self.snapshot_name

    @property
    def resolved_options(self) -> dict:
        """Options dict with ``language`` pinned to this case's resolved language."""
        return {**self.options, "language": self.language}


def _extension(language: str) -> str:
    return "sv" if language == "sv" else "v"


def discover_snippet_dirs() -> list[Path]:
    """Every immediate subdirectory of ``tests/golden`` containing a ``cases.py``."""
    if not GOLDEN_ROOT.is_dir():
        return []
    dirs = [
        p
        for p in GOLDEN_ROOT.iterdir()
        if p.is_dir() and not p.name.startswith("_") and (p / "cases.py").is_file()
    ]
    return sorted(dirs, key=lambda p: p.name)


def _load_cases_module(snippet_dir: Path):
    spec = importlib.util.spec_from_file_location(
        f"_golden_cases_{snippet_dir.name}", snippet_dir / "cases.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_golden_cases() -> list[GoldenCase]:
    """Flatten every discovered ``cases.py`` into concrete (snippet, case, lang) cases.

    A case that pins ``language`` yields exactly one :class:`GoldenCase`; a case
    that omits it yields two (sv and verilog), with distinct snapshot names.
    """
    results: list[GoldenCase] = []
    for snippet_dir in discover_snippet_dirs():
        snippet_id = snippet_dir.name
        module = _load_cases_module(snippet_dir)
        cases: dict[str, dict] = getattr(module, "CASES", {})
        for case_name, options in cases.items():
            pinned_language = options.get("language")
            languages = [pinned_language] if pinned_language else ["sv", "verilog"]
            for language in languages:
                ext = _extension(language)
                results.append(
                    GoldenCase(
                        snippet_id=snippet_id,
                        case_name=case_name,
                        options=options,
                        language=language,
                        snapshot_name=f"{case_name}.{ext}",
                    )
                )
    return results


def golden_case_id(case: GoldenCase) -> str:
    return f"{case.snippet_id}/{case.case_name}[{case.language}]"
