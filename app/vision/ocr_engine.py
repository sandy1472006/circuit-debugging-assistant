"""
ocr_engine.py - Electronic engineering label and unit parser.
Parses component reference designators (R1, C1, L1) and values (10k, 100nF, 10mH, 10V).
"""

import re
from typing import Dict, Tuple, Optional, Any

SI_MULTIPLIERS = {
    'p': 1e-12, 'P': 1e-12, # pico
    'n': 1e-9,  'N': 1e-9,  # nano
    'u': 1e-6,  'U': 1e-6,  'µ': 1e-6, # micro
    'm': 1e-3,  'M': 1e-3,  # milli (unless followed by Hz or ohm context)
    'k': 1e3,   'K': 1e3,   # kilo
    'meg': 1e6, 'MEG': 1e6, 'g': 1e9, 'G': 1e9 # mega, giga
}

VALUE_PATTERN = re.compile(
    r'([0-9]+(?:\.[0-9]+)?)\s*([pnumkMµ]|meg|MEG)?\s*(Ω|ohm|ohms|F|f|H|h|V|v|Hz|hz)?',
    re.IGNORECASE
)

REF_PATTERN = re.compile(
    r'\b([RCLVDQI]|VIN|VOUT|GND)\s*([0-9]*)\b',
    re.IGNORECASE
)

def parse_engineering_value(text: str) -> Optional[Tuple[float, str]]:
    """
    Parses a string like '10k', '4.7kΩ', '100nF', '0.1uF', '10mH', '10V'.
    Returns (normalized_float_val, unit_string) or None.
    """
    if not text:
        return None
    cleaned = text.strip().replace(" ", "")

    # Check for direct decimal value
    match = VALUE_PATTERN.search(cleaned)
    if not match:
        return None

    num_str, mult_str, unit_str = match.groups()
    try:
        val = float(num_str)
    except ValueError:
        return None

    mult = 1.0
    if mult_str:
        mult = SI_MULTIPLIERS.get(mult_str.lower(), 1.0)
        # Note: if someone writes '1M' for resistor, in electronics it usually means Megohm
        if mult_str == 'M' and (unit_str in ['Ω', 'ohm', None]):
            mult = 1e6

    normalized_val = val * mult
    detected_unit = unit_str if unit_str else ("Ω" if mult_str in ['k', 'meg'] else "")
    return normalized_val, detected_unit


def extract_component_annotation(text: str) -> Dict[str, Any]:
    """
    Extracts both reference designator and value from a schematic text label.
    Example: 'R1 10k', 'C1 100nF', 'VIN 10V'
    """
    ref_match = REF_PATTERN.search(text)
    val_parsed = parse_engineering_value(text)

    ref = ref_match.group(0).upper() if ref_match else "UNKNOWN"
    val = val_parsed[0] if val_parsed else 1000.0
    unit = val_parsed[1] if val_parsed else "Ω"

    return {
        "raw_text": text,
        "ref": ref,
        "value": val,
        "unit": unit,
        "confidence": 0.95 if (ref_match and val_parsed) else 0.70
    }
