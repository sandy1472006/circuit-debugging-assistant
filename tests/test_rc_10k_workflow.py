"""
test_rc_10k_workflow.py - End-to-end test verifying the specific RC low-pass workflow
required in Part 9:
- Uses R = 10 kΩ and C = 100 nF.
- Confirms theoretical cutoff frequency is ~159.15 Hz.
- Verifies circuit is NOT classified as RLC or assigned a non-existent inductor.
- Verifies 1-to-2 page PDF generation and component consistency.
"""

import pytest
import re
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.config import SAMPLE_DIR
from app.core.circuit_models import get_model

client = TestClient(app)

def test_rc_10k_cutoff_calculation():
    # Mathematical check: fc = 1 / (2*pi*R*C)
    model = get_model("rc_low_pass", {"R": 10000.0, "C": 100e-9, "Vin": 1.0})
    fc = model.cutoff_frequency({"R": 10000.0, "C": 100e-9})
    assert pytest.approx(fc, abs=0.1) == 159.15
    print(f"\n[PASS] Calculated Cutoff Frequency = {fc:.2f} Hz (Expected ~159.15 Hz)")

def test_rc_10k_complete_workflow(tmp_path):
    img_path = SAMPLE_DIR / "sample_rc_10k_100nf.png"
    assert img_path.exists(), "Test image sample_rc_10k_100nf.png must exist"

    # 1. Upload schematic
    with open(img_path, "rb") as f:
        res = client.post(
            "/api/analysis/upload",
            files={"file": ("sample_rc_10k_100nf.png", f, "image/png")}
        )
    assert res.status_code == 200
    upload_data = res.json()
    session_id = upload_data["session_id"]
    circuit_type = upload_data["circuit_type"]

    # Verify NOT classified as RLC and NO inductor
    assert circuit_type == "rc_low_pass", f"Expected 'rc_low_pass', got '{circuit_type}'"
    assert "L" not in upload_data["extracted_parameters"], "Circuit must not be assigned a non-existent inductor!"
    print(f"[PASS] Circuit classified strictly as '{circuit_type}', no inductor assigned.")

    # 2. Confirm extracted values: R = 10000, C = 100e-9
    params = upload_data["extracted_parameters"]
    assert pytest.approx(params["R"], rel=1e-2) == 10000.0
    assert pytest.approx(params["C"], rel=1e-2) == 100e-9

    # 3. Run Analysis
    run_res = client.post(
        "/api/analysis/run",
        json={
            "session_id": session_id,
            "circuit_type": "rc_low_pass",
            "parameters": {"R": 10000.0, "C": 100e-9, "Vin": 1.0},
            "use_multi_evidence": True
        }
    )
    assert run_res.status_code == 200
    analysis_data = run_res.json()

    # 4. View original and reference circuit panels
    assert "panels" in analysis_data
    assert "reference_svg" in analysis_data["panels"]
    assert "reconstructed_svg" in analysis_data["panels"]
    print("[PASS] Both original/reconstructed and reference circuit diagrams generated.")

    # 5. Review findings
    findings = analysis_data["findings"]
    # For a clean RC filter with R=10k, C=100nF and ground, findings should have 0 topology violations
    critical_findings = [f for f in findings if f.get("severity") == "Critical"]
    assert len(critical_findings) == 0

    # 6 & 7. Generate & Download PDF
    pdf_res = client.get(f"/api/reports/{session_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    pdf_bytes = pdf_res.content

    # 8. Confirm PDF length is strictly 1 or 2 pages maximum!
    page_count = len(re.findall(rb'/Type\s*/Page[^s]', pdf_bytes))
    assert 1 <= page_count <= 2, f"PDF report must be 1 to 2 pages maximum, got {page_count} pages!"
    print(f"[PASS] Diagnostic Report generated: exactly {page_count} page(s) ({len(pdf_bytes):,} bytes).")
