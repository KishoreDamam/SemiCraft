"""Register-map metadata for IP blocks (Phase-4 P4-01).

The software-visible face of an IP: a list of byte-offset :class:`Register`
entries, each a list of bit-range :class:`RegisterField` entries. Pure
metadata — this module generates no RTL. P4-02 builds the AXI4-Lite register
block *from* this model; P4-01 ships the model, its validation rules, and the
derived quantities that generator will consume (:attr:`RegisterField.mask`,
:meth:`Register.reset_value`, :meth:`RegisterMap.span_bytes`).

One register is one bus word
----------------------------

A register has no width of its own: it is exactly ``data_width`` bits, the
map's bus data width. That is what a memory-mapped register *is*, and giving
registers an independent width would create a second source of truth that
address arithmetic would then have to reconcile. Fields need not tile the
whole word — any bit no field covers is **reserved and reads as zero**.

What a *write* to a reserved bit does is deliberately not specified here: it
is the generator's policy, not the layout's. ``regblock.py``, for instance,
rejects such a write with ``SLVERR`` rather than ignoring it.

Frozen means frozen
-------------------

Sequence fields are ``tuple``, not ``list``, so ``frozen=True`` is a real
promise rather than a claim a caller can walk around by appending to
``reg.fields``. Constructing from lists still works — pydantic coerces — so
this costs authors nothing. It matches the IR's own convention
(``ir/nodes.py`` stores every sequence as a tuple for the same reason).

Validation is strict on purpose
-------------------------------

Every rule below raises at model-construction time rather than producing a
subtly wrong decoder later:

R1. Register names are ``UPPER_SNAKE_CASE``, field names ``lower_snake_case``
    (matching IR_SPEC's parameter/signal conventions — register names become
    address localparams, field names become bit-slice names).
R2. Field names are unique within a register; register names are unique
    within a map.
R3. Fields are listed in ascending ``lsb`` order and may not overlap.
R4. A field's ``reset`` value must fit in its ``width``.
R5. ``data_width`` is one of 8/16/32/64; every field must fit inside it.
R6. Register offsets are byte offsets, listed in strictly ascending order,
    aligned to ``data_width // 8``, and the whole word must fit inside the
    ``2**addr_width``-byte address space.

R3 and R6 both demand *ascending* order rather than sorting silently: a map
whose entries are out of order is far more likely to be a copy-paste slip
than a deliberate choice, and sorting it away would hide that. It also makes
the generated documentation order a property of the source, not of the
renderer.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["Access", "RegisterField", "Register", "RegisterMap"]

#: Software access type of a field.
#:
#: - ``"rw"``  — read/write; software reads back what it wrote.
#: - ``"ro"``  — read-only; driven by hardware, writes are ignored.
#: - ``"wo"``  — write-only; reads return zero (command/trigger bits).
#: - ``"w1c"`` — write-1-to-clear; hardware sets the bit, software clears it
#:   by writing 1. Writing 0 leaves it alone.
Access = Literal["rw", "ro", "wo", "w1c"]

#: Bus data widths a register map may declare. Restricted to whole-byte powers
#: of two so that ``data_width // 8`` is always the natural address stride.
_DATA_WIDTHS = (8, 16, 32, 64)

_UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_LOWER_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


class RegisterField(BaseModel):
    """One contiguous bit range within a register (rules R1, R3, R4).

    ``lsb`` is the least-significant bit position within the register word and
    ``width`` the number of bits, so the field occupies ``[msb:lsb]`` with
    ``msb == lsb + width - 1``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(description="lower_snake_case field name, unique within the register.")
    lsb: int = Field(ge=0, description="Least-significant bit position within the word.")
    width: int = Field(default=1, ge=1, description="Field width in bits.")
    access: Access = Field(default="rw", description="Software access type.")
    reset: int = Field(default=0, ge=0, description="Reset value, must fit in `width`.")
    description: str = Field(default="", description="One-line description of the field.")

    @property
    def msb(self) -> int:
        """Most-significant bit position of the field within the word."""
        return self.lsb + self.width - 1

    @property
    def mask(self) -> int:
        """The field's bit mask, positioned at ``lsb`` within the word."""
        return ((1 << self.width) - 1) << self.lsb

    @property
    def bit_range(self) -> str:
        """Documentation spelling of the range: ``[3:1]``, or ``[0]`` if 1 bit."""
        return f"[{self.lsb}]" if self.width == 1 else f"[{self.msb}:{self.lsb}]"

    @model_validator(mode="after")
    def _check(self) -> RegisterField:
        if not _LOWER_SNAKE.match(self.name):
            raise ValueError(
                f"field name {self.name!r} must be lower_snake_case (rule R1)"
            )
        if self.reset >> self.width:
            raise ValueError(
                f"field {self.name!r}: reset value {self.reset} does not fit in "
                f"{self.width} bit(s) (rule R4)"
            )
        return self


