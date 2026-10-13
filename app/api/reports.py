"""
reports.py - PDF report generation, SPICE netlist export, and simulation data CSV download.
"""

from pathlib import Path
import io
import csv
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from app.config import REPORT_DIR
from app.core.database import get_session
from app.reports.pdf_generator import build_pdf_report
from app.core.circuit_models import get_model, FREQ_SWEEP_FINE
import numpy as np

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/{session_id}/pdf")
async def download_pdf_report(session_id: str):
    """Generates and serves the full 24-section scientific PDF report."""
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Analysis session not found.")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"{session_id}_Diagnostic_Report.pdf"
    pdf_path = REPORT_DIR / pdf_filename

    # Build report using ReportLab
    plot_temp_dir = REPORT_DIR / "plots"
    build_pdf_report(session_data, pdf_path, plot_temp_dir)

    return FileResponse(
        path=str(pdf_path),
        filename=pdf_filename,
        media_type="application/pdf"
    )


@router.get("/{session_id}/spice")
async def download_spice_netlist(session_id: str):
    """Exports SPICE netlist file (.cir)."""
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Analysis session not found.")

    circuit_type = session_data.get("circuit_type", "voltage_divider")
    params = session_data.get("parameters", {})
    model = get_model(circuit_type, params)
    netlist = model.generate_spice_netlist(params)

    return Response(
        content=netlist,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={session_id}_netlist.cir"}
    )


@router.get("/{session_id}/csv")
async def download_simulation_csv(session_id: str):
    """Exports scientific simulation frequency and step data as CSV."""
    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Analysis session not found.")

    circuit_type = session_data.get("circuit_type", "voltage_divider")
    params = session_data.get("parameters", {})
    model = get_model(circuit_type, params)

    freqs = FREQ_SWEEP_FINE
    mag_db, phase_deg = model.get_frequency_response(params, freqs)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Frequency_Hz", "Magnitude_dB", "Phase_deg"])
    for f, m, p in zip(freqs, mag_db, phase_deg):
        writer.writerow([f"{f:.4f}", f"{m:.4f}", f"{p:.4f}"])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={session_id}_simulation_data.csv"}
    )
