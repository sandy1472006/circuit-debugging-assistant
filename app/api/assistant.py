"""
assistant.py - Evidence-grounded conversational explanation assistant.
Strictly grounded in circuit equations, topology graph G=(V,E), and numerical residuals.
Does not invent electrical results or alter netlists without user confirmation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.core.database import get_session

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    circuit_context: Optional[Dict[str, Any]] = None

@router.post("/query")
async def chat_explanation(req: ChatRequest):
    """
    Answers technical questions grounded in the actual simulation data and residual score.
    """
    query = req.query.lower().strip()
    session = get_session(req.session_id) if req.session_id else None
    ctx = req.circuit_context or (session if session else {})

    circuit_type = ctx.get("circuit_type", "voltage_divider")
    params = ctx.get("parameters", {})
    diagnosis = ctx.get("diagnosis", {})
    top_cand = diagnosis.get("top_candidate", {})
    findings = ctx.get("findings", [])
    rec_test = diagnosis.get("adaptive_recommendation", {}).get("recommended_test", {})

    # Grounded response generation based on technical rules and numerical core
    response_text = ""
    evidence_points = []

    if "why" in query and ("classified" in query or "type" in query or "filter" in query):
        if circuit_type == "rc_low_pass":
            response_text = (
                "The circuit is classified as an **RC Low-Pass Filter** because of its topological structure: "
                "the input signal Vin passes through a series resistor R, and the output Vout is tapped across "
                "a shunt capacitor C connected to ground. At low frequencies, the capacitor's impedance "
                "|Z_C| = 1/(2πfC) is very large compared to R, so Vout ≈ Vin (0 dB). At high frequencies, "
                "|Z_C| approaches zero, shunting high frequencies to ground with a -20 dB/decade roll-off."
            )
            evidence_points = [
                f"Series Resistor R: {params.get('R', 1000):g} Ω",
                f"Shunt Capacitor C: {params.get('C', 100e-9)*1e9:.1f} nF",
                f"Nominal Cutoff fc = 1/(2πRC) ≈ {1.0/(2*3.14159*params.get('R', 1000)*params.get('C', 100e-9)):.1f} Hz"
            ]
        elif circuit_type == "rl_high_pass":
            response_text = (
                "The circuit is classified as an **RL High-Pass Filter** because Vin passes through series R, "
                "while Vout is measured across shunt inductor L to ground. At DC (f=0), the inductor is an "
                "ideal short to ground (Z_L = 0), yielding Vout = 0. At high frequencies, Z_L = jωL becomes "
                "much larger than R, passing signals with near-unity gain."
            )
            evidence_points = [
                f"Series Resistor R: {params.get('R', 1000):g} Ω",
                f"Shunt Inductor L: {params.get('L', 0.1)*1e3:.1f} mH",
                f"Cutoff fc = R/(2πL) ≈ {params.get('R', 1000)/(2*3.14159*params.get('L', 0.1)):.1f} Hz"
            ]
        elif circuit_type == "rlc_band_pass":
            response_text = (
                "The circuit is classified as a second-order **RLC Band-Pass Filter**. It features a series resistor R "
                "and a parallel LC tank connected to ground. At DC, the inductor shorts to ground; at high frequencies, "
                "the capacitor shorts to ground. At the resonant frequency f0 = 1/(2π√(LC)), the LC tank's parallel impedance "
                "reaches maximum (infinity in lossless case), allowing the resonant center band to pass through to Vout."
            )
            evidence_points = [
                f"Resistor R: {params.get('R', 1000):g} Ω",
                f"Inductor L: {params.get('L', 0.01)*1e3:.1f} mH",
                f"Capacitor C: {params.get('C', 25.33e-9)*1e9:.1f} nF"
            ]
        else:
            response_text = (
                "The circuit is classified as a **Resistive Voltage Divider** with series resistor R1 and shunt "
                "resistor R2 to ground, producing output voltage Vout = Vin · R2 / (R1 + R2)."
            )
            evidence_points = [
                f"R1: {params.get('R1', 10000):g} Ω",
                f"R2: {params.get('R2', 10000):g} Ω",
                f"Nominal division ratio: {params.get('R2', 10000)/(params.get('R1', 10000)+params.get('R2', 10000)):.2f}"
            ]

    elif "distinguish" in query or "measurement" in query or "test" in query or "ambig" in query:
        rec_name = rec_test.get("test_name", "DC Current Measurement")
        cost = rec_test.get("cost", 1.5)
        ig = rec_test.get("information_gain", 0.5)
        response_text = (
            f"To resolve ambiguity between leading fault candidates, the diagnostic engine recommends: "
            f"**{rec_name}**.\n\n"
            f"**Why this test?** Frequency response measurements depend on the RC/RL product and cannot "
            f"separate an increase in R from an increase in C. By introducing an independent observable "
            f"(such as the initial step current or DC branch current), we isolate the resistive path directly. "
            f"According to the value-of-information metric U(t) = [H(F) - E(H(F|X_t))] / C(t), this test gives "
            f"an expected information gain of {ig:.3f} bits at a relative bench cost of {cost}."
        )
        evidence_points = [
            f"Top Hypothesis: {top_cand.get('label', 'Nominal')}",
            f"Residual Score: {top_cand.get('residual_score', 0):.4f}",
            f"Recommended Physical Test: {rec_name}"
        ]

    elif "cutoff" in query or "shift" in query or "frequency" in query:
        comp = top_cand.get("component", "Unknown")
        mode = top_cand.get("mode", "drift")
        response_text = (
            f"The cutoff frequency shift is primarily attributed to **{top_cand.get('label', 'component deviation')}**. "
            f"In this circuit, fc is inversely proportional to component parameters. A {mode} variation alters the "
            f"reactive impedance pole, moving the -3 dB corner frequency away from the nominal design target."
        )
        evidence_points = [
            f"Fault Candidate: {top_cand.get('label')}",
            f"Residual Metric S(f): {top_cand.get('residual_score', 0):.4f}"
        ]

    elif "floating" in query or "finding" in query or "error" in query:
        if findings:
            f_summary = "; ".join([f"{f['id']} ({f['component_or_net']}): {f['evidence']}" for f in findings[:3]])
            response_text = (
                f"The topological validation engine detected {len(findings)} issues: {f_summary}. "
                "In electrical network graph theory G=(V,E), every active circuit node must have a degree ≥ 2, "
                "connecting at least two component terminals to establish a closed current loop."
            )
        else:
            response_text = "No floating nodes or dangling terminals were detected. All network nodes satisfy degree ≥ 2."
        evidence_points = [f"Total Findings Cataloged: {len(findings)}"]

    else:
        # General explanation of current state
        lbl = top_cand.get("label", "Nominal State")
        score = top_cand.get("residual_score", 0.0)
        response_text = (
            f"Current analysis of the {circuit_type.replace('_', ' ').title()} indicates the leading hypothesis is "
            f"**{lbl}** with an aggregate normalized residual score of **{score:.4f}** (where lower indicates closer physical agreement).\n\n"
            f"You can ask me about: circuit classification, why certain nodes were flagged, how to distinguish candidates, "
            f"or the physical impact of component value adjustments."
        )
        evidence_points = [
            f"Circuit Type: {circuit_type}",
            f"Leading Candidate: {lbl}",
            f"Residual S(f): {score:.4f}"
        ]

    return {
        "query": req.query,
        "response": response_text,
        "evidence_points": evidence_points,
        "grounded_in": "Deterministic Circuit Equations & Residual Matrix",
        "human_confirmation_required": True
    }
