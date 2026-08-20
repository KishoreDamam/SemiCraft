"""Register-map model: every validation rule and every derived value (P4-01).

Rules R1-R6 are documented in ``semicraft_core/ips/regmap.py``. Each has at
least one test that *fails* construction, because a validation rule with only
a happy-path test is a rule nobody has checked actually fires.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from semicraft_core.ips.regmap import Register, RegisterField, RegisterMap


def _field(name="f", lsb=0, width=1, **kw) -> RegisterField:
    return RegisterField(name=name, lsb=lsb, width=width, **kw)


# --------------------------------------------------------------------------- #
# RegisterField
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("lsb", "width", "msb", "rng", "mask"),
    [
        (0, 1, 0, "[0]", 0b1),
        (1, 2, 2, "[2:1]", 0b110),
        (8, 8, 15, "[15:8]", 0xFF00),
    ],
)
def test_field_geometry(lsb, width, msb, rng, mask) -> None:
    f = _field(lsb=lsb, width=width)
    assert (f.msb, f.bit_range, f.mask) == (msb, rng, mask)


def test_field_name_must_be_lower_snake() -> None:
    with pytest.raises(ValidationError, match="lower_snake_case"):
        _field(name="Enable")
    with pytest.raises(ValidationError, match="lower_snake_case"):
        _field(name="_enable")
    _field(name="enable_2")  # digits and underscores are fine


def test_field_reset_must_fit_width() -> None:
    _field(width=2, reset=3)  # exactly fits
    with pytest.raises(ValidationError, match="does not fit in 2 bit"):
        _field(width=2, reset=4)


def test_field_is_frozen() -> None:
    f = _field()
    with pytest.raises(ValidationError):
        f.lsb = 4


# --------------------------------------------------------------------------- #
# Register
# --------------------------------------------------------------------------- #


def test_register_name_must_be_upper_snake() -> None:
    with pytest.raises(ValidationError, match="UPPER_SNAKE_CASE"):
        Register(name="ctrl", offset=0)
    Register(name="CTRL_2", offset=0)


def test_register_rejects_duplicate_field_names() -> None:
    with pytest.raises(ValidationError, match="duplicate field name"):
        Register(name="CTRL", offset=0, fields=[_field("a", 0), _field("a", 1)])


def test_register_rejects_overlapping_fields() -> None:
    with pytest.raises(ValidationError, match="overlaps or precedes"):
        Register(
            name="CTRL", offset=0, fields=[_field("a", 0, width=4), _field("b", 2)]
        )


def test_register_rejects_descending_field_order() -> None:
    """Fields must be *listed* ascending; the model never silently sorts."""
    with pytest.raises(ValidationError, match="overlaps or precedes"):
        Register(name="CTRL", offset=0, fields=[_field("hi", 4), _field("lo", 0)])


def test_register_allows_gaps_between_fields() -> None:
    reg = Register(name="CTRL", offset=0, fields=[_field("a", 0), _field("b", 8)])
    assert reg.reserved_mask(32) == 0xFFFFFEFE


def test_register_reset_value_packs_fields() -> None:
    reg = Register(
        name="CTRL",
        offset=0,
        fields=[_field("enable", 0, reset=1), _field("mode", 1, width=2, reset=2)],
    )
    assert reg.reset_value() == 0b101


def test_register_read_reset_value_hides_write_only_fields() -> None:
    """A WO field holds a reset value in hardware but reads back as zero."""
    reg = Register(
        name="CMD",
        offset=0,
        fields=[
            _field("go", 0, reset=1, access="wo"),
            _field("keep", 1, reset=1, access="rw"),
        ],
    )
    assert reg.reset_value() == 0b11
    assert reg.read_reset_value() == 0b10


def test_register_field_lookup() -> None:
    reg = Register(name="CTRL", offset=0, fields=[_field("enable", 0)])
    assert reg.field("enable").lsb == 0
    with pytest.raises(KeyError, match="no field 'missing'"):
        reg.field("missing")


# --------------------------------------------------------------------------- #
# RegisterMap
# --------------------------------------------------------------------------- #


def _map(**kw) -> RegisterMap:
    kw.setdefault("name", "CSR")
    return RegisterMap(**kw)


@pytest.mark.parametrize("data_width", [8, 16, 32, 64])
def test_map_accepts_byte_multiple_widths(data_width: int) -> None:
    assert _map(data_width=data_width).stride_bytes == data_width // 8


@pytest.mark.parametrize("data_width", [1, 12, 24, 128])
def test_map_rejects_other_data_widths(data_width: int) -> None:
    with pytest.raises(ValidationError, match="must be one of"):
        _map(data_width=data_width)


def test_map_rejects_duplicate_register_names() -> None:
    with pytest.raises(ValidationError, match="duplicate register name"):
        _map(registers=[Register(name="A", offset=0), Register(name="A", offset=4)])


def test_map_rejects_descending_offsets() -> None:
    with pytest.raises(ValidationError, match="strictly ascending offset order"):
        _map(registers=[Register(name="B", offset=4), Register(name="A", offset=0)])


def test_map_rejects_duplicate_offsets() -> None:
    """Same offset twice is caught by the strictly-ascending rule."""
    with pytest.raises(ValidationError, match="strictly ascending offset order"):
        _map(registers=[Register(name="A", offset=0), Register(name="B", offset=0)])


def test_map_rejects_misaligned_offset() -> None:
    with pytest.raises(ValidationError, match="not aligned to the 4-byte stride"):
        _map(data_width=32, registers=[Register(name="A", offset=2)])
    # The same offset is legal at a byte stride.
    _map(data_width=8, addr_width=4, registers=[Register(name="A", offset=2)])


def test_map_rejects_register_past_the_address_space() -> None:
    with pytest.raises(ValidationError, match="does not fit inside the 16-byte space"):
        _map(addr_width=4, registers=[Register(name="A", offset=16)])
    # The last word that *does* fit is at limit - stride.
    _map(addr_width=4, registers=[Register(name="A", offset=12)])


def test_map_rejects_field_wider_than_the_word() -> None:
    reg = Register(name="A", offset=0, fields=[_field("big", lsb=4, width=8)])
    with pytest.raises(ValidationError, match=r"does not fit in a 8-bit word"):
        _map(data_width=8, addr_width=4, registers=[reg])
    _map(data_width=32, registers=[reg])  # fine in a wider word


def test_map_span_and_lookup() -> None:
    m = _map(registers=[Register(name="A", offset=0), Register(name="B", offset=8)])
    assert m.span_bytes() == 12  # highest offset + one stride, not the decoded space
    assert m.register("B").offset == 8
    assert m.at_offset(0).name == "A"
    with pytest.raises(KeyError, match="no register 'C'"):
        m.register("C")
    with pytest.raises(KeyError, match="no register at offset 0x4"):
        m.at_offset(4)


def test_empty_map_spans_nothing() -> None:
    assert _map().span_bytes() == 0


def test_sequences_are_tuples_so_frozen_is_a_real_promise() -> None:
    """``frozen=True`` on a model whose sequences are lists is only half true —
    a caller can still append. These are tuples, so it holds."""
    m = _map(registers=[Register(name="A", offset=0, fields=[_field("x", 0)])])
    assert isinstance(m.registers, tuple)
    assert isinstance(m.registers[0].fields, tuple)
    with pytest.raises(AttributeError):
        m.registers.append(Register(name="B", offset=4))
