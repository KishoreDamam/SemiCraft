"""AXI4-Lite register block generator (Phase-4 P4-02).

The keystone of the IP library: turns any :class:`~.regmap.RegisterMap` into a
complete AXI4-Lite **target** (slave) in IR. P4-05..P4-08 reuse it as their
register frontend, so this module is deliberately a plain function over a
register map rather than something welded to one catalog item:

    build_axil_regblock(name, regmap, sync_reset=..., description=...) -> Module

``semicraft_core/ips/axil_regblock.py`` is the catalog IP that wraps it; a
UART or SPI IP will call the same function with its own map and splice the
result's ports into its own module.

Protocol implementation
-----------------------

A single-outstanding target. Write and read channels are independent:

*Writes.* AW and W are captured independently (AXI permits either first), each
into a one-deep holding register with its own ``_hs`` flag. When both are held
and no response is pending, the write executes and ``bvalid`` rises.
``awready``/``wready`` are ``!captured && !bvalid`` — functions of *registers
only*, never of ``awvalid``/``wvalid``, so there is no combinational
valid→ready path (an AXI protocol violation and a classic deadlock source).

*Reads.* ``arready = !rvalid``. On an AR handshake the addressed word is
captured into ``rdata`` and ``rvalid`` rises; it clears on the R handshake.

*Errors.* An address matching no register returns ``SLVERR`` (``2'b10``) with
zero data. ``DECERR`` is deliberately not used: that code means "no slave at
this address", which is the interconnect's answer to give, not ours.

Two deliberate departures from a textbook AXI4-Lite target
----------------------------------------------------------

Both exist because this project lints every generated file with
``verilator --lint-only -Wall`` and treats *any* warning as a failure — a
module that declares inputs it never reads does not pass, and suppressing that
with a lint pragma would blind the gate to real unused-signal bugs. Rather
than weaken the gate, the design uses every bit it declares:

1. **No ``awprot``/``arprot``.** A register block enforces no protection
   policy, so those inputs would be dead. An interconnect that drives them
   simply leaves them unconnected here. Called out in the IP's limitations.
2. **The full byte address is decoded**, not just the word-index bits. An
   access whose low byte-offset bits are non-zero therefore matches nothing
   and returns ``SLVERR``, instead of silently aliasing onto the containing
   word. AXI4-Lite requires word-aligned addresses anyway; an explicit error
   beats a silent alias.

Reserved bits must be written as zero
-------------------------------------

A write that tries to set a bit the addressed register does not implement
(a gap, or a read-only field's bits) is rejected with ``SLVERR`` and performs
no update at all. This is the standard "SBZ — should be zero" register
doctrine made enforceable, it turns a class of silent software bug into a bus
error, and it is what lets every ``wdata``/``wstrb`` bit be genuinely used no
matter how sparse the map is.

The check is layered to avoid a combinational loop: ``wr_addr_<reg>`` decodes
the address only, that selects the reserved mask, and ``wr_sel_<reg>`` — the
actual field write-enable — is ``wr_addr_<reg> && !wr_reserved``.

Byte strobes are exact
----------------------

``wstrb`` is expanded to a bit mask (``wmask``) and every writable field
updates as ``(wdata & mask) | (field & ~mask)`` over its own bit range. A
partial-byte write therefore leaves the untouched bytes of a field alone,
which is what the AXI spec requires and what a "write the whole register"
shortcut gets wrong for multi-byte fields.

Access types
------------

- ``rw``  — storage; drives an output; software reads it back.
- ``ro``  — no storage; an *input* port is muxed into the read data.
- ``wo``  — storage; drives an output; **reads as zero**.
- ``w1c`` — storage; a ``<field>_set`` input sets bits, software clears them
  by writing 1. On a simultaneous set and clear the **set wins**, so a
  hardware event is never silently lost. Documented, and pinned by a test.

No parameters
-------------

The emitted module uses literal widths rather than parameters. SemiCraft
generates one module per configuration, so a parameter would add nothing —
and sized constants derived from a parameter (``ADDR_WIDTH'h4``) are not
Verilog-2001, which would cost the dual-language guarantee.

Reset
-----

AXI4-Lite mandates an active-low reset. The reset is therefore always
active-low here; the polarity is not configurable, and ``build_axil_regblock``
raises if asked otherwise. It is *named* ``areset`` and renders ``areset_n``,
because the naming engine owns the ``_n`` suffix (IR_SPEC design rule 5) —
the spec spells it ``ARESETn``. Integration matches on the bundle's declared
roles, not on spelling, so the difference stays contained; it is called out in
the IP's limitations.
"""

