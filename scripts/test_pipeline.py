"""
test_pipeline.py - End-to-end integration test verifying the FastAPI endpoints:
1. Upload & interpretation
2. Electrical analysis & fault diagnosis
3. PDF report download
4. Evidence-grounded AI assistant response
5. Benchmark runner
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.config import SAMPLE_DIR

def run_integration_pipeline():
    client = TestClient(app)
    print("Testing End-to-End Pipeline on Circuit Debugging Assistant...")

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    print("[PASS] Health Check")

    # 2. Get samples
    res = client.get("/api/analysis/samples")
    assert res.status_code == 200
    samples = res.json()
    assert len(samples) >= 4
    print(f"[PASS] Sample Schematics ({len(samples)} archetypes available)")

    # 3. Upload a sample schematic (Stage A -> Stage B)
    rc_sample_path = SAMPLE_DIR / "sample_rc_low_pass.png"
    with open(rc_sample_path, "rb") as f:
        res = client.post(
            "/api/analysis/upload",
            files={"file": ("sample_rc_low_pass.png", f, "image/png")},
            data={"hint_circuit_type": "rc_low_pass"}
        )
    assert res.status_code == 200
    upload_data = res.json()
    session_id = upload_data["session_id"]
    print(f"[PASS] Upload & CV Interpretation (Session: {session_id}, Type: {upload_data['circuit_type']})")

    # 4. Run Analysis (Stage B -> Stage C) with injected +20% C fault
    analysis_payload = {
        "session_id": session_id,
        "circuit_type": "rc_low_pass",
        "parameters": {"R": 1000.0, "C": 120e-9, "Vin": 1.0},
        "use_multi_evidence": True
    }
    res = client.post("/api/analysis/run", json=analysis_payload)
    assert res.status_code == 200
    analysis_data = res.json()
    top_cand = analysis_data["diagnosis"]["top_candidate"]
    assert top_cand["label"] == "C +20%"
    print(f"[PASS] Stage C Analysis & Fault Localization: Top Candidate = '{top_cand['label']}' (Score: {top_cand['residual_score']:.4f})")

    # 5. Download 24-section PDF Report
    res = client.get(f"/api/reports/{session_id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) > 5000
    print(f"[PASS] Publication PDF Report Generated ({len(res.content):,} bytes)")

    # 6. SPICE netlist export
    res = client.get(f"/api/reports/{session_id}/spice")
    assert res.status_code == 200
    assert "* SPICE Netlist" in res.text
    print("[PASS] SPICE Netlist (.cir) Exported")

    # 7. CSV data export
    res = client.get(f"/api/reports/{session_id}/csv")
    assert res.status_code == 200
    assert "Frequency_Hz" in res.text
    print("[PASS] Simulation Data CSV Exported")

    # 8. AI Grounded Explanation Assistant
    chat_payload = {
        "session_id": session_id,
        "query": "What measurement would best distinguish the top candidates?"
    }
    res = client.post("/api/assistant/query", json=chat_payload)
    assert res.status_code == 200
    reply = res.json()
    assert "U(t)" in reply["response"] or "test" in reply["response"].lower()
    print(f"[PASS] Grounded AI Explanation Assistant: {reply['response'][:80]}...")

    # 9. Benchmark API
    res = client.get("/api/benchmarks/run?trials=5")
    assert res.status_code == 200
    bench_data = res.json()
    assert bench_data["status"] == "completed"
    print(f"[PASS] Live Benchmark Evaluated ({bench_data['total_instances_evaluated']} instances)")

    print("\nALL INTEGRATION TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_integration_pipeline()
