"""Style engine: naming transforms and render-time style options (WP-02).

Implements IR_SPEC §2 design rule 5: IR names are canonical
(``lower_snake_case``; ``UPPER_SNAKE_CASE`` params); user naming options
(convention, prefix, suffix) and the ``_n`` active-low suffix are applied
here, at render time, via a canonical->rendered name map built *before*
emission. After transformation every rendered name is checked against BOTH
the SystemVerilog and Verilog reserved-word sets (IR_SPEC §6 rule 7 — either
target may be rendered from the same IR); collisions raise :class:`StyleError`.

Transform scope: ports, internal signals, enum declaration names, enum
members, and instance names. ``Param`` names (``UPPER_SNAKE_CASE`` by RTL
convention) and the module name are rendered verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..ir.nodes import AlwaysFF, EnumDecl, Instance, Module, Signal
from ..ir.validate import SV_KEYWORDS, VERILOG_KEYWORDS

NamingConvention = Literal["snake", "camel"]
CommentVerbosity = Literal["none", "normal", "verbose"]


class StyleError(Exception):
    """Raised when style transformation produces colliding or reserved names."""


@dataclass(frozen=True, slots=True)
class StyleOptions:
    """User-facing rendering style options (IMPLEMENTATION_PLAN §5 WP-02 task 3).

    - ``naming``: identifier convention applied to signals/ports/enums/instances.
      ``snake`` (default) keeps canonical names; ``camel`` converts to lowerCamelCase.
    - ``prefix`` / ``suffix``: literal strings attached around the converted name.
    - ``indent``: spaces per nesting level (default 4, STYLE_GUIDE §6).
    - ``comment_verbosity``: ``none`` | ``normal`` | ``verbose`` comment filter
      (design rule 7). ``none`` also suppresses port ``doc`` inline comments.
    """

    naming: NamingConvention = "snake"
    prefix: str = ""
    suffix: str = ""
    indent: int = 4
    comment_verbosity: CommentVerbosity = "normal"


def _to_camel(name: str) -> str:
    """Convert canonical ``lower_snake_case`` to ``lowerCamelCase``."""
    parts = [p for p in name.split("_") if p]
    if not parts:
        return name
    return parts[0] + "".join(p[0].upper() + p[1:] for p in parts[1:])


def build_name_map(module: Module, style: StyleOptions) -> dict[str, str]:
    """Build the canonical->rendered name map for ``module`` under ``style``.

    The map covers every name the renderer may emit; renderers must resolve
    all identifier references through it. Active-low resets (``ResetSpec.
    active_low=True``) get a terminal ``_n`` suffix so the rendered reset name
    and every reference to it agree (design rule 5).
    """
    active_low_resets = {
        item.reset.name
        for item in module.items
        if isinstance(item, AlwaysFF) and item.reset is not None and item.reset.active_low
    }

    def transform(name: str) -> str:
        base = _to_camel(name) if style.naming == "camel" else name
        rendered = f"{style.prefix}{base}{style.suffix}"
        if name in active_low_resets:
            rendered += "_n"
        return rendered

    mapping: dict[str, str] = {}
    for port in module.ports:
        mapping[port.name] = transform(port.name)
    for item in module.items:
        if isinstance(item, Signal):
            mapping[item.name] = transform(item.name)
        elif isinstance(item, EnumDecl):
            mapping[item.name] = transform(item.name)
            for member in item.members:
                mapping[member] = transform(member)
        elif isinstance(item, Instance):
            mapping[item.name] = transform(item.name)
        elif isinstance(item, AlwaysFF):
            # Clock/reset names normally alias ports (already mapped); the
            # setdefault covers specs whose names are not declared ports so the
            # composed sensitivity list still gets styled names (and ``_n``).
            mapping.setdefault(item.clock.name, transform(item.clock.name))
            if item.reset is not None:
                mapping.setdefault(item.reset.name, transform(item.reset.name))
    # Params and the module name render verbatim; include them so collision
    # checks see the full rendered namespace.
    for param in module.params:
        mapping.setdefault(param.name, param.name)
    mapping.setdefault(module.name, module.name)

    check_rendered_names(mapping)
    return mapping


def check_rendered_names(mapping: dict[str, str]) -> None:
    """Reserved-word and collision validation of post-transform names.

    Checks against BOTH ``SV_KEYWORDS`` and ``VERILOG_KEYWORDS`` (IR_SPEC §6
    rule 7: either target language may be rendered from the same IR).
    """
    reserved = SV_KEYWORDS | VERILOG_KEYWORDS
    problems: list[str] = []
    rendered_owner: dict[str, str] = {}
    for canonical in sorted(mapping):
        rendered = mapping[canonical]
        if rendered in reserved:
            problems.append(
                f"rendered name {rendered!r} (from canonical {canonical!r}) collides "
                f"with a SystemVerilog/Verilog reserved word; change the naming "
                f"prefix/suffix/convention"
            )
        owner = rendered_owner.get(rendered)
        if owner is not None and owner != canonical:
            problems.append(
                f"rendered name {rendered!r} is produced by both {owner!r} and "
                f"{canonical!r}; change the naming prefix/suffix/convention"
            )
        rendered_owner.setdefault(rendered, canonical)
    if problems:
        raise StyleError(
            "style naming transform produced invalid rendered names:\n"
            + "\n".join(f"  - {p}" for p in problems)
        )