from __future__ import annotations

from ..ir.build import IN, OUT, bit, vec
from ..ir.nodes import (
    AlwaysFF,
    Assign,
    BinOp,
    BinOpKind,
    Bit,
    Case,
    CaseItem,
    ClockSpec,
    Comment,
    CommentLevel,
    Concat,
    Const,
    ConstBase,
    ContAssign,
    Expr,
    Header,
    If,
    Module,
    ModuleItem,
    Port,
    Ref,
    Repl,
    ResetKind,
    ResetSpec,
    Signal,
    Slice,
    Stmt,
    Ternary,
    UnaryOp,
    UnaryOpKind,
)
from ..version import VERSION
from .contract import IpContractError
from .regmap import Register, RegisterField, RegisterMap

__all__ = [
    "build_axil_regblock",
    "axil_ports",
    "hw_port_name",
    "w1c_set_port_name",
    "hardware_ports",
    "AXI_RESP_OKAY",
    "AXI_RESP_SLVERR",
    "AXI_CLOCK",
    "AXI_RESET",
]

#: AXI response codes actually emitted. ``DECERR`` (2'b11) is the
#: interconnect's code for "no slave here" and is not a target's to send.
AXI_RESP_OKAY = 0b00
AXI_RESP_SLVERR = 0b10

#: Canonical clock/reset names for the AXI face.
AXI_CLOCK = "aclk"
AXI_RESET = "areset"

#: The AXI4-Lite signals, as ``(canonical_name, protocol_role)``. Canonical
#: names happen to equal their roles here; they are kept as distinct concepts
#: because a naming style renames the former and never the latter.
_AXI_SIGNALS = (
    "awaddr", "awvalid", "awready",
    "wdata", "wstrb", "wvalid", "wready",
    "bresp", "bvalid", "bready",
    "araddr", "arvalid", "arready",
    "rdata", "rresp", "rvalid", "rready",
)


# --------------------------------------------------------------------------- #
# Naming
# --------------------------------------------------------------------------- #


def hw_port_name(reg: Register, field: RegisterField) -> str:
    """Hardware-face port name for one field: ``ctrl_enable`` for CTRL.enable."""
    return f"{reg.name.lower()}_{field.name}"


def w1c_set_port_name(reg: Register, field: RegisterField) -> str:
    """Set-input name for a ``w1c`` field: ``irq_overflow_set``."""
    return f"{hw_port_name(reg, field)}_set"


def hardware_ports(regmap: RegisterMap) -> list[tuple[str, str, int]]:
    """Every hardware-face port as ``(name, direction, width)``, in map order.

    ``direction`` is ``"input"``/``"output"`` as seen from the register block.
    Used by the catalog IP for port groups and by the datasheet.
    """
    out: list[tuple[str, str, int]] = []
    for reg in regmap.registers:
        for f in reg.fields:
            name = hw_port_name(reg, f)
            if f.access == "ro":
                out.append((name, "input", f.width))
            else:
                out.append((name, "output", f.width))
                if f.access == "w1c":
                    out.append((w1c_set_port_name(reg, f), "input", f.width))
    return out


def axil_ports() -> tuple[str, ...]:
    """The AXI4-Lite signal names this generator emits, in declaration order."""
    return _AXI_SIGNALS


# --------------------------------------------------------------------------- #
# Small expression helpers
# --------------------------------------------------------------------------- #


