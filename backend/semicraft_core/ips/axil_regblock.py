"""AXI4-Lite register block — the first catalog IP (Phase-4 P4-02).

Wraps :func:`~.regblock.build_axil_regblock`, which is where the protocol
logic lives and which P4-05..P4-08 will call directly with their own register
maps. This file is the *catalog* face: an options model, a register map built
from it, port groups, the bus bundle, and a directed testbench recipe.

Why the options are counts, not a register map
----------------------------------------------

The obvious design — let the user declare registers and fields — is not
reachable from the UI: the option form is JSON-Schema-driven and renders
enums, booleans, bounded numbers, string arrays and nested objects, but has no
widget for an array of objects. Shipping an options model the form cannot
render would mean an IP configurable only through the API, which is worse than
an honest restriction.

So the catalog IP exposes *how many* registers of each access type it should
have, and builds the map itself. Arbitrary maps are a first-class capability
of the engine underneath, just not of this catalog entry — that is what the
protocol IPs use, and a register-map authoring UI is a later work package.

Registers are always numbered (``CTRL0``, ``CTRL1``, ...) even when there is
only one, so a hardware-face port name does not change meaning when a count
changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import Field, model_validator

from ..assertions.spec import (
    AssertionItem,
    AssertionSpec,
    ResetContext,
    ResetKnownValue,
)
from ..ir.nodes import Module
from ..modules.contract import PortGroup, TbSpec
from ..snippets.contract import CommonOptions, ExplanationDoc, SignalDoc
from .bundles import BundlePort, PortBundle
from .regblock import (
    AXI_CLOCK,
    AXI_RESET,
    AXI_RESP_OKAY,
    AxilSequencer,
    RegisterModel,
    axil_ports,
    build_axil_regblock,
    hardware_ports,
    hw_port_name,
    w1c_set_port_name,
    write_reserved_mask,
)
from .regmap import Register, RegisterField, RegisterMap
from .verification import VerificationSpec, axil_verification

_MODULE_NAME = "axil_regblock"


# --------------------------------------------------------------------------- #
# Options
# --------------------------------------------------------------------------- #


class AxilRegblockOptions(CommonOptions):
    """Configuration for the AXI4-Lite register block.

    Extends :class:`CommonOptions` rather than ``ClockedOptions``: AXI4-Lite
    mandates an **active-low** reset, so a polarity option would only be able
    to produce a non-conforming block. Rather than offer it and reject it, the
    option does not exist. ``reset_style`` remains a real choice — the spec
    does not dictate synchronous vs asynchronous de-assertion.
    """

    data_width: Literal[32, 64] = Field(
        default=32, description="AXI data bus width in bits."
    )
    reset_style: Literal["sync", "async"] = Field(
        default="sync",
        description=(
            "Reset timing. 'sync' samples the active-low reset on the clock "
            "edge; 'async' adds it to the sensitivity list. The polarity is "
            "fixed active-low by AXI4-Lite and is not configurable."
        ),
    )
    control_regs: int = Field(
        default=1, ge=0, le=8, description="Read/write control registers (CTRLn)."
    )
    status_regs: int = Field(
        default=1, ge=0, le=8, description="Read-only status registers (STATUSn)."
    )
    irq_regs: int = Field(
        default=1,
        ge=0,
        le=8,
        description="Write-1-to-clear interrupt-flag registers (IRQn).",
    )
    command_regs: int = Field(
        default=1,
        ge=0,
        le=8,
        description="Write-only command registers (CMDn).",
    )
    include_scratch: bool = Field(
        default=True,
        description=(
            "Add a full-width read/write SCRATCH register — the conventional "
            "way to prove the bus works end to end."
        ),
    )
    split_fields: bool = Field(
        default=True,
        description=(
            "Give each register named sub-fields with reserved gaps between "
            "them. When false, every register is a single full-width field, "
            "which leaves no reserved bits to reject."
        ),
    )

    @model_validator(mode="after")
    def _at_least_one_register(self) -> AxilRegblockOptions:
        if self._register_count == 0:
            raise ValueError(
                "the register block needs at least one register: raise one of "
                "control_regs / status_regs / irq_regs / command_regs, or set "
                "include_scratch"
            )
        return self

    @property
    def _register_count(self) -> int:
        return (
            self.control_regs
            + self.status_regs
            + self.irq_regs
            + self.command_regs
            + (1 if self.include_scratch else 0)
        )


# --------------------------------------------------------------------------- #
# Register map
# --------------------------------------------------------------------------- #


def _fields_for(kind: str, opts: AxilRegblockOptions) -> list[RegisterField]:
    """Field layout for one register family.

    With ``split_fields`` the layouts leave deliberate gaps (bit 3 of a control
    register, bits 3:1 of a status register) so the reserved-bit rejection has
    something to reject; without it each register is one full-width field.
    """
    dw = opts.data_width
    if not opts.split_fields:
        access = {"control": "rw", "status": "ro", "irq": "w1c", "command": "wo"}[kind]
        return [
            RegisterField(
                name="value",
                lsb=0,
                width=dw,
                access=access,
                description=f"Whole-word {access.upper()} value.",
            )
        ]
    if kind == "control":
        return [
            RegisterField(
                name="enable", lsb=0, width=1, access="rw", reset=1,
                description="Enable output; set out of reset.",
            ),
            RegisterField(
                name="mode", lsb=1, width=2, access="rw",
                description="Two-bit mode output.",
            ),
            RegisterField(
                name="level", lsb=4, width=4, access="rw",
                description="Four-bit level output (bit 3 is reserved).",
            ),
        ]
    if kind == "status":
        return [
            RegisterField(
                name="busy", lsb=0, width=1, access="ro",
                description="Hardware busy indication.",
            ),
            RegisterField(
                name="code", lsb=4, width=4, access="ro",
                description="Hardware status code.",
            ),
        ]
    if kind == "irq":
        return [
            RegisterField(
                name="flags", lsb=0, width=4, access="w1c",
                description="Interrupt flags; hardware sets, software writes 1 to clear.",
            )
        ]
    return [
        RegisterField(
            name="go", lsb=0, width=1, access="wo",
            description="Command strobe; reads back as zero.",
        ),
        RegisterField(
            name="code", lsb=1, width=3, access="wo",
            description="Command code; reads back as zero.",
        ),
    ]


_FAMILIES = (
    ("control", "CTRL", "Control register"),
    ("status", "STATUS", "Status register"),
    ("irq", "IRQ", "Interrupt flags"),
    ("command", "CMD", "Command register"),
)


def register_map(opts: AxilRegblockOptions) -> RegisterMap:
    """Build the register map the options describe."""
    stride = opts.data_width // 8
    registers: list[Register] = []
    offset = 0
    for kind, prefix, blurb in _FAMILIES:
        count = getattr(opts, f"{kind}_regs")
        for i in range(count):
            registers.append(
                Register(
                    name=f"{prefix}{i}",
                    offset=offset,
                    description=f"{blurb} {i}.",
                    fields=_fields_for(kind, opts),
                )
            )
            offset += stride
    if opts.include_scratch:
        registers.append(
            Register(
                name="SCRATCH",
                offset=offset,
                description="Full-width scratch register; reads back what was written.",
                fields=[
                    RegisterField(
                        name="value", lsb=0, width=opts.data_width, access="rw",
                        description="Scratch value.",
                    )
                ],
            )
        )
        offset += stride

    # Decode exactly the span the map needs. A tighter window keeps the
    # unmapped-address error path reachable (the byte offsets inside the span
    # decode to nothing) without inventing address bits nobody asked for.
    span = offset
    addr_width = max((span - 1).bit_length(), 1)
    return RegisterMap(
        name="REGS",
        data_width=opts.data_width,
        addr_width=addr_width,
        registers=registers,
    )


def generate(opts: AxilRegblockOptions) -> Module:
    """Build the register block IR (pure)."""
    return build_axil_regblock(
        _MODULE_NAME,
        register_map(opts),
        sync_reset=opts.reset_style == "sync",
        description=_description(opts),
    )


def _description(opts: AxilRegblockOptions) -> str:
    regmap = register_map(opts)
    return (
        f"AXI4-Lite register block, {opts.data_width}-bit data, "
        f"{len(regmap.registers)} register(s)"
    )


# --------------------------------------------------------------------------- #
# Directed testbench recipe
# --------------------------------------------------------------------------- #


def _first_with_rw(regmap: RegisterMap) -> Register | None:
    for reg in regmap.registers:
        if any(f.access == "rw" for f in reg.fields):
            return reg
    return None


def _first_with(regmap: RegisterMap, access: str) -> Register | None:
    for reg in regmap.registers:
        if any(f.access == access for f in reg.fields):
            return reg
    return None


def _unmapped_address(regmap: RegisterMap) -> int | None:
    """The lowest address inside the decode window that no register claims.

    ``None`` when the map tiles its window exactly (a byte-wide bus, where the
    stride is 1), in which case there is no unmapped address to test.
    """
    taken = {reg.offset for reg in regmap.registers}
    for addr in range(1 << regmap.addr_width):
        if addr not in taken:
            return addr
    return None


def _distinct_value(f: RegisterField) -> int:
    """A field value that differs from its reset, so a check proves the write.

    Writing a field's own reset value back would pass whether or not the write
    logic works at all.
    """
    top = (1 << f.width) - 1
    return 0 if f.reset != 0 else top


def tb_spec(opts: AxilRegblockOptions) -> TbSpec:
    """A directed AXI4-Lite transaction sequence.

    Every phase is guarded on the map actually containing what it needs, so a
    configuration with (say) no interrupt registers simply skips the
    write-1-to-clear phase instead of checking a port that does not exist.

    Expected values come from :class:`_Model`, which implements the access-type
    rules independently of the generator. If the two ever disagree, the
    Verilator run gate fails — which is the point.
    """
    regmap = register_map(opts)
    dw = opts.data_width
    full_strb = (1 << (dw // 8)) - 1
    model = RegisterModel(regmap)
    seq = AxilSequencer()

    # Cycle 0: nothing driven — just assert the post-reset state. A target must
    # not be asserting a response out of reset, and must be ready to accept.
    seq.expect(0, "bvalid", 0)
    seq.expect(0, "rvalid", 0)
    seq.expect(0, "awready", 1)
    seq.expect(0, "wready", 1)
    seq.expect(0, "arready", 1)
    for reg in regmap.registers:
        for f in reg.fields:
            if f.access != "ro":
                seq.expect(0, hw_port_name(reg, f), f.reset)
    seq.idle()

    # Phase 1 — write a read/write register, then read it back.
    target = _first_with_rw(regmap)
    if target is not None:
        data = 0
        after: list[tuple[str, int]] = []
        for f in target.fields:
            if f.access == "rw":
                value = _distinct_value(f)
                data |= value << f.lsb
                after.append((hw_port_name(target, f), value))
        resp = model.write(target.offset, data, full_strb)
        seq.write(target.offset, data, full_strb, resp, after)
        seq.read(target.offset, *model.read(target.offset))

    # Phase 2 — an address inside the decode window that no register claims.
    bad = _unmapped_address(regmap)
    if bad is not None:
        seq.read(bad, *model.read(bad))

    # Phase 3 — a write that tries to set a reserved bit must be rejected
    # *and* must leave the register untouched.
    if target is not None:
        reserved = write_reserved_mask(target, dw)
        if reserved:
            bit = (reserved & -reserved).bit_length() - 1
            unchanged = [
                (hw_port_name(target, f), model.field(target.name, f.name))
                for f in target.fields
                if f.access != "ro"
            ]
            resp = model.write(target.offset, 1 << bit, full_strb)
            seq.write(target.offset, 1 << bit, full_strb, resp, unchanged)

    # Phase 4 — write-1-to-clear: hardware sets flags, software clears one.
    irq = _first_with(regmap, "w1c")
    if irq is not None:
        f = next(f for f in irq.fields if f.access == "w1c")
        port = hw_port_name(irq, f)
        set_value = (1 << f.width) - 1
        model.hardware_set(irq.name, f.name, set_value)
        seq.pulse_input(
            w1c_set_port_name(irq, f), set_value, [(port, model.field(irq.name, f.name))]
        )
        clear = 1 << (f.width - 1) << f.lsb
        resp = model.write(irq.offset, clear, full_strb)
        seq.write(irq.offset, clear, full_strb, resp, [(port, model.field(irq.name, f.name))])
        seq.read(irq.offset, *model.read(irq.offset))

    # Phase 5 — byte strobes. Needs a full-width writable register, so that a
    # partial-strobe write has untouched bytes to preserve.
    if opts.include_scratch:
        scratch = regmap.register("SCRATCH")
        port = hw_port_name(scratch, scratch.fields[0])
        pattern = int("".join(f"{0xA0 + i:02X}" for i in range(dw // 8)), 16)
        model.write(scratch.offset, pattern, full_strb)
        seq.write(
            scratch.offset, pattern, full_strb, AXI_RESP_OKAY,
            [(port, model.field(scratch.name, "value"))],
        )
        # Every other byte enabled: the disabled bytes must survive.
        partial = int("55" * (dw // 16 or 1), 16) & full_strb
        if partial and partial != full_strb:
            other = ~pattern & ((1 << dw) - 1)
            model.write(scratch.offset, other, partial)
            seq.write(
                scratch.offset, other, partial, AXI_RESP_OKAY,
                [(port, model.field(scratch.name, "value"))],
            )
            seq.read(scratch.offset, *model.read(scratch.offset))

    # Phase 6 — a read-only register reflects its hardware inputs.
    status = _first_with(regmap, "ro")
    if status is not None:
        extra: dict[str, int] = {}
        for f in status.fields:
            if f.access == "ro":
                value = (1 << f.width) - 1
                extra[hw_port_name(status, f)] = value
                model.drive_ro(status.name, f.name, value)
        seq.read(status.offset, *model.read(status.offset), extra=extra)

    # Phase 7 — a write-only register reads back as zero, not as what was
    # written to it.
    cmd = _first_with(regmap, "wo")
    if cmd is not None:
        data = 0
        after = []
        for f in cmd.fields:
            if f.access == "wo":
                value = (1 << f.width) - 1
                data |= value << f.lsb
                after.append((hw_port_name(cmd, f), value))
        resp = model.write(cmd.offset, data, full_strb)
        seq.write(cmd.offset, data, full_strb, resp, after)
        seq.read(cmd.offset, *model.read(cmd.offset))

    items: list[AssertionItem] = [
        ResetKnownValue(name="bvalid_idle_after_reset", signal="bvalid", value=0, width=1),
        ResetKnownValue(name="rvalid_idle_after_reset", signal="rvalid", value=0, width=1),
    ]

    return TbSpec(
        clock=AXI_CLOCK,
        reset=AXI_RESET,
        reset_cycles=2,
        vectors=seq.vectors,
        checks=seq.checks,
        assertion_spec=AssertionSpec(
            clock=AXI_CLOCK,
            items=items,
            reset=ResetContext(
                signal=AXI_RESET,
                active_low=True,
                sync=opts.reset_style == "sync",
            ),
        ),
    )


# --------------------------------------------------------------------------- #
# Documentation metadata
# --------------------------------------------------------------------------- #


def port_groups(opts: AxilRegblockOptions) -> list[PortGroup]:
    """Clocking, the AXI4-Lite face, and the hardware face."""
    regmap = register_map(opts)
    return [
        PortGroup(
            name="Clocking",
            ports=[AXI_CLOCK, f"{AXI_RESET}_n"],
            description="Single AXI clock domain; the reset is active-low per the spec.",
        ),
        PortGroup(
            name="AXI4-Lite slave",
            ports=list(axil_ports()),
            description="AXI4-Lite target port (bundle `s_axil`).",
        ),
        PortGroup(
            name="Hardware face",
            ports=[name for name, _dir, _w in hardware_ports(regmap)],
            description="Register field values driven to, and sampled from, the design.",
        ),
    ]


def bundles(opts: AxilRegblockOptions) -> list[PortBundle]:  # noqa: ARG001 - fixed bus
    """The AXI4-Lite target bundle.

    Role names are the protocol's own spelling, so an interconnect matches on
    ``awvalid`` regardless of the naming style the user picked. The hardware
    face is deliberately not bundled — it is this IP's own interface, not a
    protocol port.
    """
    return [
        PortBundle(
            name="s_axil",
            protocol="axi4-lite",
            role="target",
            clock=AXI_CLOCK,
            reset=AXI_RESET,
            description="AXI4-Lite target port serving the register map.",
            ports=[BundlePort(signal=sig, role_name=sig) for sig in axil_ports()],
        )
    ]


def explain(opts: AxilRegblockOptions) -> ExplanationDoc:
    regmap = register_map(opts)
    signals = [
        SignalDoc(name=AXI_CLOCK, direction="input", description="AXI clock."),
        SignalDoc(
            name=f"{AXI_RESET}_n",
            direction="input",
            description="AXI reset, active-low (the spec calls it ARESETn).",
        ),
    ]
    axi_docs = {
        "awaddr": ("input", "Write address; the full byte address is decoded."),
        "awvalid": ("input", "Write address valid."),
        "awready": ("output", "Write address ready; depends on registers only."),
        "wdata": ("input", "Write data."),
        "wstrb": ("input", "Write byte strobes, one bit per byte."),
        "wvalid": ("input", "Write data valid."),
        "wready": ("output", "Write data ready; depends on registers only."),
        "bresp": ("output", "Write response: OKAY, or SLVERR if unmapped or reserved."),
        "bvalid": ("output", "Write response valid."),
        "bready": ("input", "Write response ready."),
        "araddr": ("input", "Read address; the full byte address is decoded."),
        "arvalid": ("input", "Read address valid."),
        "arready": ("output", "Read address ready."),
        "rdata": ("output", "Read data, captured on the AR handshake."),
        "rresp": ("output", "Read response: OKAY, or SLVERR if unmapped."),
        "rvalid": ("output", "Read data valid."),
        "rready": ("input", "Read data ready."),
    }
    for sig in axil_ports():
        direction, text = axi_docs[sig]
        signals.append(SignalDoc(name=sig, direction=direction, description=text))
    for reg in regmap.registers:
        for f in reg.fields:
            label = f"{reg.name}.{f.name} ({f.access.upper()})"
            if f.access == "ro":
                signals.append(
                    SignalDoc(
                        name=hw_port_name(reg, f),
                        direction="input",
                        description=f"{label} — sampled into read data.",
                    )
                )
                continue
            signals.append(
                SignalDoc(
                    name=hw_port_name(reg, f),
                    direction="output",
                    description=f"{label} — current field value.",
                )
            )
            if f.access == "w1c":
                signals.append(
                    SignalDoc(
                        name=w1c_set_port_name(reg, f),
                        direction="input",
                        description=f"{label} — hardware set; beats a same-cycle clear.",
                    )
                )

    return ExplanationDoc(
        purpose=(
            "An AXI4-Lite target that serves a register map: address decode, "
            "byte-strobe writes, per-access-type field behaviour, and a "
            "registered read path. The register-map metadata it is built from "
            "is the same model the datasheet is rendered from, so the two "
            "cannot drift."
        ),
        configuration=[
            f"Data width: {opts.data_width} bits "
            f"({regmap.stride_bytes}-byte address stride)",
            f"Address width: {regmap.addr_width} bits "
            f"({1 << regmap.addr_width} B decoded, {regmap.span_bytes()} B used)",
            f"Registers: {len(regmap.registers)} "
            f"(control {opts.control_regs}, status {opts.status_regs}, "
            f"irq {opts.irq_regs}, command {opts.command_regs}"
            f"{', scratch' if opts.include_scratch else ''})",
            f"Field layout: {'named sub-fields' if opts.split_fields else 'whole-word'}",
            f"Reset: {opts.reset_style}, active-low (fixed by AXI4-Lite)",
            f"Output language: {'SystemVerilog' if opts.language == 'sv' else 'Verilog-2001'}",
        ],
        signals=signals,
        reset_behavior=(
            f"The active-low {opts.reset_style} reset clears both channel "
            "handshakes and drops bvalid/rvalid, so the block accepts a "
            "transaction on the first cycle after release; every writable "
            "field returns to its declared reset value."
        ),
        assumptions=[
            "One AXI clock domain; the hardware face is synchronous to it.",
            "A single outstanding transaction per channel — a new write is "
            "accepted only once the previous response has been taken.",
            "awready/wready are functions of registers only, never of "
            "awvalid/wvalid, so there is no combinational valid-to-ready path.",
        ],
        limitations=[
            "No awprot/arprot: the block enforces no protection policy, so "
            "declaring inputs it never reads would be dead logic (and would "
            "fail the project's -Wall lint gate). An interconnect that drives "
            "them simply leaves them unconnected.",
            "The full byte address is decoded, so an access whose low offset "
            "bits are non-zero returns SLVERR rather than aliasing onto the "
            "containing word.",
            "Writing a 1 into a reserved bit returns SLVERR and performs no "
            "update — stricter than a block that silently ignores such bits.",
            "The reset is named areset and renders areset_n; the spec spells "
            "it ARESETn. The naming engine owns the active-low suffix, and "
            "integration matches on bundle roles rather than spelling.",
            "One transaction at a time: no write/read overlap, no pipelining.",
        ],
    )


# --------------------------------------------------------------------------- #
# IpDef instance (discovered by the registry)
# --------------------------------------------------------------------------- #


def verification_spec(opts: AxilRegblockOptions) -> VerificationSpec:
    """The shared AXI4-Lite monitor + liveness/stability checker.

    Every AXI IP splices in the same register-block frontend, so they all have
    the same bus face and the same bus properties; the scaffold is written once
    in ``ips/verification.py`` rather than eight times across the catalog.

    This is the one IP whose data width is configurable, so it is also the one
    that has to pass it through: the scaffold declares ``rdata`` as a port, and
    a 32-bit port bound to a 64-bit net does not compile. The composed
    peripherals all fix the width at 32 and take the default.
    """
    return axil_verification(_MODULE_NAME, data_width=opts.data_width)


@dataclass(frozen=True)
class _AxilRegblockIp:
    """Satisfies :class:`~.contract.IpDef` structurally."""

    id: str = "axil-regblock"
    name: str = "AXI4-Lite Register Block"
    description: str = (
        "AXI4-Lite target serving a configurable register map: byte-strobe "
        "writes, read/write, read-only, write-only and write-1-to-clear "
        "fields, and SLVERR on unmapped or reserved-bit accesses."
    )
    kind: str = "ip"
    maturity: str = "beta"
    options_model: type[AxilRegblockOptions] = AxilRegblockOptions

    def generate(self, opts: AxilRegblockOptions) -> Module:
        return generate(opts)

    def explain(self, opts: AxilRegblockOptions) -> ExplanationDoc:
        return explain(opts)

    def port_groups(self, opts: AxilRegblockOptions) -> list[PortGroup]:
        return port_groups(opts)

    def tb_spec(self, opts: AxilRegblockOptions) -> TbSpec:
        return tb_spec(opts)

    def register_map(self, opts: AxilRegblockOptions) -> RegisterMap:
        return register_map(opts)

    def bundles(self, opts: AxilRegblockOptions) -> list[PortBundle]:
        return bundles(opts)

    def verification_spec(self, opts: AxilRegblockOptions) -> VerificationSpec:
        return verification_spec(opts)


IP = _AxilRegblockIp()

__all__ = [
    "AxilRegblockOptions",
    "generate",
    "explain",
    "port_groups",
    "tb_spec",
    "register_map",
    "bundles",
    "verification_spec",
    "IP",
]
