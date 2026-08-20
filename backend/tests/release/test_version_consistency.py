"""Guards that the tool's reported version matches the release it ships as.

Why this exists: **v0.2.0 was tagged with ``VERSION = "0.1.0"``.** The release
WP bumped the docs and cut the tag but never touched ``version.py``, so every
artifact that release generated — the ``// SemiCraft v0.1.0`` banner in each RTL
file, and the provenance line in each datasheet and test plan — told users they
were running the previous version. Nothing failed, because nothing tied the
constant to the release.

``VERSION`` is not part of ``config_hash`` (which hashes only the item id and
the validated options), so a stale version does not change generated *logic* —
which is exactly why it went unnoticed for a whole release cycle.

The tie is to ``docs/RELEASE_CHECKLIST.md`` rather than to a git tag on purpose:
the checklist is a file in the tree, so this works in a shallow clone, in CI
without tags fetched, and before the tag is cut — which is when a release WP can
still fix it. Cutting a release means adding a checklist section, so the two
move together or this test fails.
"""

from __future__ import annotations

import re
from pathlib import Path

from semicraft_core.version import VERSION

_CHECKLIST = Path(__file__).resolve().parents[3] / "docs" / "RELEASE_CHECKLIST.md"
_HEADING = re.compile(r"^# SemiCraft v(\d+)\.(\d+)\.(\d+)\b", re.MULTILINE)


def _documented_versions() -> list[tuple[int, int, int]]:
    text = _CHECKLIST.read_text(encoding="utf-8")
    return [tuple(int(p) for p in m.groups()) for m in _HEADING.finditer(text)]


def test_release_checklist_is_present_and_parsable() -> None:
    assert _CHECKLIST.is_file(), f"missing release checklist at {_CHECKLIST}"
    assert _documented_versions(), (
        f"no '# SemiCraft vX.Y.Z' headings found in {_CHECKLIST}; this test "
        "cannot guard the version without them"
    )


def test_version_is_valid_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", VERSION), (
        f"VERSION={VERSION!r} is not a bare X.Y.Z string; the RTL banner and "
        "doc provenance lines interpolate it verbatim"
    )


def test_version_matches_latest_documented_release() -> None:
    """The regression that shipped in v0.2.0.

    ``VERSION`` must equal the highest version with a checklist section. If a
    release is being prepared, bump ``version.py`` and add its checklist section
    in the same change.
    """
    latest = max(_documented_versions())
    current = tuple(int(p) for p in VERSION.split("."))
    assert current == latest, (
        f"VERSION={VERSION} but the newest release documented in "
        f"{_CHECKLIST.name} is v{'.'.join(str(p) for p in latest)}. "
        "These must agree: v0.2.0 shipped with VERSION=0.1.0 because they did "
        "not, and every artifact it generated reported the wrong version. "
        "Bump version.py and add the checklist section together."
    )


def test_generated_rtl_banner_reports_current_version() -> None:
    """End-to-end: the version reaches the artifact users actually receive."""
    from semicraft_core.generate import generate_files

    result = generate_files("edge-detector", {})
    rtl = next(f for f in result.files if f.kind == "rtl")
    assert f"// SemiCraft v{VERSION}" in rtl.text

    doc = next(f for f in result.files if f.kind == "doc")
    assert f"SemiCraft {VERSION}" in doc.text


def test_pyproject_version_matches() -> None:
    """The packaging metadata is a second place the version goes stale.

    v0.2.0 shipped with ``pyproject.toml`` still at 0.1.0 as well, so anyone
    installing the backend as a package saw the wrong version too. Parsed with
    ``tomllib`` rather than a regex so a moved/reformatted field still resolves.
    """
    import tomllib

    pyproject = _CHECKLIST.resolve().parents[1] / "pyproject.toml"
    assert pyproject.is_file(), f"missing {pyproject}"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["project"]["version"] == VERSION, (
        f"pyproject version {data['project']['version']!r} != VERSION "
        f"{VERSION!r}; both must be bumped when cutting a release"
    )