def _zeros(width: int) -> Const:
    return Const(0, width=Const(width), base=ConstBase.BIN)


def _lnot(e: Expr) -> UnaryOp:
    return UnaryOp(UnaryOpKind.NOT_LOGICAL, e)


def _land(a: Expr, b: Expr) -> BinOp:
    return BinOp(BinOpKind.LAND, a, b)


def _range_of(signal: str, field: RegisterField) -> Expr:
    """``sig[lsb]`` for a 1-bit field, ``sig[msb:lsb]`` otherwise.

    A 1-bit part-select would also be legal, but ``sig[3]`` reads better than
    ``sig[3:3]`` and keeps the emitted width unambiguous.
    """
    if field.width == 1:
        return Bit(Ref(signal), Const(field.lsb))
    return Slice(Ref(signal), Const(field.msb), Const(field.lsb))


def _addr_const(offset: int, addr_width: int) -> Const:
    return Const(offset, width=Const(addr_width), base=ConstBase.HEX)


def _wr_addr_name(reg: Register) -> str:
    return f"wr_addr_{reg.name.lower()}"


def write_reserved_mask(reg: Register, data_width: int) -> int:
    """Bits of ``reg`` that a write may not set: everything not held by a
    writable (``rw``/``wo``/``w1c``) field.

    Read-only field bits count as write-reserved — an ``ro`` field has no
    storage for a write to land in.
    """
    writable = 0
    for f in reg.fields:
        if f.access != "ro":
            writable |= f.mask
    return ((1 << data_width) - 1) & ~writable


def _wr_sel_name(reg: Register) -> str:
    return f"wr_sel_{reg.name.lower()}"


# --------------------------------------------------------------------------- #
# Read data assembly
# --------------------------------------------------------------------------- #


def _read_word_expr(reg: Register, data_width: int) -> Expr:
    """The full ``data_width``-bit value a read of ``reg`` returns.

    Fields contribute their current value, except ``wo`` fields which read as
    zero; every bit no field covers is zero. Parts are assembled LSB-first and
    reversed, because a concatenation is written most-significant-first.
    """
    parts: list[Expr] = []
    pos = 0
    for f in reg.fields:
        if f.lsb > pos:
            parts.append(_zeros(f.lsb - pos))
        parts.append(
            _zeros(f.width) if f.access == "wo" else Ref(hw_port_name(reg, f))
        )
        pos = f.msb + 1
    if pos < data_width:
        parts.append(_zeros(data_width - pos))
    if not parts:
        return _zeros(data_width)
    if len(parts) == 1:
        return parts[0]
    return Concat(list(reversed(parts)))


# --------------------------------------------------------------------------- #
# Field write logic
# --------------------------------------------------------------------------- #


def _byte_merged(reg: Register, f: RegisterField) -> Expr:
    """``(wdata & mask) | (field & ~mask)`` over the field's bit range."""
    wd = _range_of("wdata_q", f)
    wm = _range_of("wmask", f)
    keep = BinOp(
        BinOpKind.AND,
        Ref(hw_port_name(reg, f)),
        UnaryOp(UnaryOpKind.NOT_BITWISE, wm),
    )
    return BinOp(BinOpKind.OR, BinOp(BinOpKind.AND, wd, wm), keep)


def _w1c_on_write(reg: Register, f: RegisterField) -> Expr:
    """``(field & ~(wdata & mask)) | set`` — software clear, hardware set wins."""
    clear = BinOp(BinOpKind.AND, _range_of("wdata_q", f), _range_of("wmask", f))
    held = BinOp(
        BinOpKind.AND,
        Ref(hw_port_name(reg, f)),
        UnaryOp(UnaryOpKind.NOT_BITWISE, clear),
    )
    return BinOp(BinOpKind.OR, held, Ref(w1c_set_port_name(reg, f)))


