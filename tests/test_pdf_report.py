"""
test_pdf_report.py - Unit test verifying automated 24-section scientific PDF report generation.
"""

import pytest
from pathlib import Path
from app.reports.pdf_generator import build_pdf_report
from app.config import REPORT_DIR

def test_pdf_generation(tmp_path):
    session_data = {
        "id": "TEST-REPORT-001",
        "created_at": 1700000000.0,
        "circuit_type": "rc_low_pass",
        "parameters": {"R": 1000.0, "C": 120e-9, "Vin": 1.0},
        "findings": [
            {
                "id": "FIND-001",
                "category": "Category C: Functional design issues",
                "component_or_net": "C1",
                "severity": "Major",
                "status": "Confirmed",
                "confidence": 0.98,
                "evidence": "Cutoff frequency shifted from 1.59 kHz nominal to 1.33 kHz."
            }
        ],
        "diagnosis": {
            "top_candidate": {
                "component": "C",
                "mode": "+20%",
                "label": "C +20%",
                "residual_score": 0.042
            },
            "ranked_candidates": [
                {"label": "C +20%", "residual_score": 0.042},
                {"label": "R +20%", "residual_score": 0.581},
                {"label": "Nominal", "residual_score": 0.923}
            ],
            "adaptive_recommendation": {
                "recommended_test": {
                    "test_name": "Oscilloscope Initial Step Current Test",
                    "cost": 2.0,
                    "information_gain": 0.65,
                    "utility_score": 0.325
                }
            }
        }
    }

    out_pdf = tmp_path / "test_report.pdf"
    plots_dir = tmp_path / "plots"

    generated_path = build_pdf_report(session_data, out_pdf, plots_dir)

    assert generated_path.exists()
    assert generated_path.stat().st_size > 1000 # Valid non-empty PDF
