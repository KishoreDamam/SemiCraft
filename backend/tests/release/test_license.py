"""Guards the repository's own license, and the boundary around generated output.

Two separate guards live here because two separate things can rot.

**The license file itself.** ``README.md`` promised a repository license
"if/when added" from v0.1.0 through v0.4.0 and none was ever added, so for four
releases a public repository granted nobody the right to use, fork or contribute
to it. Nothing failed, because nothing tied the README's claim to a file. This
ties them: the LICENSE must exist, must be the license the README and
``pyproject.toml`` both name, and must not still carry a template's placeholder
copyright line.

**The output boundary.** SemiCraft's whole proposition is that the RTL it
generates is the user's, unencumbered — no attribution, no notice file, no MIT
obligation riding along into a proprietary design. That is a *documentation*
guarantee: it lives in one README section and nowhere in the code. A future
README rewrite (release WP R-02 is exactly that) drops it in one careless edit,
and the loss is silent — no test fails, no user complains, and the project has
quietly changed what it promises about every file it has ever generated. So the
claim is asserted here, at the level of "the README must still say this", which
is the only level available for a promise made in prose.

Deliberately *not* asserted: the exact wording. The sentences may be rewritten
freely; what may not vanish is the distinction between the tool's license and
the output's terms.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_LICENSE = _ROOT / "LICENSE"
_README = _ROOT / "README.md"
_PYPROJECT = _ROOT / "pyproject.toml"

_SPDX = "MIT"

# A copyright line with a real holder. Template placeholders — "<year>",
# "[fullname]", "YOUR NAME" — are the classic way an MIT file ships unfinished.
_COPYRIGHT = re.compile(r"^Copyright \(c\) (\d{4})(?:-\d{4})? +(\S.*\S)$", re.MULTILINE)
_PLACEHOLDER = re.compile(r"[<\[]|\byour name\b|\bfullname\b|\bauthor\b", re.IGNORECASE)


def _license_text() -> str:
    return _LICENSE.read_text(encoding="utf-8")


def _readme_text() -> str:
    return _README.read_text(encoding="utf-8")


# --- the license file exists and is what it claims to be ---------------------


def test_license_file_exists() -> None:
    assert _LICENSE.is_file(), (
        f"missing {_LICENSE}. A public repository with no license grants no "
        "rights to use, fork, redistribute or contribute."
    )


def test_license_is_the_mit_license() -> None:
    text = _license_text()
    assert text.lstrip().startswith("MIT License"), "LICENSE does not open as the MIT License"
    # The two clauses that make MIT what it is: the grant and the disclaimer.
    assert "Permission is hereby granted, free of charge" in text
    assert "WITHOUT WARRANTY OF ANY KIND" in text
    assert "The above copyright notice and this permission notice shall be included" in text


def test_license_names_a_real_copyright_holder() -> None:
    match = _COPYRIGHT.search(_license_text())
    assert match is not None, (
        "LICENSE has no 'Copyright (c) <year> <holder>' line; an MIT file "
        "without one is unattributed"
    )
    holder = match.group(2)
    assert not _PLACEHOLDER.search(holder), (
        f"LICENSE copyright holder {holder!r} still looks like a template "
        "placeholder rather than a name"
    )


# --- the file, the packaging metadata and the README agree -------------------


def test_pyproject_declares_the_same_license() -> None:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    declared = data["project"]["license"]
    assert declared == _SPDX, f"pyproject declares {declared!r}, LICENSE is {_SPDX}"
    assert "LICENSE" in data["project"]["license-files"], (
        "pyproject does not ship LICENSE in built distributions"
    )


def test_readme_names_the_license_and_links_the_file() -> None:
    text = _readme_text()
    assert f"{_SPDX} License" in text, f"README never names the {_SPDX} License"
    assert "(LICENSE)" in text, "README does not link the LICENSE file"


def test_readme_no_longer_promises_a_license_it_does_not_have() -> None:
    """The exact defect this file exists to stop recurring."""
    text = _readme_text().lower()
    for phrase in ("if/when added", "if and when added", "licensed separately (see"):
        assert phrase not in text, (
            f"README still says {phrase!r} — it described the repository as "
            "unlicensed for four releases"
        )


# --- the output boundary survives a README rewrite ---------------------------


def test_readme_states_that_generated_output_is_not_covered_by_the_repo_license() -> None:
    text = _readme_text().lower()
    assert "generated output" in text or "generated code" in text
    # The substantive promise: the MIT terms do not attach to what users generate.
    assert "do not attach to it" in text or "not covered by" in text, (
        "README no longer states that the repository's license does not attach "
        "to generated output. That promise is why users can put SemiCraft RTL "
        "into proprietary designs; it exists only in prose, so only a test "
        "keeps it from being edited away."
    )


def test_readme_keeps_the_as_is_disclaimer_on_generated_output() -> None:
    text = _readme_text()
    assert "as-is" in text.lower()
    assert "no warranty" in text.lower() or "without warranty" in text.lower()


def test_readme_disclaimer_quotes_the_single_sourced_constant() -> None:
    """The README's quoted disclaimer must be the one actually stamped into files."""
    from semicraft_core.license import DISCLAIMER

    # The README carries it as a wrapped markdown blockquote, so strip the "> "
    # markers before collapsing whitespace — otherwise a mid-sentence line break
    # leaves a stray ">" inside the text and no verbatim quote can ever match.
    unquoted = "\n".join(
        re.sub(r"^\s*>\s?", "", line) for line in _readme_text().splitlines()
    )
    readme_flat = " ".join(unquoted.split())
    assert " ".join(DISCLAIMER.split()) in readme_flat, (
        "README quotes a disclaimer that differs from semicraft_core.license."
        "DISCLAIMER, the text actually stamped into every generated file"
    )