def _w1c_idle(reg: Register, f: RegisterField) -> Expr:
    """``field | set`` — no write this cycle, so only the hardware set applies."""
    return BinOp(
        BinOpKind.OR,
        Ref(hw_port_name(reg, f)),
        Ref(w1c_set_port_name(reg, f)),
    )


# --------------------------------------------------------------------------- #
# The generator
# --------------------------------------------------------------------------- #


def _check_port_names(regmap: RegisterMap) -> None:
    """Hardware-face port names must be unique.

    ``<reg>_<field>`` can collide even though register and field names are each
    unique within their scope — register ``A_B`` field ``c`` and register ``A``
    field ``b_c`` both produce ``a_b_c``. Rare, but it would emit a module with
    a duplicate port, so it is caught here rather than by the renderer.
    """
    seen: dict[str, str] = {}
    for name, _dir, _w in hardware_ports(regmap):
        if name in seen:
            raise IpContractError(
                f"register map {regmap.name!r}: hardware port name {name!r} is "
                f"produced twice (once already by {seen[name]!r}); rename a "
                f"register or field so <register>_<field> stays unique"
            )
        seen[name] = name
    # No AXI-name collision check: every hardware port name contains an
    # underscore (`<register>_<field>`) and no AXI4-Lite signal name does, so
    # such a check could never fire. An unreachable guard is worse than none —
    # it reads like protection that is not there.


def _axi_port_list(data_width: int, addr_width: int) -> list[Port]:
    strb_width = data_width // 8
    return [
        Port(AXI_CLOCK, IN, bit(), doc="AXI clock; everything is synchronous to it"),
        Port(AXI_RESET, IN, bit(), doc="AXI reset, active-low (spec: ARESETn)"),
        Port("awaddr", IN, vec(addr_width), doc="Write address (byte address)"),
        Port("awvalid", IN, bit(), doc="Write address valid"),
        Port("awready", OUT, bit(), doc="Write address ready"),
        Port("wdata", IN, vec(data_width), doc="Write data"),
        Port("wstrb", IN, vec(strb_width), doc="Write byte strobes, one bit per byte"),
        Port("wvalid", IN, bit(), doc="Write data valid"),
        Port("wready", OUT, bit(), doc="Write data ready"),
        Port("bresp", OUT, vec(2), doc="Write response: OKAY, or SLVERR if unmapped"),
        Port("bvalid", OUT, bit(), doc="Write response valid"),
        Port("bready", IN, bit(), doc="Write response ready"),
        Port("araddr", IN, vec(addr_width), doc="Read address (byte address)"),
        Port("arvalid", IN, bit(), doc="Read address valid"),
        Port("arready", OUT, bit(), doc="Read address ready"),
        Port("rdata", OUT, vec(data_width), doc="Read data"),
        Port("rresp", OUT, vec(2), doc="Read response: OKAY, or SLVERR if unmapped"),
        Port("rvalid", OUT, bit(), doc="Read data valid"),
        Port("rready", IN, bit(), doc="Read data ready"),
    ]


def _hw_port_list(regmap: RegisterMap) -> list[Port]:
    ports: list[Port] = []
    for reg in regmap.registers:
        for f in reg.fields:
            name = hw_port_name(reg, f)
            dtype = bit() if f.width == 1 else vec(f.width)
            label = f"{reg.name}.{f.name}"
            if f.access == "ro":
                ports.append(Port(name, IN, dtype, doc=f"{label} (RO) — sampled on read"))
            elif f.access == "wo":
                ports.append(Port(name, OUT, dtype, doc=f"{label} (WO) — reads back as 0"))
            elif f.access == "w1c":
                ports.append(Port(name, OUT, dtype, doc=f"{label} (W1C) — current value"))
                ports.append(
                    Port(
                        w1c_set_port_name(reg, f),
                        IN,
                        dtype,
                        doc=f"{label} (W1C) — set request; a set beats a same-cycle clear",
                    )
                )
            else:
                ports.append(Port(name, OUT, dtype, doc=f"{label} (RW)"))
    return ports


