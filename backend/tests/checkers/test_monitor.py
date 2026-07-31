"""Monitor family (P3-06) coverage: exact emission, determinism, validation."""

from __future__ import annotations

import pytest
from semicraft_core.checkers import MonitorSpec, Signal, generate_monitor


def test_qualified_monitor_exact_text() -> None:
    spec = MonitorSpec(
        name="axi_mon",
        clock="clk",
        fields=[Signal("valid", 1), Signal("ready", 1), Signal("data", 8)],
        qualifier="valid && ready",
    )
    assert generate_monitor(spec) == (
        "module axi_mon (\n"
        "    input logic clk,\n"
        "    input logic valid,\n"
        "    input logic ready,\n"
        "    input logic [7:0] data\n"
        ");\n"
        "\n"
        "    // Passive monitor: samples the bundle on posedge clk when valid && ready\n"
        "    always @(posedge clk) begin\n"
        "        if (valid && ready) begin\n"
        '            $display("[%0t] axi_mon: valid=%0d ready=%0d data=%0d", '
        "$time, valid, ready, data);\n"
        "        end\n"
        "    end\n"
        "\n"
        "endmodule\n"
    )


def test_unqualified_monitor_samples_every_edge() -> None:
    spec = MonitorSpec(
        name="simple_mon",
        clock="clk",
        fields=[Signal("data", 4)],
    )
    text = generate_monitor(spec)
    assert "if (" not in text
    assert "always @(posedge clk) begin" in text
    assert '$display("[%0t] simple_mon: data=%0d", $time, data);' in text


def test_monitor_with_no_fields() -> None:
    spec = MonitorSpec(name="tick_mon", clock="clk", fields=[])
    assert generate_monitor(spec) == (
        "module tick_mon (\n"
        "    input logic clk\n"
        ");\n"
        "\n"
        "    // Passive monitor: samples the bundle on posedge clk\n"
        "    always @(posedge clk) begin\n"
        '        $display("[%0t] tick_mon", $time);\n'
        "    end\n"
        "\n"
        "endmodule\n"
    )


def test_single_bit_fields_render_bare_ports() -> None:
    spec = MonitorSpec(
        name="m", clock="clk", fields=[Signal("valid"), Signal("ready")]
    )
    text = generate_monitor(spec)
    assert "input logic valid,\n" in text
    assert "input logic ready\n" in text
    assert "[0:0]" not in text


def test_multi_bit_field_renders_ranged_port() -> None:
    spec = MonitorSpec(name="m", clock="clk", fields=[Signal("data", 8)])
    text = generate_monitor(spec)
    assert "input logic [7:0] data\n" in text


def test_determinism_same_spec_same_output() -> None:
    spec = MonitorSpec(
        name="axi_mon",
        clock="clk",
        fields=[Signal("valid", 1), Signal("ready", 1), Signal("data", 8)],
        qualifier="valid && ready",
    )
    assert generate_monitor(spec) == generate_monitor(spec)


def test_duplicate_field_name_rejected() -> None:
    spec = MonitorSpec(
        name="m", clock="clk", fields=[Signal("a", 1), Signal("a", 2)]
    )
    with pytest.raises(ValueError, match="duplicate monitor port name: 'a'"):
        generate_monitor(spec)


def test_field_colliding_with_clock_name_rejected() -> None:
    spec = MonitorSpec(name="m", clock="clk", fields=[Signal("clk", 1)])
    with pytest.raises(ValueError, match="duplicate monitor port name: 'clk'"):
        generate_monitor(spec)


def test_field_order_is_preserved_in_ports_and_display() -> None:
    spec = MonitorSpec(
        name="m",
        clock="clk",
        fields=[Signal("c", 1), Signal("a", 1), Signal("b", 1)],
    )
    text = generate_monitor(spec)
    port_lines = [ln for ln in text.splitlines() if ln.strip().startswith("input logic")]
    assert [ln.split()[-1].rstrip(",") for ln in port_lines] == ["clk", "c", "a", "b"]
    assert "c=%0d a=%0d b=%0d" in text