class Register(BaseModel):
    """One addressable bus word at byte offset ``offset`` (rules R1, R2, R3).

    Bits not covered by any field are reserved and read as zero; what a write
    to them does is the generator's policy (see the module docstring). Field-vs-
    ``data_width`` checks live on :class:`RegisterMap`, which is where the word
    width is known.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(description="UPPER_SNAKE_CASE register name, unique within the map.")
    offset: int = Field(ge=0, description="Byte offset from the IP's base address.")
    fields: tuple[RegisterField, ...] = Field(
        default=(),
        description="Fields in ascending `lsb` order; gaps are reserved-read-zero.",
    )
    description: str = Field(default="", description="One-line description of the register.")

    @model_validator(mode="after")
    def _check(self) -> Register:
        if not _UPPER_SNAKE.match(self.name):
            raise ValueError(
                f"register name {self.name!r} must be UPPER_SNAKE_CASE (rule R1)"
            )
        seen: set[str] = set()
        prev_msb = -1
        for f in self.fields:
            if f.name in seen:
                raise ValueError(
                    f"register {self.name!r}: duplicate field name {f.name!r} (rule R2)"
                )
            seen.add(f.name)
            if f.lsb <= prev_msb:
                raise ValueError(
                    f"register {self.name!r}: field {f.name!r} at lsb {f.lsb} overlaps or "
                    f"precedes the previous field ending at bit {prev_msb} — fields must be "
                    f"listed in ascending, non-overlapping bit order (rule R3)"
                )
            prev_msb = f.msb
        return self

    def field(self, name: str) -> RegisterField:
        """The field called ``name``; raises :class:`KeyError` if absent."""
        for f in self.fields:
            if f.name == name:
                return f
        raise KeyError(f"register {self.name!r} has no field {name!r}")

    def reset_value(self) -> int:
        """The word's value out of reset: every field's ``reset`` in place.

        Reserved bits contribute zero, so this is the exact value a read of the
        register returns before software or hardware has changed anything —
        except for ``wo`` fields, which read as zero regardless (see
        :meth:`read_reset_value`).
        """
        value = 0
        for f in self.fields:
            value |= (f.reset << f.lsb) & f.mask
        return value

    def read_reset_value(self) -> int:
        """:meth:`reset_value` as *software* observes it: ``wo`` fields read 0."""
        value = 0
        for f in self.fields:
            if f.access == "wo":
                continue
            value |= (f.reset << f.lsb) & f.mask
        return value

    def reserved_mask(self, data_width: int) -> int:
        """Mask of the bits in a ``data_width``-bit word that no field covers."""
        covered = 0
        for f in self.fields:
            covered |= f.mask
        return ((1 << data_width) - 1) & ~covered


class RegisterMap(BaseModel):
    """An IP's complete software-visible register layout (rules R5, R6)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(description="Map name, used as the documentation heading.")
    data_width: int = Field(
        default=32, description="Bus data width in bits; one of 8, 16, 32, 64."
    )
    addr_width: int = Field(
        default=8,
        ge=1,
        description="Byte-address width; the map spans 2**addr_width bytes.",
    )
    registers: tuple[Register, ...] = Field(
        default=(), description="Registers in ascending `offset` order."
    )

    @model_validator(mode="after")
    def _check(self) -> RegisterMap:
        if self.data_width not in _DATA_WIDTHS:
            raise ValueError(
                f"data_width {self.data_width} must be one of {list(_DATA_WIDTHS)} (rule R5)"
            )
        stride = self.stride_bytes
        limit = 1 << self.addr_width
        seen: set[str] = set()
        prev_offset = -1
        for reg in self.registers:
            if reg.name in seen:
                raise ValueError(f"duplicate register name {reg.name!r} (rule R2)")
            seen.add(reg.name)
            if reg.offset <= prev_offset:
                raise ValueError(
                    f"register {reg.name!r} at offset {reg.offset:#x} does not follow the "
                    f"previous offset {prev_offset:#x} — registers must be listed in "
                    f"strictly ascending offset order (rule R6)"
                )
            prev_offset = reg.offset
            if reg.offset % stride:
                raise ValueError(
                    f"register {reg.name!r} offset {reg.offset:#x} is not aligned to the "
                    f"{stride}-byte stride implied by data_width={self.data_width} (rule R6)"
                )
            if reg.offset + stride > limit:
                raise ValueError(
                    f"register {reg.name!r} at offset {reg.offset:#x} does not fit inside "
                    f"the {limit}-byte space of addr_width={self.addr_width} (rule R6)"
                )
            for f in reg.fields:
                if f.msb >= self.data_width:
                    raise ValueError(
                        f"register {reg.name!r}: field {f.name!r} occupies {f.bit_range}, "
                        f"which does not fit in a {self.data_width}-bit word (rule R5)"
                    )
        return self

    @property
    def stride_bytes(self) -> int:
        """Byte distance between consecutive word addresses (``data_width // 8``)."""
        return self.data_width // 8

    def span_bytes(self) -> int:
        """Bytes from the base address through the end of the highest register.

        Zero for an empty map. This is the *used* span, not the decoded space:
        the decoded space is always ``2**addr_width`` bytes.
        """
        if not self.registers:
            return 0
        return self.registers[-1].offset + self.stride_bytes

    def register(self, name: str) -> Register:
        """The register called ``name``; raises :class:`KeyError` if absent."""
        for reg in self.registers:
            if reg.name == name:
                return reg
        raise KeyError(f"register map {self.name!r} has no register {name!r}")

    def at_offset(self, offset: int) -> Register:
        """The register at byte ``offset``; raises :class:`KeyError` if none."""
        for reg in self.registers:
            if reg.offset == offset:
                return reg
        raise KeyError(f"register map {self.name!r} has no register at offset {offset:#x}")