def _decode_signals(regmap: RegisterMap, addr_width: int) -> list[ModuleItem]:
    """Address decode, the reserved-bit write check, and the write selects.

    Three layers, in dependency order — the split matters, because folding the
    reserved check into ``wr_addr_*`` would make ``wr_reserved`` depend on a
    signal that depends on it:

    1. ``wr_addr_<reg>`` — address match only. Feeds ``wr_hit`` and the
       reserved-mask mux.
    2. ``wr_rsvd_mask`` / ``wr_reserved`` — the bits the addressed register
       does not implement, and whether the write is trying to set any of them.
    3. ``wr_sel_<reg>`` — the actual field write-enable: addressed *and* not a
       reserved-bit violation. Emitted only for registers that have something
       writable, so a read-only register never declares a select nobody reads.
    """
    data_width = regmap.data_width
    items: list[ModuleItem] = [
        Signal("wr_exec", bit(), doc="Both write channels captured and no response pending"),
        ContAssign(
            Ref("wr_exec"),
            _land(_land(Ref("aw_hs"), Ref("w_hs")), _lnot(Ref("bvalid"))),
        ),
    ]

    hit: Expr | None = None
    mask: Expr | None = None
    for reg in regmap.registers:
        addr_sel = _wr_addr_name(reg)
        items.append(Signal(addr_sel, bit(), doc=f"Write address selects {reg.name}"))
        items.append(
            ContAssign(
                Ref(addr_sel),
                _land(
                    Ref("wr_exec"),
                    BinOp(
                        BinOpKind.EQ,
                        Ref("awaddr_q"),
                        _addr_const(reg.offset, addr_width),
                    ),
                ),
            )
        )
        hit = Ref(addr_sel) if hit is None else BinOp(BinOpKind.LOR, hit, Ref(addr_sel))
        arm = Ternary(
            Ref(addr_sel),
            Const(
                write_reserved_mask(reg, data_width),
                width=Const(data_width),
                base=ConstBase.HEX,
            ),
            _zeros(data_width),
        )
        mask = arm if mask is None else BinOp(BinOpKind.OR, mask, arm)

    items.append(Signal("wr_hit", bit(), doc="The write address matched a register"))
    items.append(ContAssign(Ref("wr_hit"), hit if hit is not None else _zeros(1)))

    items.append(
        Signal(
            "wr_rsvd_mask",
            vec(data_width),
            doc="Bits the addressed register does not implement",
        )
    )
    items.append(
        ContAssign(Ref("wr_rsvd_mask"), mask if mask is not None else _zeros(data_width))
    )
    items.append(
        Signal("wr_reserved", bit(), doc="The write tries to set a reserved bit")
    )
    items.append(
        ContAssign(
            Ref("wr_reserved"),
            UnaryOp(
                UnaryOpKind.RED_OR,
                BinOp(
                    BinOpKind.AND,
                    BinOp(BinOpKind.AND, Ref("wdata_q"), Ref("wmask")),
                    Ref("wr_rsvd_mask"),
                ),
            ),
        )
    )

    for reg in regmap.registers:
        if all(f.access == "ro" for f in reg.fields):
            continue
        sel = _wr_sel_name(reg)
        items.append(Signal(sel, bit(), doc=f"Write updates {reg.name}"))
        items.append(
            ContAssign(
                Ref(sel), _land(Ref(_wr_addr_name(reg)), _lnot(Ref("wr_reserved")))
            )
        )
    return items


def _reset_body(regmap: RegisterMap, data_width: int) -> list[Stmt]:
    body: list[Stmt] = [
        Assign(Ref("aw_hs"), _zeros(1)),
        Assign(Ref("w_hs"), _zeros(1)),
        Assign(Ref("bvalid"), _zeros(1)),
        Assign(Ref("bresp"), Const(AXI_RESP_OKAY, width=Const(2), base=ConstBase.BIN)),
        Assign(Ref("rvalid"), _zeros(1)),
        Assign(Ref("rresp"), Const(AXI_RESP_OKAY, width=Const(2), base=ConstBase.BIN)),
        Assign(Ref("rdata"), _zeros(data_width)),
    ]
    for reg in regmap.registers:
        for f in reg.fields:
            if f.access == "ro":
                continue
            body.append(
                Assign(
                    Ref(hw_port_name(reg, f)),
                    Const(f.reset, width=Const(f.width)),
                )
            )
    return body


