"""Checker/monitor/scoreboard scaffold generator (P3-06).

A standalone package that turns declarative specs
(:mod:`semicraft_core.checkers.spec`) into deterministic SystemVerilog
**scaffold text** for three directed (not UVM, per PRD non-goal)
verification components:

- a passive bundle **monitor** module (:func:`generate_monitor`),
- a **checker** module of procedural protocol checks
  (:func:`generate_checker`) — distinct from the P3-05 concurrent-SVA
  (``assert property``) generator, see ``docs/CHECKERS.md``,
- an expected-value **scoreboard** class with an optional wrapper module
  (:func:`generate_scoreboard`).

Not yet wired into ``generate_files`` — integration is a later WP. See
``docs/CHECKERS.md``.
"""

from .generate import generate_checker, generate_monitor, generate_scoreboard
from .spec import (
    CheckerItem,
    CheckerSpec,
    LatencyCheck,
    MonitorSpec,
    ResetPolarity,
    ResetValueCheck,
    ScoreboardSpec,
    ScoreboardWrapper,
    Signal,
    StabilityCheck,
)

__all__ = [
    "generate_monitor",
    "generate_checker",
    "generate_scoreboard",
    "Signal",
    "ResetPolarity",
    "MonitorSpec",
    "ResetValueCheck",
    "StabilityCheck",
    "LatencyCheck",
    "CheckerItem",
    "CheckerSpec",
    "ScoreboardWrapper",
    "ScoreboardSpec",
]
