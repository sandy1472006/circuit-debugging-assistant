"""
reference_generator.py - Generates Reference Circuit, Corrected Circuit,
and vector SVG schematic diagrams for the 4-panel comparison view.
"""

from typing import Dict, List, Tuple, Any, Optional

def generate_reference_circuit(circuit_type: str, custom_params: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """Generates standard validated reference circuit topology and values."""
    params = custom_params or {}
    if circuit_type == "voltage_divider":
        ref_params = {
            "R1": float(params.get("R1", 10000.0)),
            "R2": float(params.get("R2", 5000.0)),
            "Vin": float(params.get("Vin", 10.0))
        }
        description = "Standard 2-resistor voltage divider with grounded lower leg and mid-point output node."
        equations = [
            "V_{out} = V_{in} \\cdot \\frac{R_2}{R_1 + R_2}",
            "I_{supply} = \\frac{V_{in}}{R_1 + R_2}"
        ]
        components = [
            {"ref": "VIN", "type": "VOLTAGE_SOURCE", "value": ref_params["Vin"], "unit": "V", "nodes": ["in", "0"]},
            {"ref": "R1", "type": "RESISTOR", "value": ref_params["R1"], "unit": "Ω", "nodes": ["in", "out"]},
            {"ref": "R2", "type": "RESISTOR", "value": ref_params["R2"], "unit": "Ω", "nodes": ["out", "0"]}
        ]
    elif circuit_type == "rc_low_pass":
        ref_params = {
            "R": float(params.get("R", 10000.0)),
            "C": float(params.get("C", 100e-9)),
            "Vin": float(params.get("Vin", 5.0))
        }
        description = "First-order passive RC low-pass filter with series resistor and shunt capacitor to ground."
        equations = [
            "H(f) = \\frac{1}{1 + j 2\\pi f R C}",
            "f_c = \\frac{1}{2\\pi R C}",
            "I_{step}(0^+) = \\frac{V_{in}}{R}"
        ]
        components = [
            {"ref": "VIN", "type": "VOLTAGE_SOURCE", "value": ref_params["Vin"], "unit": "V", "nodes": ["in", "0"]},
            {"ref": "R1", "type": "RESISTOR", "value": ref_params["R"], "unit": "Ω", "nodes": ["in", "out"]},
            {"ref": "C1", "type": "CAPACITOR", "value": ref_params["C"], "unit": "F", "nodes": ["out", "0"]}
        ]
    elif circuit_type == "rl_high_pass":
        ref_params = {
            "R": float(params.get("R", 1000.0)),
            "L": float(params.get("L", 0.01)),
            "Vin": float(params.get("Vin", 5.0))
        }
        description = "First-order passive RL high-pass filter with series resistor and shunt inductor to ground."
        equations = [
            "H(f) = \\frac{j 2\\pi f L}{R + j 2\\pi f L}",
            "f_c = \\frac{R}{2\\pi L}",
            "I_{DC} = \\frac{V_{in}}{R}"
        ]
        components = [
            {"ref": "VIN", "type": "VOLTAGE_SOURCE", "value": ref_params["Vin"], "unit": "V", "nodes": ["in", "0"]},
            {"ref": "R1", "type": "RESISTOR", "value": ref_params["R"], "unit": "Ω", "nodes": ["in", "out"]},
            {"ref": "L1", "type": "INDUCTOR", "value": ref_params["L"], "unit": "H", "nodes": ["out", "0"]}
        ]
    elif circuit_type == "rlc_band_pass":
        ref_params = {
            "R": float(params.get("R", 1000.0)),
            "L": float(params.get("L", 0.01)),
            "C": float(params.get("C", 100e-9)),
            "Vin": float(params.get("Vin", 1.0))
        }
        description = "Second-order passive RLC band-pass filter with series resistor and parallel LC shunt resonator to ground."
        equations = [
            "f_0 = \\frac{1}{2\\pi \\sqrt{L C}}",
            "Q = R \\sqrt{\\frac{C}{L}}",
            "BW = \\frac{f_0}{Q} = \\frac{1}{2\\pi R C}",
            "I_{DC} = \\frac{V_{in}}{R}"
        ]
        components = [
            {"ref": "VIN", "type": "VOLTAGE_SOURCE", "value": ref_params["Vin"], "unit": "V", "nodes": ["in", "0"]},
            {"ref": "R1", "type": "RESISTOR", "value": ref_params["R"], "unit": "Ω", "nodes": ["in", "out"]},
            {"ref": "L1", "type": "INDUCTOR", "value": ref_params["L"], "unit": "H", "nodes": ["out", "0"]},
            {"ref": "C1", "type": "CAPACITOR", "value": ref_params["C"], "unit": "F", "nodes": ["out", "0"]}
        ]
    else:
        raise ValueError(f"Unknown circuit type: {circuit_type}")

    return {
        "circuit_type": circuit_type,
        "description": description,
        "parameters": ref_params,
        "equations": equations,
        "components": components
    }


def generate_corrected_circuit(
    circuit_type: str,
    original_params: Dict[str, float],
    top_fault: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates proposed corrected circuit:
    If a component was diagnosed with drift (+20%, -20%), open or short,
    restores it to the nominal reference value and highlights the diff.
    """
    reference = generate_reference_circuit(circuit_type, original_params)
    corrected_params = original_params.copy()
    changes = []

    if top_fault and top_fault.get("component") != "None":
        comp_name = top_fault["component"]
        mode = top_fault["mode"]

        # Restore component to reference nominal value
        nom_val = reference["parameters"].get(comp_name, original_params.get(comp_name, 1000.0))
        orig_val = original_params.get(comp_name, nom_val)
        corrected_params[comp_name] = nom_val

        changes.append({
            "component": comp_name,
            "detected_anomaly": f"{comp_name} was identified with {mode} fault",
            "original_value": orig_val,
            "corrected_value": nom_val,
            "rationale": f"Replace or repair {comp_name} to restore nominal design specification ({nom_val})."
        })

    return {
        "circuit_type": circuit_type,
        "original_parameters": original_params,
        "corrected_parameters": corrected_params,
        "changes": changes,
        "is_corrected": len(changes) > 0
    }


def generate_schematic_svg(
    circuit_type: str,
    params: Dict[str, float],
    highlight_comp: Optional[str] = None,
    color_scheme: str = "default"
) -> str:
    """
    Renders a clean, professional vector SVG schematic diagram
    matching IEEE standard electronic symbol conventions.
    """
    accent_color = "#1E40AF" if color_scheme == "default" else "#059669"
    warn_color = "#DC2626"

    # SVG Canvas dimensions
    w, h = 520, 280

    svg_header = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="240" '
        f'style="background-color: #FAFAFA; border: 1px solid #E2E8F0; border-radius: 6px;">\n'
        f'<defs>\n'
        f'  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">\n'
        f'    <circle cx="2" cy="2" r="1" fill="#CBD5E1" opacity="0.6"/>\n'
        f'  </pattern>\n'
        f'</defs>\n'
        f'<rect width="{w}" height="{h}" fill="url(#grid)" />\n'
    )

    content = ""

    if circuit_type == "voltage_divider":
        r1_val = params.get("R1", 10000.0)
        r2_val = params.get("R2", 10000.0)
        r1_color = warn_color if highlight_comp == "R1" else accent_color
        r2_color = warn_color if highlight_comp == "R2" else accent_color

        content = f"""
        <!-- Vin Terminal -->
        <circle cx="60" cy="80" r="4" fill="#0F172A" />
        <text x="50" y="65" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0F172A">Vin</text>
        <line x1="60" y1="80" x2="160" y2="80" stroke="#0F172A" stroke-width="2" />

        <!-- R1 Resistor (Zig-zag) -->
        <g stroke="{r1_color}" stroke-width="2.5" fill="none">
            <polyline points="160,80 170,70 180,90 190,70 200,90 210,70 220,90 230,80" />
        </g>
        <text x="180" y="55" font-family="sans-serif" font-size="12" font-weight="bold" fill="{r1_color}">R1</text>
        <text x="175" y="110" font-family="sans-serif" font-size="10" fill="#475569">{r1_val:g} Ω</text>

        <!-- Node out -->
        <line x1="230" y1="80" x2="360" y2="80" stroke="#0F172A" stroke-width="2" />
        <circle cx="300" cy="80" r="4" fill="#0F172A" />
        <circle cx="360" cy="80" r="4" fill="#0F172A" />
        <text x="370" y="85" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0F172A">Vout</text>

        <!-- Branch to R2 -->
        <line x1="300" y1="80" x2="300" y2="130" stroke="#0F172A" stroke-width="2" />
        <g stroke="{r2_color}" stroke-width="2.5" fill="none">
            <polyline points="300,130 290,140 310,150 290,160 310,170 290,180 310,190 300,200" />
        </g>
        <text x="325" y="165" font-family="sans-serif" font-size="12" font-weight="bold" fill="{r2_color}">R2</text>
        <text x="325" y="180" font-family="sans-serif" font-size="10" fill="#475569">{r2_val:g} Ω</text>

        <!-- Ground connection -->
        <line x1="300" y1="200" x2="300" y2="230" stroke="#0F172A" stroke-width="2" />
        <line x1="285" y1="230" x2="315" y2="230" stroke="#0F172A" stroke-width="2" />
        <line x1="290" y1="235" x2="310" y2="235" stroke="#0F172A" stroke-width="2" />
        <line x1="295" y1="240" x2="305" y2="240" stroke="#0F172A" stroke-width="2" />
        <text x="290" y="255" font-family="sans-serif" font-size="10" fill="#475569">GND</text>
        """

    elif circuit_type == "rc_low_pass":
        r_val = params.get("R", 1000.0)
        c_val = params.get("C", 100e-9)
        r_color = warn_color if highlight_comp in ["R", "R1"] else accent_color
        c_color = warn_color if highlight_comp in ["C", "C1"] else accent_color

        content = f"""
        <!-- Vin Terminal -->
        <circle cx="60" cy="80" r="4" fill="#0F172A" />
        <text x="50" y="65" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0F172A">Vin</text>
        <line x1="60" y1="80" x2="160" y2="80" stroke="#0F172A" stroke-width="2" />

        <!-- R Series Resistor -->
        <g stroke="{r_color}" stroke-width="2.5" fill="none">
            <polyline points="160,80 170,70 180,90 190,70 200,90 210,70 220,90 230,80" />
        </g>
        <text x="185" y="55" font-family="sans-serif" font-size="12" font-weight="bold" fill="{r_color}">R</text>
        <text x="175" y="110" font-family="sans-serif" font-size="10" fill="#475569">{r_val:g} Ω</text>

        <!-- Node Vout -->
        <line x1="230" y1="80" x2="360" y2="80" stroke="#0F172A" stroke-width="2" />
        <circle cx="300" cy="80" r="4" fill="#0F172A" />
        <circle cx="360" cy="80" r="4" fill="#0F172A" />
        <text x="370" y="85" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0F172A">Vout</text>

        <!-- Shunt Capacitor C -->
        <line x1="300" y1="80" x2="300" y2="140" stroke="#0F172A" stroke-width="2" />
        <line x1="285" y1="140" x2="315" y2="140" stroke="{c_color}" stroke-width="3" />
        <line x1="285" y1="150" x2="315" y2="150" stroke="{c_color}" stroke-width="3" />
        <line x1="300" y1="150" x2="300" y2="210" stroke="#0F172A" stroke-width="2" />
        <text x="325" y="145" font-family="sans-serif" font-size="12" font-weight="bold" fill="{c_color}">C</text>
        <text x="325" y="160" font-family="sans-serif" font-size="10" fill="#475569">{c_val*1e9:.1f} nF</text>

        <!-- Ground -->
        <line x1="285" y1="210" x2="315" y2="210" stroke="#0F172A" stroke-width="2" />
        <line x1="290" y1="215" x2="310" y2="215" stroke="#0F172A" stroke-width="2" />
        <line x1="295" y1="220" x2="305" y2="220" stroke="#0F172A" stroke-width="2" />
        <text x="290" y="235" font-family="sans-serif" font-size="10" fill="#475569">GND</text>
        """

    elif circuit_type == "rl_high_pass":
        r_val = params.get("R", 1000.0)
        l_val = params.get("L", 0.1)
        r_color = warn_color if highlight_comp in ["R", "R1"] else accent_color
        l_color = warn_color if highlight_comp in ["L", "L1"] else accent_color

        content = f"""
        <!-- Vin Terminal -->
        <circle cx="60" cy="80" r="4" fill="#0F172A" />
        <text x="50" y="65" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0F172A">Vin</text>
        <line x1="60" y1="80" x2="160" y2="80" stroke="#0F172A" stroke-width="2" />

        <!-- R Series Resistor -->
        <g stroke="{r_color}" stroke-width="2.5" fill="none">
            <polyline points="160,80 170,70 180,90 190,70 200,90 210,70 220,90 230,80" />
        </g>
        <text x="185" y="55" font-family="sans-serif" font-size="12" font-weight="bold" fill="{r_color}">R</text>
        <text x="175" y="110" font-family="sans-serif" font-size="10" fill="#475569">{r_val:g} Ω</text>

        <!-- Node Vout -->
        <line x1="230" y1="80" x2="360" y2="80" stroke="#0F172A" stroke-width="2" />
        <circle cx="300" cy="80" r="4" fill="#0F172A" />
        <circle cx="360" cy="80" r="4" fill="#0F172A" />
        <text x="370" y="85" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0F172A">Vout</text>

        <!-- Shunt Inductor L (Coil loops) -->
        <line x1="300" y1="80" x2="300" y2="120" stroke="#0F172A" stroke-width="2" />
        <g stroke="{l_color}" stroke-width="2" fill="none">
            <path d="M 300 120 A 10 10 0 0 1 300 140 A 10 10 0 0 1 300 160 A 10 10 0 0 1 300 180" />
        </g>
        <line x1="300" y1="180" x2="300" y2="210" stroke="#0F172A" stroke-width="2" />
        <text x="325" y="150" font-family="sans-serif" font-size="12" font-weight="bold" fill="{l_color}">L</text>
        <text x="325" y="165" font-family="sans-serif" font-size="10" fill="#475569">{l_val*1e3:.1f} mH</text>

        <!-- Ground -->
        <line x1="285" y1="210" x2="315" y2="210" stroke="#0F172A" stroke-width="2" />
        <line x1="290" y1="215" x2="310" y2="215" stroke="#0F172A" stroke-width="2" />
        <line x1="295" y1="220" x2="305" y2="220" stroke="#0F172A" stroke-width="2" />
        <text x="290" y="235" font-family="sans-serif" font-size="10" fill="#475569">GND</text>
        """

    elif circuit_type == "rlc_band_pass":
        r_val = params.get("R", 1000.0)
        l_val = params.get("L", 0.01)
        c_val = params.get("C", 25.33e-9)
        r_color = warn_color if highlight_comp in ["R", "R1"] else accent_color
        l_color = warn_color if highlight_comp in ["L", "L1"] else accent_color
        c_color = warn_color if highlight_comp in ["C", "C1"] else accent_color

        content = f"""
        <!-- Vin Terminal -->
        <circle cx="40" cy="70" r="4" fill="#0F172A" />
        <text x="30" y="55" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0F172A">Vin</text>
        <line x1="40" y1="70" x2="130" y2="70" stroke="#0F172A" stroke-width="2" />

        <!-- R Series Resistor -->
        <g stroke="{r_color}" stroke-width="2.5" fill="none">
            <polyline points="130,70 140,60 150,80 160,60 170,80 180,60 190,80 200,70" />
        </g>
        <text x="160" y="45" font-family="sans-serif" font-size="12" font-weight="bold" fill="{r_color}">R</text>
        <text x="145" y="100" font-family="sans-serif" font-size="10" fill="#475569">{r_val:g} Ω</text>

        <!-- Node Vout -->
        <line x1="200" y1="70" x2="420" y2="70" stroke="#0F172A" stroke-width="2" />
        <circle cx="280" cy="70" r="4" fill="#0F172A" />
        <circle cx="360" cy="70" r="4" fill="#0F172A" />
        <circle cx="420" cy="70" r="4" fill="#0F172A" />
        <text x="430" y="75" font-family="sans-serif" font-size="12" font-weight="bold" fill="#0F172A">Vout</text>

        <!-- Parallel L Branch -->
        <line x1="280" y1="70" x2="280" y2="120" stroke="#0F172A" stroke-width="2" />
        <g stroke="{l_color}" stroke-width="2" fill="none">
            <path d="M 280 120 A 10 10 0 0 1 280 140 A 10 10 0 0 1 280 160 A 10 10 0 0 1 280 180" />
        </g>
        <line x1="280" y1="180" x2="280" y2="210" stroke="#0F172A" stroke-width="2" />
        <text x="250" y="150" font-family="sans-serif" font-size="12" font-weight="bold" fill="{l_color}">L</text>
        <text x="230" y="165" font-family="sans-serif" font-size="10" fill="#475569">{l_val*1e3:.1f} mH</text>

        <!-- Parallel C Branch -->
        <line x1="360" y1="70" x2="360" y2="135" stroke="#0F172A" stroke-width="2" />
        <line x1="345" y1="135" x2="375" y2="135" stroke="{c_color}" stroke-width="3" />
        <line x1="345" y1="145" x2="375" y2="145" stroke="{c_color}" stroke-width="3" />
        <line x1="360" y1="145" x2="360" y2="210" stroke="#0F172A" stroke-width="2" />
        <text x="385" y="140" font-family="sans-serif" font-size="12" font-weight="bold" fill="{c_color}">C</text>
        <text x="385" y="155" font-family="sans-serif" font-size="10" fill="#475569">{c_val*1e9:.1f} nF</text>

        <!-- Common Ground Bus -->
        <line x1="280" y1="210" x2="360" y2="210" stroke="#0F172A" stroke-width="2" />
        <line x1="320" y1="210" x2="320" y2="230" stroke="#0F172A" stroke-width="2" />
        <line x1="305" y1="230" x2="335" y2="230" stroke="#0F172A" stroke-width="2" />
        <line x1="310" y1="235" x2="330" y2="235" stroke="#0F172A" stroke-width="2" />
        <line x1="315" y1="240" x2="325" y2="240" stroke="#0F172A" stroke-width="2" />
        <text x="310" y="255" font-family="sans-serif" font-size="10" fill="#475569">GND</text>
        """

    return svg_header + content + "\n</svg>"