def _write_body(regmap: RegisterMap) -> list[Stmt]:
    """Per-register field updates, one ``if (wr_sel_X) ... else ...`` each.

    The ``else`` branch exists only for registers holding ``w1c`` fields: those
    must keep accepting hardware sets on cycles when software is not writing
    them, whereas an ``rw``/``wo`` field simply holds.
    """
    stmts: list[Stmt] = []
    for reg in regmap.registers:
        writable = [f for f in reg.fields if f.access != "ro"]
        if not writable:
            continue
        then: list[Stmt] = []
        otherwise: list[Stmt] = []
        for f in writable:
            target = Ref(hw_port_name(reg, f))
            if f.access == "w1c":
                then.append(Assign(target, _w1c_on_write(reg, f)))
                otherwise.append(Assign(target, _w1c_idle(reg, f)))
            else:
                then.append(Assign(target, _byte_merged(reg, f)))
        stmts.append(
            If(Ref(_wr_sel_name(reg)), then=then, else_=otherwise or None)
        )
    return stmts


def _read_body(regmap: RegisterMap, data_width: int, addr_width: int) -> Stmt:
    okay = Const(AXI_RESP_OKAY, width=Const(2), base=ConstBase.BIN)
    slverr = Const(AXI_RESP_SLVERR, width=Const(2), base=ConstBase.BIN)
    items = [
        CaseItem(
            [_addr_const(reg.offset, addr_width)],
            [
                Assign(Ref("rdata"), _read_word_expr(reg, data_width)),
                Assign(Ref("rresp"), okay),
            ],
        )
        for reg in regmap.registers
    ]
    default = [
        Assign(Ref("rdata"), _zeros(data_width)),
        Assign(Ref("rresp"), slverr),
    ]
    inner: Stmt
    if items:
        inner = Case(Ref("araddr"), items=items, default=default)
    else:
        # A map with no registers decodes nothing; every read is an error.
        inner = default[0]
    body: list[Stmt] = [Assign(Ref("rvalid"), Const(1, width=Const(1), base=ConstBase.BIN))]
    if items:
        body.append(inner)
    else:
        body.extend(default)
    return If(_land(Ref("arvalid"), Ref("arready")), then=body)


