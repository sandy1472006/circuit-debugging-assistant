"""
test_circuits.py - Unit tests for the 4 analytical circuit models:
Voltage Divider, RC Low-pass, RL High-pass, RLC Band-pass.
"""

import pytest
import numpy as np
from app.core.circuit_models import get_model, FREQ_5_POINTS, FREQ_6_POINTS

def test_voltage_divider():
    model = get_model("voltage_divider", {"R1": 10000.0, "R2": 10000.0, "Vin": 10.0})
    v_out, i_supply = model.compute_dc(model.nominal_params)
    assert pytest.approx(v_out, rel=1e-3) == 5.0
    assert pytest.approx(i_supply, rel=1e-3) == 0.0005 # 0.5 mA

    # Test short fault on R1: Vout should be Vin
    fault_params = {"R1": 1e-4, "R2": 10000.0, "Vin": 10.0}
    v_short, _ = model.compute_dc(fault_params)
    assert pytest.approx(v_short, rel=1e-2) == 10.0


def test_rc_low_pass():
    # R = 1k, C = 100nF -> fc ≈ 1591.55 Hz
    model = get_model("rc_low_pass", {"R": 1000.0, "C": 100e-9, "Vin": 1.0})
    fc = model.cutoff_frequency(model.nominal_params)
    assert pytest.approx(fc, rel=1e-3) == 1591.55

    # At fc, magnitude should be 1/sqrt(2) ≈ 0.707 (-3.01 dB)
    mag_db, phase_deg = model.get_frequency_response(model.nominal_params, np.array([fc]))
    assert pytest.approx(mag_db[0], abs=0.1) == -3.01
    assert pytest.approx(phase_deg[0], abs=0.5) == -45.0

    # Independent feature: step current at t=0+ = Vin / R = 1.0 / 1000 = 1 mA
    feats = model.get_features(model.nominal_params, use_independent=True)
    i_step = feats[-1]
    assert pytest.approx(i_step, rel=1e-3) == 0.001


def test_rl_high_pass():
    # R = 1k, L = 100mH -> fc = R / (2*pi*L) ≈ 1591.55 Hz
    model = get_model("rl_high_pass", {"R": 1000.0, "L": 0.1, "Vin": 1.0})
    fc = model.cutoff_frequency(model.nominal_params)
    assert pytest.approx(fc, rel=1e-3) == 1591.55

    # At fc, magnitude should be -3.01 dB, phase +45 deg
    mag_db, phase_deg = model.get_frequency_response(model.nominal_params, np.array([fc]))
    assert pytest.approx(mag_db[0], abs=0.1) == -3.01
    assert pytest.approx(phase_deg[0], abs=0.5) == 45.0

    # Independent feature: DC current = Vin / R = 1 mA
    feats = model.get_features(model.nominal_params, use_independent=True)
    i_dc = feats[-1]
    assert pytest.approx(i_dc, rel=1e-3) == 0.001


def test_rlc_band_pass():
    # R = 1k, L = 10mH, C = 25.33nF -> f0 ≈ 10 kHz
    model = get_model("rlc_band_pass", {"R": 1000.0, "L": 0.01, "C": 25.33e-9, "Vin": 1.0})
    f0, q, bw = model.resonance_parameters(model.nominal_params)
    assert pytest.approx(f0, rel=1e-2) == 10000.0

    # At resonance, H(f0) should be approx 1.0 (0 dB, 0 deg)
    mag_db, phase_deg = model.get_frequency_response(model.nominal_params, np.array([f0]))
    assert pytest.approx(mag_db[0], abs=0.2) == 0.0
    assert pytest.approx(phase_deg[0], abs=2.0) == 0.0
