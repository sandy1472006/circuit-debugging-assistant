"""
test_vision_pipeline.py - Unit test verifying schematic preprocessing, symbol detection,
and graph reconstruction pipeline.
"""

import pytest
from pathlib import Path
from app.config import SAMPLE_DIR
from app.vision.inference import run_vision_inference

def test_vision_pipeline_on_sample_rc():
    rc_sample = SAMPLE_DIR / "sample_rc_low_pass.png"
    if not rc_sample.exists():
        pytest.skip("Sample RC image not yet generated.")

    result = run_vision_inference(rc_sample, hint_circuit_type="rc_low_pass")

    assert result["circuit_type"] == "rc_low_pass"
    assert result["classification_confidence"] >= 0.80
    assert "graph" in result
    assert "spice_netlist" in result
    assert "extracted_parameters" in result
    assert "R" in result["extracted_parameters"]
    assert "C" in result["extracted_parameters"]
