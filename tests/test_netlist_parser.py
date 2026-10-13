"""
test_netlist_parser.py - Unit tests for structured graph G=(V,E),
SPICE netlist export, and 4-category topology validation.
"""

import pytest
from app.core.netlist_parser import CircuitGraph, Component, validate_circuit_topology

def test_valid_topology():
    graph = CircuitGraph("Test Valid Divider")
    graph.add_component(Component("VIN", "VOLTAGE_SOURCE", 10.0, "V", ["in", "0"]))
    graph.add_component(Component("R1", "RESISTOR", 10000.0, "Ω", ["in", "out"]))
    graph.add_component(Component("R2", "RESISTOR", 10000.0, "Ω", ["out", "0"]))

    findings = validate_circuit_topology(graph, "voltage_divider")
    # Valid circuit should have 0 topology violations
    assert len(findings) == 0

    spice = graph.to_spice_netlist()
    assert "VIN in 0 10.0" in spice
    assert "R1 in out 10000.0" in spice
    assert "R2 out 0 10000.0" in spice

def test_missing_ground_detection():
    graph = CircuitGraph("Floating Divider")
    graph.add_component(Component("VIN", "VOLTAGE_SOURCE", 10.0, "V", ["in", "ret"]))
    graph.add_component(Component("R1", "RESISTOR", 10000.0, "Ω", ["in", "out"]))
    graph.add_component(Component("R2", "RESISTOR", 10000.0, "Ω", ["out", "ret"]))

    findings = validate_circuit_topology(graph)
    gnd_findings = [f for f in findings if f["component_or_net"] == "GND"]
    assert len(gnd_findings) == 1
    assert gnd_findings[0]["severity"] == "Critical"

def test_shorted_component_detection():
    graph = CircuitGraph("Shorted Resistor")
    graph.add_component(Component("VIN", "VOLTAGE_SOURCE", 10.0, "V", ["in", "0"]))
    # R1 connected from 'in' to 'in' (direct short!)
    graph.add_component(Component("R1", "RESISTOR", 10000.0, "Ω", ["in", "in"]))
    graph.add_component(Component("R2", "RESISTOR", 10000.0, "Ω", ["in", "0"]))

    findings = validate_circuit_topology(graph)
    short_findings = [f for f in findings if "short" in f["evidence"].lower()]
    assert len(short_findings) >= 1
