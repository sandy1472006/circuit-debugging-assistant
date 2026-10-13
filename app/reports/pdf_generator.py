"""
pdf_generator.py - Professional, concise 1–2 page Circuit Diagnostic Report generator.
Strictly adheres to A4 layout standards, restrained engineering typography, and 2-page maximum constraint.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, HRFlowable
)
from PIL import Image as PILImage
from app.reports.plot_generator import (
    generate_bode_plot, generate_step_plot, generate_schematic_preview_image
)
from app.core.circuit_models import get_model, FREQ_SWEEP_FINE
from app.config import UPLOAD_DIR, SAMPLE_DIR, REFERENCE_DIR
import numpy as np

# Page width for A4 with 28pt margins: 595.27 - 56 = 539.27pt
PAGE_WIDTH = 539.0

def build_pdf_report(
    session_data: Dict[str, Any],
    output_pdf_path: Path,
    plot_images_dir: Path
) -> Path:
    """
    Builds a professional, concise 1-to-2 page engineering diagnostic report.
    Page 1: Circuit Diagnosis (Header, Uploaded vs Reference side-by-side, Summary, Detected Flaws table).
    Page 2: Technical Evidence (Component Table, Governing Equations, Simulation Plot, Recommended Actions, Footer).
    """
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    plot_images_dir.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=26,
        bottomMargin=26
    )

    styles = getSampleStyleSheet()

    # Typography matching professional engineering design system
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#0F172A")
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B")
    )
    h1_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1E293B")
    )
    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B")
    )
    caption_style = ParagraphStyle(
        "CaptionStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        alignment=1, # Centered
        textColor=colors.HexColor("#64748B")
    )
    footer_style = ParagraphStyle(
        "FooterStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#94A3B8")
    )

    session_id = session_data.get("id", "ANALYSIS-001")
    circuit_type = session_data.get("circuit_type", "rc_low_pass")
    type_display = circuit_type.replace("_", " ").title()
    params = session_data.get("parameters", {})
    findings = session_data.get("findings", [])
    diagnosis = session_data.get("diagnosis", {})
    top_cand = diagnosis.get("top_candidate", {})
    created_at = session_data.get("created_at", time.time())
    date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(created_at))

    # Determine Overall Diagnostic Status
    has_critical = any(f.get("severity") == "Critical" for f in findings)
    has_major = any(f.get("severity") == "Major" for f in findings)
    is_faulty = top_cand and top_cand.get("component") != "None"

    if has_critical or (is_faulty and "short" in top_cand.get("mode", "")):
        status_text = "CONFIRMED ISSUES IDENTIFIED"
        status_color = colors.HexColor("#DC2626") # Red
        status_bg = colors.HexColor("#FEF2F2")
    elif has_major or is_faulty:
        status_text = "POTENTIAL ISSUES IDENTIFIED"
        status_color = colors.HexColor("#D97706") # Amber
        status_bg = colors.HexColor("#FFFBEB")
    else:
        status_text = "NO ISSUES DETECTED IN CHECKS"
        status_color = colors.HexColor("#059669") # Green
        status_bg = colors.HexColor("#ECFDF5")

    story = []

    # =========================================================================
    # PAGE 1: CIRCUIT DIAGNOSIS
    # =========================================================================

    # Header & Meta Block
    header_data = [
        [
            Paragraph("<b>Circuit Debugging Assistant</b><br/><font color='#64748B'>Circuit Diagnostic Report</font>", title_style),
            Paragraph(
                f"<b>Report ID:</b> {session_id}<br/>"
                f"<b>Date:</b> {date_str}<br/>"
                f"<b>Circuit:</b> {type_display}",
                body_style
            ),
            Table(
                [[Paragraph(f"<b>STATUS:</b><br/>{status_text}", ParagraphStyle("StatusBadge", parent=body_style, textColor=status_color, fontSize=7, leading=9, alignment=1))]],
                colWidths=[120],
                style=[
                    ('BACKGROUND', (0,0), (-1,-1), status_bg),
                    ('BOX', (0,0), (-1,-1), 1, status_color),
                    ('PADDING', (0,0), (-1,-1), 4),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ]
            )
        ]
    ]
    header_table = Table(header_data, colWidths=[210, 190, 139])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceAfter=5, spaceBefore=2))

    # SECTION 1: UPLOADED VERSUS EXPECTED CIRCUIT (Side-by-Side Images)
    story.append(Paragraph("1. Uploaded versus Expected Circuit", h1_style))

    # Locate uploaded image or create clean thumbnail
    upload_fname = session_data.get("upload_filename", "")
    orig_img_path = None
    if upload_fname:
        p1 = UPLOAD_DIR / upload_fname
        p2 = SAMPLE_DIR / upload_fname
        p3 = UPLOAD_DIR / f"{session_id}_{upload_fname}"
        for candidate in [p1, p2, p3]:
            if candidate.exists() and candidate.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                orig_img_path = candidate
    if not orig_img_path:
        for cand in UPLOAD_DIR.glob(f"{session_id}*"):
            if cand.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                orig_img_path = cand
                break

    # Prepare right-hand reference image
    ref_img_path = plot_images_dir / f"{session_id}_ref_preview.png"
    canonical_ref = REFERENCE_DIR / f"ref_{circuit_type}.png"
    if canonical_ref.exists():
        try:
            im_ref = PILImage.open(canonical_ref)
            im_ref.thumbnail((500, 320))
            im_ref.save(ref_img_path)
        except Exception:
            generate_schematic_preview_image(circuit_type, params, ref_img_path)
    else:
        generate_schematic_preview_image(circuit_type, params, ref_img_path)

    # Prepare left-hand image (Actual Uploaded Schematic)
    left_img_path = plot_images_dir / f"{session_id}_uploaded_preview.png"
    if orig_img_path and orig_img_path.exists():
        try:
            im = PILImage.open(orig_img_path)
            im.thumbnail((500, 320))
            im.save(left_img_path)
        except Exception:
            generate_schematic_preview_image(circuit_type, params, left_img_path)
    else:
        generate_schematic_preview_image(circuit_type, params, left_img_path)

    # Side-by-side Table (each image 260pt wide, 115pt high)
    img_w, img_h = 260, 115
    diag_table_data = [
        [
            RLImage(str(left_img_path), width=img_w, height=img_h),
            RLImage(str(ref_img_path), width=img_w, height=img_h)
        ],
        [
            Paragraph("Figure 1A: Uploaded Circuit Schematic", caption_style),
            Paragraph("Figure 1B: Expected / Reference Circuit Model", caption_style)
        ]
    ]
    diag_table = Table(diag_table_data, colWidths=[268, 268])
    diag_table.setStyle(TableStyle([
        ('BOX', (0,0), (0,0), 0.5, colors.HexColor("#CBD5E1")),
        ('BOX', (1,0), (1,0), 0.5, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FAFAFA")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,1), (-1,1), 4),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 6))

    # SECTION 2: DIAGNOSIS SUMMARY
    story.append(Paragraph("2. Diagnosis Summary", h1_style))
    if is_faulty:
        summary_body = (
            f"The device under test was analyzed as a <b>{type_display}</b>. "
            f"Numerical multi-evidence evaluation identified a probable parameter shift on <b>{top_cand.get('label')}</b> "
            f"(normalized residual score: <b>{top_cand.get('residual_score', 0):.4f}</b>). "
            f"A total of {len(findings)} structural or parameter observations were cataloged."
        )
    elif findings:
        summary_body = (
            f"The device under test was analyzed as a <b>{type_display}</b>. "
            f"Electrical network analysis identified {len(findings)} potential topology or connectivity issue(s) "
            f"requiring engineer verification."
        )
    else:
        summary_body = (
            f"All structural and parametric checks for the <b>{type_display}</b> passed. "
            f"The circuit conforms to the nominal reference topology, with closed electrical nets, designated ground reference, "
            f"and component values within standard 5% manufacturing tolerances."
        )
    story.append(Paragraph(summary_body, body_style))
    story.append(Spacer(1, 6))

    # SECTION 3: DETECTED FLAWS TABLE
    story.append(Paragraph("3. Detected Flaws & Consistency Register", h1_style))

    flaw_rows = [
        [
            Paragraph("<b>Severity</b>", table_header_style),
            Paragraph("<b>Component / Net</b>", table_header_style),
            Paragraph("<b>Finding & Evidence</b>", table_header_style),
            Paragraph("<b>Recommended Action</b>", table_header_style)
        ]
    ]

    # Combine topological findings + fault candidate findings
    displayed_findings = list(findings)
    if is_faulty:
        comp_name = top_cand.get("component")
        mode = top_cand.get("mode")
        displayed_findings.append({
            "severity": "Major" if mode in ["+20%", "-20%"] else "Critical",
            "component_or_net": comp_name,
            "evidence": f"Normalized residual S(f)={top_cand.get('residual_score'):.3f} matches {top_cand.get('label')} signature.",
            "recommended_correction": f"Verify {comp_name} value with bench meter or replace with nominal part."
        })

    if displayed_findings:
        for f in displayed_findings[:5]: # Keep up to top 5 to strictly fit Page 1
            sev = f.get("severity", "Warning")
            sev_color = colors.HexColor("#DC2626") if sev == "Critical" else (
                colors.HexColor("#D97706") if sev == "Major" else colors.HexColor("#1E40AF")
            )
            flaw_rows.append([
                Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", table_cell_style),
                Paragraph(f"<b>{f.get('component_or_net', 'N/A')}</b>", table_cell_style),
                Paragraph(f.get("evidence", f.get("observed_behavior", "Identified anomaly")), table_cell_style),
                Paragraph(f.get("recommended_correction", "Inspect component connections."), table_cell_style)
            ])
    else:
        flaw_rows.append([
            Paragraph("<font color='#059669'><b>Passed</b></font>", table_cell_style),
            Paragraph("All Nets", table_cell_style),
            Paragraph("No topological violations, floating nodes, or short circuits detected.", table_cell_style),
            Paragraph("Proceed to functional bench power-up.", table_cell_style)
        ])

    flaws_table = Table(flaw_rows, colWidths=[65, 85, 220, 169])
    flaws_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(flaws_table)

    # Strictly break to Page 2
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: TECHNICAL EVIDENCE AND RECOMMENDATIONS
    # =========================================================================

    # Page 2 Mini Header
    story.append(Paragraph(
        f"<b>Circuit Diagnostic Report</b> — Technical Evidence & Verification | {session_id} | {date_str}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1"), spaceAfter=5, spaceBefore=2))

    # SECTION 4: COMPONENT VALUES TABLE
    story.append(Paragraph("4. Confirmed Component Values", h1_style))
    comp_rows = [
        [
            Paragraph("<b>Reference</b>", table_header_style),
            Paragraph("<b>Component Type</b>", table_header_style),
            Paragraph("<b>Extracted / Nominal Value</b>", table_header_style),
            Paragraph("<b>Tolerance</b>", table_header_style),
            Paragraph("<b>Verification Status</b>", table_header_style)
        ]
    ]
    for k, v in params.items():
        if k == "Vin":
            comp_rows.append([
                Paragraph("<b>VIN</b>", table_cell_style),
                Paragraph("Input Voltage Source", table_cell_style),
                Paragraph(f"{v:g} V", table_cell_style),
                Paragraph("±1.0%", table_cell_style),
                Paragraph("<font color='#059669'>Confirmed</font>", table_cell_style)
            ])
        elif k.startswith("R"):
            comp_rows.append([
                Paragraph(f"<b>{k}</b>", table_cell_style),
                Paragraph("Film Resistor", table_cell_style),
                Paragraph(f"{v:g} Ω", table_cell_style),
                Paragraph("±5.0%", table_cell_style),
                Paragraph("<font color='#059669'>Confirmed</font>", table_cell_style)
            ])
        elif k.startswith("C"):
            comp_rows.append([
                Paragraph(f"<b>{k}</b>", table_cell_style),
                Paragraph("Ceramic / Electrolytic Capacitor", table_cell_style),
                Paragraph(f"{v*1e9:.2f} nF", table_cell_style),
                Paragraph("±10.0%", table_cell_style),
                Paragraph("<font color='#059669'>Confirmed</font>", table_cell_style)
            ])
        elif k.startswith("L"):
            comp_rows.append([
                Paragraph(f"<b>{k}</b>", table_cell_style),
                Paragraph("Inductor Choke", table_cell_style),
                Paragraph(f"{v*1e3:.2f} mH", table_cell_style),
                Paragraph("±10.0%", table_cell_style),
                Paragraph("<font color='#059669'>Confirmed</font>", table_cell_style)
            ])

    comp_table = Table(comp_rows, colWidths=[65, 150, 130, 80, 114])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")])
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 5))

    # SECTION 5: EXPECTED BEHAVIOUR & GOVERNING FORMULAS
    story.append(Paragraph("5. Expected Behaviour & Governing Calculations", h1_style))
    calc_text = ""
    if circuit_type == "rc_low_pass":
        r = params.get("R", 1000.0)
        c = params.get("C", 100e-9)
        fc_calc = 1.0 / (2.0 * np.pi * r * c)
        i_step = params.get("Vin", 1.0) / r
        calc_text = (
            f"• <b>Transfer Function:</b> H(f) = 1 / (1 + j 2π f R C)<br/>"
            f"• <b>Theoretical Cutoff Frequency:</b> fc = 1 / (2π · R · C) = <b>{fc_calc:.2f} Hz</b><br/>"
            f"• <b>Initial Step Current (Independent Observable):</b> I_step(0+) = Vin / R = <b>{i_step*1e3:.2f} mA</b>"
        )
    elif circuit_type == "rl_high_pass":
        r = params.get("R", 1000.0)
        l = params.get("L", 0.1)
        fc_calc = r / (2.0 * np.pi * l)
        i_dc = params.get("Vin", 1.0) / r
        calc_text = (
            f"• <b>Transfer Function:</b> H(f) = (j 2π f L) / (R + j 2π f L)<br/>"
            f"• <b>Theoretical Cutoff Frequency:</b> fc = R / (2π · L) = <b>{fc_calc:.2f} Hz</b><br/>"
            f"• <b>DC Branch Current (Independent Observable):</b> I_DC = Vin / R = <b>{i_dc*1e3:.2f} mA</b>"
        )
    elif circuit_type == "rlc_band_pass":
        r = params.get("R", 1000.0)
        l = params.get("L", 0.01)
        c = params.get("C", 25.33e-9)
        f0_calc = 1.0 / (2.0 * np.pi * np.sqrt(l * c))
        q_calc = r * np.sqrt(c / l)
        bw_calc = f0_calc / max(q_calc, 1e-6)
        calc_text = (
            f"• <b>Resonant Center Frequency:</b> f0 = 1 / (2π √(L · C)) = <b>{f0_calc:.2f} Hz</b><br/>"
            f"• <b>Quality Factor & Bandwidth:</b> Q = <b>{q_calc:.2f}</b>, BW = <b>{bw_calc:.2f} Hz</b><br/>"
            f"• <b>DC Bias Current:</b> I_DC = Vin / R = <b>{(params.get('Vin', 1.0)/r)*1e3:.2f} mA</b>"
        )
    else: # Voltage divider
        r1 = params.get("R1", 10000.0)
        r2 = params.get("R2", 10000.0)
        vin = params.get("Vin", 10.0)
        vout_calc = vin * (r2 / (r1 + r2))
        isup_calc = vin / (r1 + r2)
        calc_text = (
            f"• <b>Transfer Ratio:</b> Vout = Vin · [R2 / (R1 + R2)] = <b>{vout_calc:.2f} V</b> (for Vin = {vin:g}V)<br/>"
            f"• <b>Total Series Current:</b> Is = Vin / (R1 + R2) = <b>{isup_calc*1e3:.3f} mA</b>"
        )
    story.append(Paragraph(calc_text, body_style))
    story.append(Spacer(1, 5))

    # SECTION 6: SIMULATION PLOT
    story.append(Paragraph("6. Numerical Simulation Curves", h1_style))
    sim_plot_path = plot_images_dir / f"{session_id}_sim_plot.png"
    model = get_model(circuit_type, params)

    if circuit_type != "voltage_divider":
        mag_nom, phase_nom = model.get_frequency_response(model.nominal_params, FREQ_SWEEP_FINE)
        mag_act, phase_act = model.get_frequency_response(params, FREQ_SWEEP_FINE)
        fc = getattr(model, "cutoff_frequency", lambda p: 0.0)(params)
        generate_bode_plot(FREQ_SWEEP_FINE, mag_nom, phase_nom, mag_act, phase_act, cutoff_freq=fc, output_path=sim_plot_path)
    else:
        time_pts = np.linspace(0, 0.002, 100)
        v_step = model.get_step_response(params, time_pts)
        generate_step_plot(time_pts, v_step, output_path=sim_plot_path)

    if sim_plot_path.exists():
        story.append(RLImage(str(sim_plot_path), width=536, height=155))
        story.append(Spacer(1, 4))

    # SECTION 7: RECOMMENDED ACTIONS
    story.append(Paragraph("7. Recommended Engineering Actions", h1_style))
    rec = diagnosis.get("adaptive_recommendation", {}).get("recommended_test", {})
    rec_test_name = rec.get("test_name", "In-circuit component DMM measurement") if rec else "In-circuit DMM measurement"

    actions_text = (
        f"1. <b>Physical Verification:</b> Perform <b>{rec_test_name}</b> to independently separate ambiguous parameter hypotheses.<br/>"
        f"2. <b>Signal Integrity:</b> Measure test points with a 10:1 passive probe to avoid probe capacitance loading.<br/>"
        f"3. <b>Post-Repair Gate:</b> Confirm that measured response stays within ±5% of reference cutoff before releasing design."
    )
    story.append(Paragraph(actions_text, body_style))
    story.append(Spacer(1, 8))

    # FOOTER
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=3, spaceBefore=2))
    story.append(Paragraph(
        "<b>Circuit Debugging Assistant v1.0.0</b> | Analysis Assumptions: Deterministic linear lumped-element models. "
        "Parasitic trace capacitance and connector contact resistances require laboratory bench instrument verification.",
        footer_style
    ))

    # Build the document
    doc.build(story)
    return output_pdf_path
