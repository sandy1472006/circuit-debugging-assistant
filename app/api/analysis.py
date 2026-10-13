"""
analysis.py - FastAPI endpoints for schematic upload, computer vision parsing,
Stage A->B->C analysis pipeline, and reference/corrected circuit generation.
"""

import os
import uuid
import time
import hashlib
from pathlib import Path
import numpy as np
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.config import UPLOAD_DIR, SAMPLE_DIR
from app.vision.inference import run_vision_inference
from app.core.circuit_models import get_model, FREQ_SWEEP_FINE
from app.core.fault_engine import FaultDiagnosisEngine
from app.core.netlist_parser import CircuitGraph, Component, validate_circuit_topology
from app.core.reference_generator import generate_reference_circuit, generate_corrected_circuit, generate_schematic_svg
from app.core.database import save_session, get_session

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

class AnalyzeRequest(BaseModel):
    session_id: Optional[str] = None
    circuit_type: str
    parameters: Dict[str, float]
    measurements: Optional[Dict[str, float]] = None
    use_multi_evidence: bool = True

@router.post("/upload")
async def upload_schematic(
    file: UploadFile = File(...),
    hint_circuit_type: Optional[str] = Form(None)
):
    """
    Stage A -> Stage B:
    Uploads an electronic schematic image (PNG, JPG, PDF), computes hash,
    runs the computer-vision extraction pipeline, and constructs editable representation.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".pdf"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file format {ext}. Allowed: PNG, JPG, JPEG, PDF.")

    session_id = f"ANALYSIS-{uuid.uuid4().hex[:8].upper()}"
    saved_filename = f"{session_id}_{file.filename}"
    saved_path = UPLOAD_DIR / saved_filename

    # Save uploaded file safely
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 20MB limit.")

    with open(saved_path, "wb") as f:
        f.write(content)

    checksum = hashlib.sha256(content).hexdigest()

    # Run CV extraction pipeline
    cv_result = run_vision_inference(saved_path, hint_circuit_type=hint_circuit_type)
    detected_type = cv_result["circuit_type"]
    extracted_params = cv_result["extracted_parameters"]

    # Reconstruct SVG preview
    reconstructed_svg = generate_schematic_svg(detected_type, extracted_params)

    # Initial session record
    session_data = {
        "id": session_id,
        "created_at": time.time(),
        "circuit_type": detected_type,
        "upload_filename": saved_filename,
        "file_checksum": checksum,
        "status": "interpreted",
        "parameters": extracted_params,
        "observations": {},
        "findings": [],
        "diagnosis": {},
        "report_pdf_path": None,
        "report_summary": "Schematic uploaded and interpreted."
    }
    save_session(session_data)

    return {
        "session_id": session_id,
        "filename": file.filename,
        "checksum": checksum,
        "image_url": f"/uploads/{saved_filename}",
        "circuit_type": detected_type,
        "classification_confidence": cv_result["classification_confidence"],
        "extracted_parameters": extracted_params,
        "symbols_detected": cv_result["symbols_detected"],
        "reconstructed_svg": reconstructed_svg,
        "spice_netlist": cv_result["spice_netlist"],
        "notes": cv_result["inference_notes"]
    }


@router.post("/run")
async def run_circuit_analysis(req: AnalyzeRequest):
    """
    Stage B -> Stage C:
    Runs full electrical simulation, topology validation, residual fault diagnosis,
    reference & corrected circuit synthesis, and adaptive test selection.
    """
    session_id = req.session_id or f"ANALYSIS-{uuid.uuid4().hex[:8].upper()}"
    circuit_type = req.circuit_type
    params = req.parameters
    measurements = req.measurements or {}
    use_multi_evidence = req.use_multi_evidence

    # 1. Instantiate analytical model with nominal reference parameters
    reference_circ = generate_reference_circuit(circuit_type)
    nominal_ref_params = reference_circ["parameters"]
    model = get_model(circuit_type, nominal_ref_params)

    # 2. Reconstruct graph and validate topology
    graph = CircuitGraph("DUT Analysis Graph")
    for k, v in params.items():
        if k == "Vin":
            graph.add_component(Component("VIN", "VOLTAGE_SOURCE", v, "V", ["in", "0"]))
        elif k.startswith("R"):
            nodes = ["in", "out"] if (k in ["R", "R1"]) else ["out", "0"]
            graph.add_component(Component(k, "RESISTOR", v, "Ω", nodes))
        elif k.startswith("C"):
            graph.add_component(Component("C1", "CAPACITOR", v, "F", ["out", "0"]))
        elif k.startswith("L"):
            graph.add_component(Component("L1", "INDUCTOR", v, "H", ["out", "0"]))

    findings = validate_circuit_topology(graph, circuit_type=circuit_type)

    # 3. Simulate nominal vs observed curves
    freqs = FREQ_SWEEP_FINE
    mag_nominal_db, phase_nominal_deg = model.get_frequency_response(model.nominal_params, freqs)
    mag_actual_db, phase_actual_deg = model.get_frequency_response(params, freqs)

    time_pts = np.linspace(0, 0.005, 200)
    step_nom = model.get_step_response(model.nominal_params, time_pts)
    step_act = model.get_step_response(params, time_pts)

    # 4. Fault Diagnosis & Residual Scoring
    engine = FaultDiagnosisEngine(model)
    # Observed feature vector: if measurements provided, use them; otherwise use simulated actual params
    obs_vector = model.get_features(params, use_independent=use_multi_evidence)

    ranked_candidates = engine.score_observations(obs_vector, use_independent=use_multi_evidence)
    top_cand = ranked_candidates[0] if ranked_candidates else None

    # Adaptive test recommendation (Value of Information U(t))
    adaptive_test = engine.recommend_adaptive_test(ranked_candidates, top_k=5)

    # 5. Reference & Corrected Circuit Generation (Panels 3 & 4)
    reference_circ = generate_reference_circuit(circuit_type, model.nominal_params)
    corrected_circ = generate_corrected_circuit(circuit_type, params, top_fault=top_cand)

    # Generate SVGs for all panels
    reconstructed_svg = generate_schematic_svg(circuit_type, params)
    reference_svg = generate_schematic_svg(circuit_type, reference_circ["parameters"], color_scheme="reference")
    corrected_svg = generate_schematic_svg(
        circuit_type,
        corrected_circ["corrected_parameters"],
        highlight_comp=top_cand.get("component") if top_cand else None,
        color_scheme="corrected"
    )

    # Update database session
    diagnosis_payload = {
        "top_candidate": top_cand,
        "ranked_candidates": ranked_candidates,
        "adaptive_recommendation": adaptive_test,
        "use_multi_evidence": use_multi_evidence
    }

    existing = get_session(session_id) or {}
    upload_fn = existing.get("upload_filename", "")
    if not upload_fn or not (UPLOAD_DIR / upload_fn).exists():
        for cand in UPLOAD_DIR.glob(f"{session_id}_*"):
            upload_fn = cand.name
            break

    session_data = {
        "id": session_id,
        "created_at": time.time(),
        "circuit_type": circuit_type,
        "upload_filename": upload_fn,
        "file_checksum": existing.get("file_checksum", ""),
        "status": "analyzed",
        "parameters": params,
        "observations": measurements,
        "findings": findings,
        "diagnosis": diagnosis_payload,
        "report_pdf_path": None,
        "report_summary": f"Diagnosed {top_cand.get('label') if top_cand else 'Nominal'}"
    }
    save_session(session_data)

    return {
        "session_id": session_id,
        "circuit_type": circuit_type,
        "findings": findings,
        "simulation": {
            "frequencies": freqs.tolist(),
            "mag_nominal_db": mag_nominal_db.tolist(),
            "phase_nominal_deg": phase_nominal_deg.tolist(),
            "mag_actual_db": mag_actual_db.tolist(),
            "phase_actual_deg": phase_actual_deg.tolist(),
            "time_points": (time_pts * 1e3).tolist(), # ms
            "step_nominal": step_nom.tolist(),
            "step_actual": step_act.tolist()
        },
        "diagnosis": diagnosis_payload,
        "panels": {
            "reconstructed_svg": reconstructed_svg,
            "reference_svg": reference_svg,
            "corrected_svg": corrected_svg,
            "reference_image_url": f"/references/ref_{circuit_type}.png",
            "reference_info": reference_circ,
            "corrected_info": corrected_circ
        },
        "spice_netlist": graph.to_spice_netlist()
    }


@router.get("/samples")
async def get_sample_schematics():
    """Returns available sample circuit schematics for 1-click loading."""
    samples = [
        {
            "id": "voltage_divider",
            "name": "Resistive Voltage Divider (R1=10k, R2=10k, Vin=10V)",
            "type": "voltage_divider",
            "filename": "sample_voltage_divider.png",
            "url": "/samples/sample_voltage_divider.png",
            "default_params": {"R1": 10000.0, "R2": 10000.0, "Vin": 10.0}
        },
        {
            "id": "rc_low_pass",
            "name": "RC Low-Pass Filter (R=1k, C=100nF, fc≈1.59kHz)",
            "type": "rc_low_pass",
            "filename": "sample_rc_low_pass.png",
            "url": "/samples/sample_rc_low_pass.png",
            "default_params": {"R": 1000.0, "C": 100e-9, "Vin": 1.0}
        },
        {
            "id": "rc_10k_100nf",
            "name": "RC Low-Pass Filter (R=10k, C=100nF, fc≈159.15Hz)",
            "type": "rc_low_pass",
            "filename": "sample_rc_10k_100nf.png",
            "url": "/samples/sample_rc_10k_100nf.png",
            "default_params": {"R": 10000.0, "C": 100e-9, "Vin": 1.0}
        },
        {
            "id": "rl_high_pass",
            "name": "RL High-Pass Filter (R=1k, L=100mH, fc≈1.59kHz)",
            "type": "rl_high_pass",
            "filename": "sample_rl_high_pass.png",
            "url": "/samples/sample_rl_high_pass.png",
            "default_params": {"R": 1000.0, "L": 0.1, "Vin": 1.0}
        },
        {
            "id": "rlc_band_pass",
            "name": "RLC Band-Pass Filter (R=1k, L=10mH, C=25.33nF, f0≈10kHz)",
            "type": "rlc_band_pass",
            "filename": "sample_rlc_band_pass.png",
            "url": "/samples/sample_rlc_band_pass.png",
            "default_params": {"R": 1000.0, "L": 0.01, "C": 25.33e-9, "Vin": 1.0}
        },
        {
            "id": "rc_drift_120nf",
            "name": "[FAULT CASE] RC Low-Pass with C = 120nF (+20% Drift - Paper Section V.A)",
            "type": "rc_low_pass",
            "filename": "test_rc_drift_120nf.png",
            "url": "/samples/test_rc_drift_120nf.png",
            "default_params": {"R": 1000.0, "C": 120e-9, "Vin": 1.0}
        },
        {
            "id": "missing_ground",
            "name": "[TOPOLOGY ERROR] Voltage Divider with Missing Ground Reference",
            "type": "voltage_divider",
            "filename": "test_missing_ground.png",
            "url": "/samples/test_missing_ground.png",
            "default_params": {"R1": 10000.0, "R2": 10000.0, "Vin": 10.0}
        },
        {
            "id": "shorted_component",
            "name": "[TOPOLOGY ERROR] Voltage Divider with R1 Shorted by Bypass Wire",
            "type": "voltage_divider",
            "filename": "test_shorted_component.png",
            "url": "/samples/test_shorted_component.png",
            "default_params": {"R1": 1e-4, "R2": 10000.0, "Vin": 10.0}
        },
        {
            "id": "dangling_wire",
            "name": "[TOPOLOGY ERROR] RC Filter with Dangling / Floating Wire Endpoint",
            "type": "rc_low_pass",
            "filename": "test_dangling_wire.png",
            "url": "/samples/test_dangling_wire.png",
            "default_params": {"R": 1000.0, "C": 100e-9, "Vin": 1.0}
        }
    ]
    return samples
