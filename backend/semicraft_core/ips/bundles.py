"""Bus-side port bundles: interface metadata over flat ports (Phase-4 P4-01).

A :class:`PortBundle` says "these flat ports, together, are one AXI4-Lite
target port called ``s_axil``, and this one is its ``awvalid``". It changes
nothing about the generated RTL — see the package docstring for why that is a
deliberate decision rather than a stepping stone to SystemVerilog
``interface`` constructs.

Why not just reuse ``PortGroup``?
---------------------------------

:class:`~..modules.contract.PortGroup` already groups ports, but it groups
them *for the reader*: a name, a prose description, and a list of ports, with
no promise that the grouping means anything to a tool. A bundle is the
opposite: it is a machine-consumable claim with a protocol name and a
per-port role, and it is cross-checked against the generated module's actual
ports (:func:`..contract.check_bundles_against_module`). Phase 5's subsystem
composer will connect two IPs by matching ``role_name`` within a shared
``protocol``, which is only sound because the roles are declared rather than
guessed from signal spelling.

Clocks and resets are referenced, not owned
-------------------------------------------

``clock``/``reset`` name the clock domain a bundle lives in but are *not*
members of ``ports``. Two bundles on the same IP routinely share one clock,
and a port may belong to at most one bundle
(:func:`..contract.check_bundles_against_module` enforces that) — so treating
the clock as a member would make the common case illegal. Phase 5's
clock/reset domain declaration reads these fields.

Directions are deliberately absent
----------------------------------

A bundle port carries no direction. The generated IR module already declares
one, and duplicating it here would create two sources of truth that could
disagree — the exact defect class this project keeps finding. Consumers
resolve direction from the module; :func:`..contract.check_bundles_against_module`
is what guarantees the port is really there to resolve.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["BundleRole", "BundlePort", "PortBundle", "restyle_bundles"]

#: Which side of the protocol this IP implements.
#:
#: - ``"target"``    — the IP is accessed (an AXI4-Lite slave, an SPI device).
#: - ``"initiator"`` — the IP drives transactions (an AXI4-Lite master).
#:
#: Only these two: every protocol SemiCraft will generate in Phase 4 has
#: exactly two sides, and inventing speculative roles ("monitor", "passthrough")
#: before something consumes them is how dormant metadata accumulates.
BundleRole = Literal["target", "initiator"]

_BUNDLE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_PROTOCOL = re.compile(r"^[a-z][a-z0-9]*(?:[-.][a-z0-9]+)*$")
_ROLE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class BundlePort(BaseModel):
    """One flat port's membership in a bundle.

    - ``signal`` — the *canonical* port name on this IP, exactly as the IR
      ``Module`` declares it (before naming-style transforms). Style transforms
      are applied downstream by the render name map, the same way
      ``PortGroup.ports`` and ``TbSpec`` signal names are handled.
    - ``role_name`` — the protocol's own name for this signal (``"awvalid"``,
      ``"rdata"``, ``"sclk"``). This is what a composer matches on.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    signal: str = Field(description="Canonical IR port name on this IP.")
    role_name: str = Field(description="The protocol's name for this signal.")

    @model_validator(mode="after")
    def _check(self) -> BundlePort:
        if not _ROLE_NAME.match(self.role_name):
            raise ValueError(
                f"role_name {self.role_name!r} must be lower_snake_case"
            )
        return self


class PortBundle(BaseModel):
    """A named group of flat ports implementing one side of one protocol."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(
        description="lower_snake_case bundle name, unique within the IP (e.g. 's_axil')."
    )
    protocol: str = Field(
        description="Protocol identifier, e.g. 'axi4-lite', 'uart', 'spi'."
    )
    role: BundleRole = Field(description="Which side of the protocol this IP implements.")
    ports: tuple[BundlePort, ...] = Field(description="Member ports; at least one.")
    clock: str | None = Field(
        default=None,
        description=(
            "Canonical name of the clock this bundle is timed by, or null for an "
            "asynchronous/combinational interface. Not a member of `ports`."
        ),
    )
    reset: str | None = Field(
        default=None,
        description=(
            "Canonical name of the reset that applies to this bundle, or null. "
            "Not a member of `ports`."
        ),
    )
    description: str = Field(default="", description="One-line description of the bundle.")

    @model_validator(mode="after")
    def _check(self) -> PortBundle:
        if not _BUNDLE_NAME.match(self.name):
            raise ValueError(f"bundle name {self.name!r} must be lower_snake_case")
        if not _PROTOCOL.match(self.protocol):
            raise ValueError(
                f"protocol {self.protocol!r} must be lowercase alphanumeric with "
                f"'-' or '.' separators, e.g. 'axi4-lite'"
            )
        if not self.ports:
            raise ValueError(f"bundle {self.name!r} declares no ports")
        for attr in ("signal", "role_name"):
            seen: set[str] = set()
            for p in self.ports:
                value = getattr(p, attr)
                if value in seen:
                    raise ValueError(
                        f"bundle {self.name!r}: duplicate {attr} {value!r}"
                    )
                seen.add(value)
        member_signals = {p.signal for p in self.ports}
        for role, name in (("clock", self.clock), ("reset", self.reset)):
            if name is not None and name in member_signals:
                raise ValueError(
                    f"bundle {self.name!r}: {role} {name!r} is also listed as a member "
                    f"port — a bundle's clock/reset are referenced, not owned, so that "
                    f"several bundles can share one clock domain"
                )
        return self

    @property
    def signals(self) -> list[str]:
        """Canonical port names in this bundle, in declaration order."""
        return [p.signal for p in self.ports]

    def by_role(self, role_name: str) -> BundlePort:
        """The member port whose protocol role is ``role_name``.

        Raises :class:`KeyError` if the bundle has no such role — which is how
        a composer discovers that an optional protocol signal is absent.
        """
        for p in self.ports:
            if p.role_name == role_name:
                return p
        raise KeyError(f"bundle {self.name!r} has no port with role {role_name!r}")


def restyle_bundles(
    bundles: list[PortBundle], rename: dict[str, str]
) -> list[PortBundle]:
    """Rewrite every canonical signal name in ``bundles`` through ``rename``.

    A module writes its metadata in *canonical* names — ``bundles(opts)`` never
    sees the render style — while the emitted RTL names ports through
    :func:`~..render.style.build_name_map`. Anything that shows those names to a
    user (or to another tool) must therefore go through the same map, or an
    active-low reset declared ``rst`` would be documented as ``rst`` against a
    port actually rendered ``rst_n``. This is the same correction
    ``assertions/restyle.py`` makes for SVA specs, and for the same reason.

    Only the structured name fields — ``BundlePort.signal``, ``clock`` and
    ``reset`` — are rewritten. ``role_name`` is *protocol* vocabulary, not an
    identifier in the generated RTL, so it is deliberately untouched: renaming
    ``awvalid`` because a user chose a port prefix would break exactly the
    matching that bundles exist to enable. Bundle names and descriptions are
    likewise left alone.

    Names absent from ``rename`` pass through unchanged.
    """

    def styled(name: str | None) -> str | None:
        return None if name is None else rename.get(name, name)

    return [
        b.model_copy(
            update={
                # ``model_copy`` does not re-validate, so the tuple has to be
                # built here rather than relying on pydantic to coerce a list.
                "ports": tuple(
                    p.model_copy(update={"signal": rename.get(p.signal, p.signal)})
                    for p in b.ports
                ),
                "clock": styled(b.clock),
                "reset": styled(b.reset),
            }
        )
        for b in bundles
    ]