def build_axil_regblock(
    name: str,
    regmap: RegisterMap,
    *,
    sync_reset: bool = True,
    description: str = "",
) -> Module:
    """Build the IR for an AXI4-Lite register block serving ``regmap``.

    ``name`` is the module name; ``sync_reset`` selects a synchronous or
    asynchronous active-low reset (the polarity is fixed by the protocol).
    Pure: the same arguments always produce identical IR.

    Raises :class:`~.contract.IpContractError` if the map cannot be served —
    an address space too small to hold a word index, or hardware-face port
    names that collide with each other or with an AXI signal.
    """
    data_width = regmap.data_width
    addr_width = regmap.addr_width
    if not regmap.registers:
        raise IpContractError(
            f"register map {regmap.name!r} declares no registers; an AXI4-Lite "
            f"register block with nothing to decode would answer SLVERR to every "
            f"access and leave its address inputs unread"
        )
    _check_port_names(regmap)

    strb_width = data_width // 8
    ports = _axi_port_list(data_width, addr_width) + _hw_port_list(regmap)

    signals: list[ModuleItem] = [
        Signal("aw_hs", bit(), doc="Write address captured, awaiting the data beat"),
        Signal("w_hs", bit(), doc="Write data captured, awaiting the address beat"),
        Signal("awaddr_q", vec(addr_width), doc="Captured write address"),
        Signal("wdata_q", vec(data_width), doc="Captured write data"),
        Signal("wstrb_q", vec(strb_width), doc="Captured write byte strobes"),
        Signal("wmask", vec(data_width), doc="Captured strobes expanded to a bit mask"),
    ]

    # awready/wready depend on registers only — never on awvalid/wvalid. A
    # combinational valid->ready path is an AXI violation and deadlocks against
    # a master that waits for ready before asserting valid.
    handshake = [
        ContAssign(Ref("awready"), _land(_lnot(Ref("aw_hs")), _lnot(Ref("bvalid")))),
        ContAssign(Ref("wready"), _land(_lnot(Ref("w_hs")), _lnot(Ref("bvalid")))),
        ContAssign(Ref("arready"), _lnot(Ref("rvalid"))),
        ContAssign(
            Ref("wmask"),
            Concat(
                [Repl(Const(8), Bit(Ref("wstrb_q"), Const(i))) for i in reversed(range(strb_width))]
            )
            if strb_width > 1
            else Repl(Const(8), Bit(Ref("wstrb_q"), Const(0))),
        ),
    ]

    one = Const(1, width=Const(1), base=ConstBase.BIN)
    zero = _zeros(1)

    body: list[Stmt] = [
        Comment("Capture AW and W independently; either may arrive first",
                level=CommentLevel.VERBOSE),
        If(
            _land(Ref("awvalid"), Ref("awready")),
            then=[Assign(Ref("aw_hs"), one), Assign(Ref("awaddr_q"), Ref("awaddr"))],
        ),
        If(
            _land(Ref("wvalid"), Ref("wready")),
            then=[
                Assign(Ref("w_hs"), one),
                Assign(Ref("wdata_q"), Ref("wdata")),
                Assign(Ref("wstrb_q"), Ref("wstrb")),
            ],
        ),
        Comment("Both beats held and no response outstanding: execute the write",
                level=CommentLevel.VERBOSE),
        If(
            Ref("wr_exec"),
            then=[
                Assign(Ref("aw_hs"), zero),
                Assign(Ref("w_hs"), zero),
                Assign(Ref("bvalid"), one),
                # SLVERR for an unmapped address *or* an attempt to set a
                # reserved bit. Without the second term the reserved-bit check
                # would silently drop the write and still answer OKAY — the
                # write-rejected-but-reported-fine bug this caught.
                Assign(
                    Ref("bresp"),
                    Ternary(
                        _land(Ref("wr_hit"), _lnot(Ref("wr_reserved"))),
                        Const(AXI_RESP_OKAY, width=Const(2), base=ConstBase.BIN),
                        Const(AXI_RESP_SLVERR, width=Const(2), base=ConstBase.BIN),
                    ),
                ),
            ],
        ),
        If(_land(Ref("bvalid"), Ref("bready")), then=[Assign(Ref("bvalid"), zero)]),
        *_write_body(regmap),
        Comment("Registered read: capture the addressed word on the AR handshake",
                level=CommentLevel.VERBOSE),
        _read_body(regmap, data_width, addr_width),
        If(_land(Ref("rvalid"), Ref("rready")), then=[Assign(Ref("rvalid"), zero)]),
    ]

    always = AlwaysFF(
        clock=ClockSpec(AXI_CLOCK),
        reset=ResetSpec(
            name=AXI_RESET,
            kind=ResetKind.SYNC if sync_reset else ResetKind.ASYNC,
            active_low=True,
        ),
        reset_body=_reset_body(regmap, data_width),
        body=body,
    )

    items: list[ModuleItem] = [
        *signals,
        *handshake,
        *_decode_signals(regmap, addr_width),
        always,
    ]

    return Module(
        name=name,
        header=Header(
            license="",
            config_hash="",
            tool_version=VERSION,
            description=description or f"AXI4-Lite register block ({regmap.name})",
        ),
        params=[],
        ports=ports,
        items=items,
    )
