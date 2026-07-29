"""Test-plan / verification-checklist document generator (Phase 3, P3-07).

``generate_testplan(item, opts, rtl_module, explanation, config_hash_value)``
renders a markdown test-plan document for a ``ModuleDef`` from metadata that
already exists — nothing new is added to :class:`~.modules.contract.ModuleDef`
(CLAUDE.md workflow rule: frozen-contract changes need an explicit recorded
decision, not a silent addition). The three sources are:

- ``item.explain(opts)`` (:class:`~.snippets.contract.ExplanationDoc`) — the
  human-written purpose/configuration/reset/limitations prose;
- ``item.port_groups(opts)`` (:class:`~.modules.contract.PortGroup`) — the same
  clocking/data grouping the datasheet (``_module_doc``) uses;
- ``item.tb_spec(opts)`` (:class:`~.modules.contract.TbSpec`) — the directed
  smoke-TB recipe :func:`semicraft_core.tb.generate_tb.generate_tb` actually
  renders.

Document structure and why
---------------------------

The wiring point (:func:`semicraft_core.generate.generate_files`) already calls
``generate_tb`` to render the *TB itself*; this module never re-renders TB text,
it only re-derives the same facts ``generate_tb`` derives (checked-cycle
grouping, styled names, reset polarity) so every claim below is guaranteed true
of the TB actually emitted alongside it. Sections, in order:

1. **Title + purpose + provenance** — mirrors ``generate._module_doc``'s
   ``config_hash`` provenance line, so the two docs read as a matched pair.
2. **Features Under Test** — ``explanation.purpose`` plus
   ``explanation.configuration``/``reset_behavior``/``enable_behavior``: the
   *intent* the module claims, restated as a checklist a reviewer can tick off
   against the RTL.
3. **Test Plan table** — one row per *directed cycle that has a check*, not one
   row per ``Check``. ``generate_tb`` itself groups checks by cycle
   (``checks_by_cycle``) because that is the real unit of TB action: a cycle's
   stimulus is driven once, then every check attached to that cycle samples
   after the same settle delay. Mirroring that grouping is what "group them
   sensibly" (P3-07 brief) means concretely, and it scales correctly to a
   module with many checks without inventing a semantic grouping the metadata
   doesn't actually contain.
4. **Coverage / Stimulus Summary** — clock/reset/run-length facts, declared
   ``port_constraints``, and — reusing ``port_groups()`` for the same grouping
   the datasheet uses — a per-port Driven/Checked table ending in an explicit
   **Gaps** list. This is deliberately the most detailed section: an input port
   that never appears in any vector is only ever driven to the constant 0 (the
   TB's blanket initialisation) and is never varied, and an output port with no
   ``Check`` is wired to the DUT but never sampled by anything self-checking.
   Both are real, user-relevant gaps and are reported plainly rather than
   folded into vague prose.
5. **Assertions (SVA)** — when ``tb_spec.assertion_spec`` is set, the *actual*
   generated property list (via ``assertions.generate.generate_assertions`` —
   the same call ``generate_tb`` makes) is tabulated, not a re-derivation of the
   spec's item types; this guarantees the table can never drift from what the
   TB emits. When it is ``None`` (true of every module shipped as of P3-07),
   the document says so plainly instead of describing hypothetical SVA.
6. **Not Covered / Limitations** — ``explanation.limitations`` verbatim, plus a
   small fixed set of limitations that are structurally true of every
   ``generate_tb`` output (directed not randomized, single default
   parameterization, single clock/reset domain) and one dynamically-derived
   note when no ``Check`` samples the first post-reset cycle.

A module whose ``tb_spec(opts).clock`` is ``None`` gets no smoke TB at all
(``generate_tb`` returns ``""``); this generator still produces a test-plan
document for it (the doc-file/tb-file existence are independent in
``generate_files``), but its Test Plan / Coverage sections say plainly that no
TB is generated rather than describing a TB that does not exist.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .modules.contract import Check, PortGroup, TbSpec
from .render.style import StyleOptions, build_name_map
from .version import VERSION

if TYPE_CHECKING:
    from .ir.nodes import Module
    from .snippets.contract import ExplanationDoc

__all__ = ["generate_testplan"]


# ---------------------------------------------------------------------------
# Style / name resolution (kept in step with generate_tb._style_from_options
# and generate._style_from_options so displayed names match the rendered TB)
# ---------------------------------------------------------------------------


def _style_from_options(opts) -> StyleOptions:
    naming = opts.naming
    return StyleOptions(
        naming=naming.convention,
        prefix=naming.prefix,
        suffix=naming.suffix,
        comment_verbosity=opts.comment_verbosity,
    )


def _name_map(rtl_module: Module, opts) -> dict[str, str]:
    return build_name_map(rtl_module, _style_from_options(opts))


# ---------------------------------------------------------------------------
# Features Under Test
# ---------------------------------------------------------------------------


def _features_section(explanation: ExplanationDoc) -> list[str]:
    lines = ["## Features Under Test", ""]
    if explanation.configuration:
        lines.append("Configuration exercised by this test plan:")
        lines.append("")
        lines.extend(f"- {item}" for item in explanation.configuration)
        lines.append("")
    lines.append(f"**Reset behavior:** {explanation.reset_behavior}")
    lines.append("")
    if explanation.enable_behavior is not None:
        lines.append(f"**Enable behavior:** {explanation.enable_behavior}")
        lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Test Plan table (grouped by checked cycle, mirroring generate_tb)
# ---------------------------------------------------------------------------


def _checks_by_cycle(checks: list[Check]) -> dict[int, list[Check]]:
    grouped: dict[int, list[Check]] = {}
    for chk in checks:
        grouped.setdefault(chk.cycle, []).append(chk)
    return grouped


def _stimulus_text(spec: TbSpec, styled, cycle: int) -> str:
    if cycle < len(spec.vectors) and spec.vectors[cycle]:
        drives = ", ".join(
            f"{styled(sig)}={val}" for sig, val in sorted(spec.vectors[cycle].items())
        )
        return f"drive {drives}"
    return "no new stimulus this cycle (holds prior-driven values)"


def _test_plan_section(spec: TbSpec, styled) -> list[str]:
    lines = ["## Test Plan", ""]

    if spec.clock is None:
        lines.append(
            "This module's `TbSpec.clock` is `None`, so `generate_tb` emits no "
            "testbench at all (`generate_files` produces no `tb` file). Nothing "
            "below is exercised as SystemVerilog."
        )
        lines.append("")
        return lines

    if not spec.checks:
        lines.append(
            "`TbSpec.checks` is empty: the generated smoke TB drives the "
            "stimulus vectors below and prints `SMOKE PASS` unconditionally — "
            "it performs **no self-checking assertions**. A passing run only "
            "proves the DUT did not hang or diverge in simulation time, not "
            "that any output value is correct."
        )
        lines.append("")
        return lines

    grouped = _checks_by_cycle(list(spec.checks))
    lines.append(
        "One row per directed cycle that carries a `Check` (cycle indices are "
        "0-based, counted from the first cycle after reset release — matching "
        "`generate_tb`'s own `checks_by_cycle` grouping). Every row is a "
        "directed, self-checking assertion emitted as an "
        "`if (sig !== expected) $fatal(...)` in the generated TB."
    )
    lines.append("")
    lines.append("| ID | Feature / Intent | Stimulus | Expected Result | Status |")
    lines.append("|---|---|---|---|---|")
    for idx, cycle in enumerate(sorted(grouped), start=1):
        row_checks = grouped[cycle]
        signals = ", ".join(f"`{styled(c.signal)}`" for c in _unique_signals(row_checks))
        intent = f"Cycle {cycle}: expected value of {signals}"
        stimulus = f"cycle {cycle}: {_stimulus_text(spec, styled, cycle)}"
        expected = "; ".join(f"{styled(c.signal)} == {c.expected}" for c in row_checks)
        status = "Directed check in generated TB (`$fatal` on mismatch)"
        tp_id = f"TP-{idx:02d}"
        lines.append(f"| {tp_id} | {intent} | {stimulus} | {expected} | {status} |")
    lines.append("")
    return lines


def _unique_signals(checks: list[Check]) -> list[Check]:
    """First `Check` per distinct signal, in first-seen order (for the
    Feature/Intent cell — avoids repeating a signal name that appears twice
    at the same cycle, which cannot happen today but costs nothing to guard)."""
    seen: set[str] = set()
    out: list[Check] = []
    for chk in checks:
        if chk.signal not in seen:
            seen.add(chk.signal)
            out.append(chk)
    return out


# ---------------------------------------------------------------------------
# Coverage / Stimulus Summary
# ---------------------------------------------------------------------------


def _n_cycles(spec: TbSpec) -> int:
    max_check_cycle = max((c.cycle for c in spec.checks), default=-1)
    return max(len(spec.vectors), max_check_cycle + 1)


def _clock_reset_lines(spec: TbSpec, styled) -> list[str]:
    lines = []
    if spec.clock is None:
        lines.append("- **Clock:** none — this module is combinational/unclocked; "
                      "no smoke TB is generated.")
        return lines
    lines.append(f"- **Clock:** `{styled(spec.clock)}` — free-running, `#5` half-period.")
    if spec.reset is not None:
        lines.append(
            f"- **Reset:** `{styled(spec.reset)}` — held asserted for "
            f"{spec.reset_cycles} cycle(s) before the first directed vector."
        )
    else:
        lines.append("- **Reset:** none — this module has no reset port; no reset "
                      "sequencing is applied by the TB.")
    n = _n_cycles(spec)
    v = len(spec.vectors)
    if n > v:
        lines.append(
            f"- **Directed run length:** {v} vector cycle(s) in `TbSpec.vectors`, "
            f"extended to {n} cycle(s) because a `Check` targets a later cycle."
        )
    else:
        lines.append(f"- **Directed run length:** {v} vector cycle(s).")
    return lines


def _constraints_lines(spec: TbSpec, styled) -> list[str]:
    if not spec.port_constraints:
        return [
            "- **Port value constraints:** none declared — every driven value is "
            "only masked to its port's bit width, not clamped to a sub-range."
        ]
    lines = ["- **Port value constraints:**"]
    for name in sorted(spec.port_constraints):
        c = spec.port_constraints[name]
        lo = "unbounded" if c.min_value is None else str(c.min_value)
        hi = "unbounded" if c.max_value is None else str(c.max_value)
        lines.append(f"  - `{styled(name)}`: [{lo}, {hi}]")
    return lines


def _port_coverage_table(
    group: PortGroup,
    ports_by_name: dict[str, object],
    spec: TbSpec,
    styled,
    driven_signals: set[str],
    checked_signals: set[str],
) -> tuple[list[str], list[str]]:
    """Coverage table rows for one ``PortGroup`` plus any gap bullets it finds.

    Returns ``(table_lines, gap_bullets)``.
    """
    rows = ["| Port | Direction | Driven | Checked |", "|---|---|---|---|"]
    gaps: list[str] = []
    for port_name in group.ports:
        # `port_groups()` lists canonical IR port names *except* for the reset
        # port, which each module's own ``_reset_port_name`` helper already
        # suffixes with "_n" for an active-low reset (documentation-only
        # convention, matching the datasheet's ``_module_doc``/``explain()``
        # join key) — so it never equals the canonical ``TbSpec.reset`` string
        # directly for an active-low module. Match both forms, and display the
        # role via ``styled(spec.clock)``/``styled(spec.reset)`` (resolved
        # through the real name map) rather than ``styled(port_name)``, which
        # would be a pass-through no-op for an already-suffixed "rst_n" and so
        # silently drop any user prefix/suffix/convention.
        if port_name == spec.clock:
            rows.append(f"| `{styled(spec.clock)}` | clock | free-running | n/a |")
            continue
        if spec.reset is not None and port_name in (spec.reset, f"{spec.reset}_n"):
            rows.append(f"| `{styled(spec.reset)}` | reset | reset sequence only | n/a |")
            continue

        display = styled(port_name)
        port = ports_by_name.get(port_name)
        direction = port.dir.value if port is not None else "input"
        is_checked = port_name in checked_signals
        checked_cell = "yes" if is_checked else "no"

        if direction == "output":
            driven_cell = "n/a (output)"
            if not is_checked:
                gaps.append(
                    f"`{display}` is an output that no `Check` samples — it is "
                    "wired to the DUT but never inspected by the self-checking TB."
                )
        else:
            is_driven = port_name in driven_signals
            if is_driven:
                driven_cell = "yes (varies across the run)"
            else:
                driven_cell = "no — held at 0 for the entire run"
                gaps.append(
                    f"`{display}` is an input that never appears in any "
                    "`TbSpec` vector — it is only ever driven to the constant 0 "
                    "the TB initialises every input to, and is never varied."
                )

        rows.append(f"| `{display}` | {direction} | {driven_cell} | {checked_cell} |")
    return rows, gaps


def _coverage_section(
    item, opts, spec: TbSpec, rtl_module: Module, styled
) -> list[str]:
    lines = ["## Coverage / Stimulus Summary", ""]
    lines.extend(_clock_reset_lines(spec, styled))
    if spec.clock is not None:
        lines.extend(_constraints_lines(spec, styled))
    lines.append("")

    if spec.clock is None:
        return lines

    driven_signals = {sig for vec in spec.vectors for sig in vec}
    checked_signals = {c.signal for c in spec.checks}
    ports_by_name = {p.name: p for p in rtl_module.ports}

    lines.append("### Ports exercised")
    lines.append("")
    all_gaps: list[str] = []
    for group in item.port_groups(opts):
        lines.append(f"#### {group.name}")
        lines.append("")
        rows, gaps = _port_coverage_table(
            group, ports_by_name, spec, styled, driven_signals, checked_signals
        )
        lines.extend(rows)
        lines.append("")
        all_gaps.extend(gaps)

    if not spec.checks:
        all_gaps.insert(
            0,
            "No `Check` is defined at all — see the Test Plan section: this TB "
            "self-checks nothing.",
        )

    lines.append("**Gaps:**")
    lines.append("")
    if all_gaps:
        lines.extend(f"- {g}" for g in all_gaps)
    else:
        lines.append(
            "- None found: every port is either driven with varying values or "
            "is an output sampled by at least one `Check`."
        )
    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Assertions (SVA)
# ---------------------------------------------------------------------------


def _assertions_section(spec: TbSpec) -> list[str]:
    lines = ["## Assertions (SVA)", ""]
    if spec.assertion_spec is None:
        lines.append(
            "`TbSpec.assertion_spec` is `None`: no concurrent SVA assertions "
            "are generated for this module. The Test Plan above is the entire "
            "self-checking surface of the generated TB."
        )
        lines.append("")
        return lines

    # Lazy import: mirrors semicraft_core.tb.generate_tb's own lazy import of
    # this same function, avoiding a module-load-time cycle
    # (assertions -> tb.nodes -> tb/__init__ -> tb.generate_tb).
    from .assertions.generate import generate_assertions

    props = generate_assertions(spec.assertion_spec)
    lines.append(
        "The properties below are the *actual* output of "
        "`assertions.generate_assertions(tb_spec.assertion_spec)` — the same "
        "call `generate_tb` makes — so this table cannot drift from the "
        "concurrent-assertion block the TB emits."
    )
    lines.append("")
    lines.append("| Name | Property | Clock | Guard |")
    lines.append("|---|---|---|---|")
    for p in props:
        guard = f"`disable iff ({p.disable_iff})`" if p.disable_iff else "none"
        lines.append(f"| `{p.name}` | `{p.property_text}` | `{p.clock}` | {guard} |")
    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Not Covered / Limitations
# ---------------------------------------------------------------------------


def _limitations_section(explanation: ExplanationDoc, spec: TbSpec) -> list[str]:
    lines = ["## Not Covered / Limitations", ""]
    for limit in explanation.limitations:
        lines.append(f"- {limit}")

    if spec.clock is None:
        lines.append(
            "- This module has no clock, so no smoke TB is generated at all — "
            "none of the metadata above is ever executed as SystemVerilog."
        )
        lines.append("")
        return lines

    lines.append(
        "- Directed, not randomized: the smoke TB only runs the fixed vectors "
        "in `TbSpec.vectors`; no constrained-random or exhaustive stimulus is "
        "attempted."
    )
    lines.append(
        "- Default parameterization only: the generated TB instantiates the "
        "DUT with no parameter overrides, so only the exact configuration used "
        "to generate this file is exercised. A different parameterization of "
        "the same RTL is not covered by this TB."
    )
    lines.append(
        "- Single clock/reset domain only: this TB drives one free-running "
        "clock and (if present) one reset; it performs no clock-domain-"
        "crossing verification."
    )
    if spec.checks and min(c.cycle for c in spec.checks) != 0:
        lines.append(
            "- No `Check` samples cycle 0 (the first cycle after reset "
            "release): reset behavior runs structurally but is not directly "
            "self-checked by this TB."
        )
    lines.append("")
    return lines


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def generate_testplan(
    item,
    opts,
    rtl_module: Module,
    explanation: ExplanationDoc,
    config_hash_value: str,
) -> str:
    """Render the markdown test-plan document for ``item``/``opts`` (pure).

    ``rtl_module`` must be the *stamped* IR module the RTL/TB were rendered
    from (same requirement as ``generate_tb``) so displayed signal names match
    the actually generated TB exactly. Deterministic: identical inputs yield
    byte-identical text.
    """
    spec: TbSpec = item.tb_spec(opts)
    names = _name_map(rtl_module, opts)

    def styled(canonical: str) -> str:
        return names.get(canonical, canonical)

    lines: list[str] = [
        f"# {item.name} — Test Plan",
        "",
        explanation.purpose,
        "",
        f"_Generated by SemiCraft {VERSION} — config hash `{config_hash_value}`. "
        f"Derived from `{rtl_module.name}`'s `ExplanationDoc`, `port_groups()`, "
        "and `tb_spec()`; the Test Plan table mirrors exactly what "
        f"`{rtl_module.name}_tb.sv` drives and checks._"
        if spec.clock is not None
        else f"_Generated by SemiCraft {VERSION} — config hash `{config_hash_value}`. "
        f"Derived from `{rtl_module.name}`'s `ExplanationDoc`, `port_groups()`, "
        "and `tb_spec()`. No testbench is generated for this configuration "
        "(`TbSpec.clock` is `None`)._",
        "",
    ]
    lines.extend(_features_section(explanation))
    lines.extend(_test_plan_section(spec, styled))
    lines.extend(_coverage_section(item, opts, spec, rtl_module, styled))
    lines.extend(_assertions_section(spec))
    lines.extend(_limitations_section(explanation, spec))
    return "\n".join(lines)
