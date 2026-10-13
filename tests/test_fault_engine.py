"""
test_fault_engine.py - Unit tests for the deterministic fault diagnosis engine,
residual calculations, multi-evidence fusion, and adaptive test selection.
"""

import pytest
import numpy as np
from app.core.circuit_models import get_model
from app.core.fault_engine import FaultDiagnosisEngine, get_fault_param_value

def test_fault_dictionary_generation():
    model = get_model("rc_low_pass")
    engine = FaultDiagnosisEngine(model)
    # R (4 faults) + C (4 faults) + Nominal (1) = 9 candidates
    assert len(engine.candidates) == 9

    dictionary = engine.generate_fault_dictionary(use_independent=True)
    assert len(dictionary) == 9
    assert "Nominal (Fault-Free)" in dictionary
    assert "C +20%" in dictionary
    assert "R -20%" in dictionary

def test_residual_fault_scoring():
    model = get_model("rc_low_pass")
    engine = FaultDiagnosisEngine(model)

    # Injected fault: C +20%
    faulty_params = model.nominal_params.copy()
    faulty_params["C"] = 120e-9 # 120 nF
    observed_x = model.get_features(faulty_params, use_independent=True)

    ranked = engine.score_observations(observed_x, use_independent=True)
    top_candidate = ranked[0]

    # Top candidate should be precisely "C +20%" with near-zero residual score
    assert top_candidate["label"] == "C +20%"
    assert top_candidate["residual_score"] < 1e-4

def test_adaptive_test_recommendation():
    model = get_model("rc_low_pass")
    engine = FaultDiagnosisEngine(model)

    faulty_params = model.nominal_params.copy()
    faulty_params["C"] = 120e-9
    observed_x = model.get_features(faulty_params, use_independent=True)

    ranked = engine.score_observations(observed_x, use_independent=True)
    rec = engine.recommend_adaptive_test(ranked, top_k=5)

    assert "current_entropy" in rec
    assert "recommended_test" in rec
    assert rec["recommended_test"]["utility_score"] > 0
