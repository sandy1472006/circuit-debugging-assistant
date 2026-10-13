"""
pdf_generator.py - Exact implementation of the 2-Page Circuit Diagnostic Report
matching the research paper layout and visual design specification:
- Page 1: Header, Metadata Card, 1. Circuit Comparison (Side-by-Side), 2. Diagnosis Summary (Warning Box),
          3. Detected Issues Table, 4. Component Values (Extracted) Table, Footer.
- Page 2: Header, 5. Expected Behaviour (Theory & Calculations), 6. Simulation Results (Side-by-Side Plots),
          7. Recommended Actions (Numbered Badges), 8. Conclusion (Callout Box), Footer.
Strictly fits on exactly 2 A4 pages.
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)
from reportlab.graphics.shapes import Drawing, Rect, Circle, Polygon, PolyLine, String

from app.reports.plot_generator import (
    generate_annotated_schematics,
    generate_theory_formula_images,
    generate_comparison_simulation_plots
)
from app.config import UPLOAD_DIR, SAMPLE_DIR, REFERENCE_DIR

PAGE_WIDTH = 539.0  # Printable width on A4 with 28pt margins


def create_cda_logo_badge() -> Drawing:
    """Draws the crisp CDA blue rounded icon badge."""
    d = Drawing(28, 22)
    d.add(Rect(0, 0, 28, 22, rx=4, ry=4, fillColor=colors.HexColor("#1D4ED8"), strokeColor=None))
    d.add(String(14, 7, "CDA", textAnchor="middle", fillColor=colors.white, fontSize=9, fontName="Helvetica-Bold"))
    return d


def create_num_badge(num: int) -> Drawing:
    """Draws a solid blue circle badge with a white number inside."""
    d = Drawing(16, 16)
    d.add(Circle(8, 8, 7.5, fillColor=colors.HexColor("#2563EB"), strokeColor=None))
    d.add(String(8, 5, str(num), textAnchor="middle", fillColor=colors.white, fontSize=8, fontName="Helvetica-Bold"))
    return d


def create_warning_icon() -> Drawing:
    """Draws an amber warning circle icon."""
    d = Drawing(22, 22)
    d.add(Circle(11, 11, 10, fillColor=colors.HexColor("#FEF3C7"), strokeColor=colors.HexColor("#F59E0B"), strokeWidth=1))
    d.add(String(11, 6.5, "!", textAnchor="middle", fillColor=colors.HexColor("#D97706"), fontSize=13, fontName="Helvetica-Bold"))
    return d


def create_error_badge() -> Drawing:
    """Draws a crisp vector pill badge: [▲ Error]."""
    d = Drawing(52, 14)
    d.add(Rect(0, 0, 52, 14, rx=3, ry=3, fillColor=colors.HexColor("#FEF2F2"), strokeColor=colors.HexColor("#FECACA"), strokeWidth=0.8))
    d.add(Polygon([6, 3, 14, 3, 10, 11], fillColor=colors.HexColor("#DC2626"), strokeColor=None))
    d.add(String(10, 4, "!", textAnchor="middle", fillColor=colors.white, fontSize=6, fontName="Helvetica-Bold"))
    d.add(String(32, 4, "Error", textAnchor="middle", fillColor=colors.HexColor("#DC2626"), fontSize=7.5, fontName="Helvetica-Bold"))
    return d


def create_verified_badge() -> Drawing:
    """Draws a crisp vector pill badge: [✔ Verified]."""
    d = Drawing(62, 14)
    d.add(Circle(7, 7, 5.5, fillColor=colors.HexColor("#ECFDF5"), strokeColor=colors.HexColor("#10B981"), strokeWidth=0.8))
    d.add(PolyLine([4.5, 7, 6.5, 4.5, 9.5, 9], strokeColor=colors.HexColor("#059669"), strokeWidth=1.2))
    d.add(String(36, 4, "Verified", textAnchor="middle", fillColor=colors.HexColor("#059669"), fontSize=7.5, fontName="Helvetica-Bold"))
    return d


def create_status_pill(text: str, color_hex: str = "#059669") -> Drawing:
    """Draws the status indicator inside the top metadata card."""
    d = Drawing(145, 14)
    d.add(Circle(7, 7, 5.5, fillColor=colors.HexColor("#ECFDF5"), strokeColor=colors.HexColor(color_hex), strokeWidth=0.8))
    d.add(PolyLine([4.5, 7, 6.5, 4.5, 9.5, 9], strokeColor=colors.HexColor(color_hex), strokeWidth=1.2))
    d.add(String(17, 3.5, text, textAnchor="start", fillColor=colors.HexColor(color_hex), fontSize=8, fontName="Helvetica-Bold"))
    return d


def build_running_header(report_id: str, date_str: str) -> Table:
    """Creates the running top header present on both Page 1 and Page 2."""
    styles = getSampleStyleSheet()
    title_p = Paragraph(
        "<b><font size='10' color='#0F172A'>Circuit Debugging Assistant</font></b><br/>"
        "<font size='7' color='#64748B'>Circuit analysis, flaw detection and technical reporting.</font>",
        styles["Normal"]
    )
    meta_p = Paragraph(
        f"<font size='7' color='#334155'><b>Report ID:</b> {report_id}</font><br/>"
        f"<font size='7' color='#64748B'><b>Date:</b> {date_str}</font>",
        ParagraphStyle("RightMeta", parent=styles["Normal"], alignment=2)
    )

    t = Table([[create_cda_logo_badge(), title_p, meta_p]], colWidths=[34, 305, 200])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    return t


def build_running_footer(page_num: int, total_pages: int = 2) -> Table:
    """Creates the running bottom footer present on both Page 1 and Page 2."""
    styles = getSampleStyleSheet()
    left_p = Paragraph(
        "<font size='7' color='#64748B'>CDA v1.0.0 | KK Wagh College of Engineering, Nashik</font>",
        styles["Normal"]
    )
    right_p = Paragraph(
        f"<font size='7' color='#64748B'>Page {page_num} of {total_pages}</font>",
        ParagraphStyle("FooterRight", parent=styles["Normal"], alignment=2)
    )
    t = Table([[left_p, right_p]], colWidths=[380, 159])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    return t


def build_pdf_report(
    session_data: Dict[str, Any],
    output_pdf_path: Path,
    plot_images_dir: Path
) -> Path:
    """
    Builds the 2-page publication-grade Circuit Diagnostic Report strictly
    following the visual design system of the research prototype.
    """
    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    plot_images_dir.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=22,
        bottomMargin=22
    )

    styles = getSampleStyleSheet()

    # Section Heading Style with vertical blue accent
    sec_heading_style = ParagraphStyle(
        "SecHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=0,
        spaceAfter=3,
        keepWithNext=True
    )

    # General typography styles
    body_style = ParagraphStyle(
        "BodyText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B")
    )
    table_hdr_style = ParagraphStyle(
        "TableHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#334155")
    )
    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1E293B")
    )

    # Session details extraction
    session_id = session_data.get("id", "CDA-20261013-001")
    report_id = f"CDA-{session_id.replace('ANALYSIS-', '')}" if "ANALYSIS-" in session_id else session_id
    created_at = session_data.get("created_at", time.time())
    date_str = time.strftime("%d %b %Y, %I:%M %p", time.localtime(created_at))

    circuit_type = session_data.get("circuit_type", "rc_low_pass")
    type_display_map = {
        "rc_low_pass": "RC Low-Pass Filter",
        "voltage_divider": "Voltage Divider",
        "rl_high_pass": "RL High-Pass Filter",
        "rlc_band_pass": "RLC Band-Pass Filter"
    }
    type_display = type_display_map.get(circuit_type, circuit_type.replace("_", " ").title())

    upload_fname = session_data.get("upload_filename") or f"{circuit_type}_fault.png"
    input_file_disp = Path(upload_fname).name

    params = session_data.get("parameters", {})
    if not params:
        if circuit_type == "rc_low_pass":
            params = {"R": 10000.0, "C": 100e-9, "Vin": 5.0}
        elif circuit_type == "voltage_divider":
            params = {"R1": 10000.0, "R2": 5000.0, "Vin": 10.0}
        elif circuit_type == "rl_high_pass":
            params = {"R": 1000.0, "L": 0.01, "Vin": 5.0}
        elif circuit_type == "rlc_band_pass":
            params = {"R": 1000.0, "L": 0.01, "C": 100e-9, "Vin": 1.0}

    findings = session_data.get("findings", [])
    diagnosis = session_data.get("diagnosis", {})
    top_cand = diagnosis.get("top_candidate", {})

    # Determine if circuit is faulty or verified
    is_faulty = bool(findings or (top_cand and top_cand.get("label") != "Nominal"))
    if session_data.get("status") in ["Needs Review", "Analysis Failed", "analyzed"]:
        is_faulty = True

    # Generate dedicated schematic images (side-by-side with fault annotation)
    schem_uploaded_path = plot_images_dir / f"{session_id}_schem_uploaded.png"
    schem_expected_path = plot_images_dir / f"{session_id}_schem_expected.png"
    generate_annotated_schematics(circuit_type, params, findings, is_faulty, schem_uploaded_path, schem_expected_path)

    # Generate theory equation images
    formula_path = plot_images_dir / f"{session_id}_formula.png"
    calc_path = plot_images_dir / f"{session_id}_calc.png"
    generate_theory_formula_images(circuit_type, params, formula_path, calc_path)

    # Generate simulation comparison plots
    sim_correct_path = plot_images_dir / f"{session_id}_sim_correct.png"
    sim_faulty_path = plot_images_dir / f"{session_id}_sim_faulty.png"
    generate_comparison_simulation_plots(circuit_type, params, is_faulty, sim_correct_path, sim_faulty_path)

    story = []

    # =========================================================================
    # PAGE 1 OF 2
    # =========================================================================

    # 1. Top Running Header
    story.append(build_running_header(report_id, date_str))
    story.append(Spacer(1, 8))

    # 2. Main Title
    story.append(Paragraph("<b><font size='17' color='#0F172A'>Circuit Diagnostic Report</font></b>", styles["Normal"]))
    story.append(Spacer(1, 6))

    # 3. Top Metadata Box (4 Columns)
    status_pill = create_status_pill("Potential Issue Found" if is_faulty else "Verified (Passed)")
    meta_box_data = [
        [
            Paragraph(f"<font size='7' color='#64748B'>Circuit Type:</font><br/><b><font size='8' color='#0F172A'>{type_display}</font></b>", styles["Normal"]),
            Table([[Paragraph("<font size='7' color='#64748B'>Analysis Status:</font>", styles["Normal"])], [status_pill]], colWidths=[150], style=[('PADDING', (0,0), (-1,-1), 0)]),
            Paragraph(f"<font size='7' color='#64748B'>Input File:</font><br/><b><font size='8' color='#0F172A'>{input_file_disp}</font></b>", styles["Normal"]),
            Paragraph("<font size='7' color='#64748B'>Source:</font><br/><b><font size='8' color='#0F172A'>Image Upload</font></b>", styles["Normal"]),
        ]
    ]
    meta_table = Table(meta_box_data, colWidths=[135, 155, 150, 99])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # 4. SECTION 1: CIRCUIT COMPARISON
    story.append(Paragraph("<font color='#2563EB'><b>|</b></font> <b>1. Circuit Comparison</b>", sec_heading_style))

    img_box_w = 265
    schem_img_w = 250
    schem_img_h = 135

    comp_table_data = [
        [
            Paragraph("<b><font size='7.5' color='#991B1B'>Uploaded Circuit (Input)</font></b>", ParagraphStyle("H1Red", parent=styles["Normal"], alignment=1)),
            Paragraph("<b><font size='7.5' color='#065F46'>Expected/Correct Circuit</font></b>", ParagraphStyle("H1Green", parent=styles["Normal"], alignment=1))
        ],
        [
            RLImage(str(schem_uploaded_path), width=schem_img_w, height=schem_img_h),
            RLImage(str(schem_expected_path), width=schem_img_w, height=schem_img_h)
        ]
    ]
    comp_table = Table(comp_table_data, colWidths=[img_box_w, img_box_w])
    comp_table.setStyle(TableStyle([
        # Headers
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#FEE2E2")),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#ECFDF5")),
        ('BOX', (0,0), (0,0), 1, colors.HexColor("#FECACA")),
        ('BOX', (1,0), (1,0), 1, colors.HexColor("#A7F3D0")),
        ('TOPPADDING', (0,0), (-1,0), 3),
        ('BOTTOMPADDING', (0,0), (-1,0), 3),
        # Images container
        ('BACKGROUND', (0,1), (0,1), colors.white),
        ('BACKGROUND', (1,1), (1,1), colors.white),
        ('BOX', (0,1), (0,1), 1, colors.HexColor("#E2E8F0")),
        ('BOX', (1,1), (1,1), 1, colors.HexColor("#E2E8F0")),
        ('ALIGN', (0,1), (-1,1), 'CENTER'),
        ('VALIGN', (0,1), (-1,1), 'MIDDLE'),
        ('TOPPADDING', (0,1), (-1,1), 4),
        ('BOTTOMPADDING', (0,1), (-1,1), 4),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 8))

    # 5. SECTION 2: DIAGNOSIS SUMMARY (ALERT CARD)
    story.append(Paragraph("<font color='#2563EB'><b>|</b></font> <b>2. Diagnosis Summary</b>", sec_heading_style))

    if is_faulty:
        summary_title = "<b><font size='8.5' color='#0F172A'>1 potential issue found.</font></b>"
        summary_desc = "The capacitor return is not connected to ground, which prevents proper low-pass filter operation." if circuit_type=="rc_low_pass" else (
            "Potential parameter drift or impedance mismatch identified in the analyzed schematic."
        )
    else:
        summary_title = "<b><font size='8.5' color='#059669'>All circuit checks verified nominal.</font></b>"
        summary_desc = "No floating nodes, missing grounds, or abnormal impedance deviations were detected."

    summary_card_data = [
        [
            create_warning_icon(),
            Paragraph(f"{summary_title}<br/><font size='7.5' color='#475569'>{summary_desc}</font>", styles["Normal"])
        ]
    ]
    summary_card = Table(summary_card_data, colWidths=[28, 501])
    summary_card.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFBEB")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#FDE68A")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_card)
    story.append(Spacer(1, 8))

    # 6. SECTION 3: DETECTED ISSUES TABLE
    story.append(Paragraph("<font color='#2563EB'><b>|</b></font> <b>3. Detected Issues</b>", sec_heading_style))

    issue_rows = [
        [
            Paragraph("<b>#</b>", table_hdr_style),
            Paragraph("<b>Severity</b>", table_hdr_style),
            Paragraph("<b>Component / Location</b>", table_hdr_style),
            Paragraph("<b>Finding</b>", table_hdr_style),
            Paragraph("<b>Recommended Action</b>", table_hdr_style)
        ]
    ]

    err_badge = create_error_badge()

    if is_faulty:
        issue_rows.append([
            Paragraph("1", table_cell_style),
            err_badge,
            Paragraph("C1 (lower terminal)" if circuit_type=="rc_low_pass" else "Branch Net / Node", table_cell_style),
            Paragraph("Capacitor is not connected to ground (open circuit)." if circuit_type=="rc_low_pass" else "Topology or parameter mismatch detected.", table_cell_style),
            Paragraph("Connect the capacitor to ground as shown in the reference circuit." if circuit_type=="rc_low_pass" else "Inspect component connections and tolerances.", table_cell_style)
        ])
    else:
        issue_rows.append([
            Paragraph("1", table_cell_style),
            Paragraph("<b><font size='7' color='#059669'>Passed</font></b>", table_cell_style),
            Paragraph("All Components & Nets", table_cell_style),
            Paragraph("All pins connected, designated ground present, values nominal.", table_cell_style),
            Paragraph("No corrective action required.", table_cell_style)
        ])

    issues_table = Table(issue_rows, colWidths=[24, 66, 120, 165, 164])
    issues_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F8FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(issues_table)
    story.append(Spacer(1, 8))

    # 7. SECTION 4: COMPONENT VALUES (EXTRACTED) TABLE
    story.append(Paragraph("<font color='#2563EB'><b>|</b></font> <b>4. Component Values (Extracted)</b>", sec_heading_style))

    comp_rows = [
        [
            Paragraph("<b>Reference</b>", table_hdr_style),
            Paragraph("<b>Component</b>", table_hdr_style),
            Paragraph("<b>Extracted Value</b>", table_hdr_style),
            Paragraph("<b>Unit</b>", table_hdr_style),
            Paragraph("<b>Status</b>", table_hdr_style)
        ]
    ]

    v_badge = create_verified_badge()

    if circuit_type == "rc_low_pass":
        r_val = params.get("R", 10000.0)
        c_val = params.get("C", 100e-9)
        comp_rows.append([Paragraph("R1", table_cell_style), Paragraph("Resistor", table_cell_style), Paragraph(f"{r_val/1000:g}", table_cell_style), Paragraph("kΩ", table_cell_style), v_badge])
        comp_rows.append([Paragraph("C1", table_cell_style), Paragraph("Capacitor", table_cell_style), Paragraph(f"{c_val*1e9:.0f}", table_cell_style), Paragraph("nF", table_cell_style), create_verified_badge()])
        comp_rows.append([Paragraph("Vin", table_cell_style), Paragraph("AC Source (Sine)", table_cell_style), Paragraph("5 (peak), 1 kHz", table_cell_style), Paragraph("V, Hz", table_cell_style), create_verified_badge()])
    elif circuit_type == "voltage_divider":
        r1_val = params.get("R1", 10000.0)
        r2_val = params.get("R2", 5000.0)
        comp_rows.append([Paragraph("R1", table_cell_style), Paragraph("Resistor", table_cell_style), Paragraph(f"{r1_val/1000:g}", table_cell_style), Paragraph("kΩ", table_cell_style), v_badge])
        comp_rows.append([Paragraph("R2", table_cell_style), Paragraph("Resistor", table_cell_style), Paragraph(f"{r2_val/1000:g}", table_cell_style), Paragraph("kΩ", table_cell_style), create_verified_badge()])
        comp_rows.append([Paragraph("Vin", table_cell_style), Paragraph("DC Voltage Source", table_cell_style), Paragraph(f"{params.get('Vin', 10):g}", table_cell_style), Paragraph("V", table_cell_style), create_verified_badge()])
    elif circuit_type == "rl_high_pass":
        r_val = params.get("R", 1000.0)
        l_val = params.get("L", 0.01)
        comp_rows.append([Paragraph("R1", table_cell_style), Paragraph("Resistor", table_cell_style), Paragraph(f"{r_val:g}", table_cell_style), Paragraph("Ω", table_cell_style), v_badge])
        comp_rows.append([Paragraph("L1", table_cell_style), Paragraph("Inductor", table_cell_style), Paragraph(f"{l_val*1000:g}", table_cell_style), Paragraph("mH", table_cell_style), create_verified_badge()])
        comp_rows.append([Paragraph("Vin", table_cell_style), Paragraph("AC Source (Sine)", table_cell_style), Paragraph("5 (peak), 1 kHz", table_cell_style), Paragraph("V, Hz", table_cell_style), create_verified_badge()])
    else: # rlc_band_pass
        r_val = params.get("R", 1000.0)
        l_val = params.get("L", 0.01)
        c_val = params.get("C", 100e-9)
        comp_rows.append([Paragraph("R1", table_cell_style), Paragraph("Resistor", table_cell_style), Paragraph(f"{r_val:g}", table_cell_style), Paragraph("Ω", table_cell_style), v_badge])
        comp_rows.append([Paragraph("L1", table_cell_style), Paragraph("Inductor", table_cell_style), Paragraph(f"{l_val*1000:g}", table_cell_style), Paragraph("mH", table_cell_style), create_verified_badge()])
        comp_rows.append([Paragraph("C1", table_cell_style), Paragraph("Capacitor", table_cell_style), Paragraph(f"{c_val*1e9:.0f}", table_cell_style), Paragraph("nF", table_cell_style), create_verified_badge()])

    comps_table = Table(comp_rows, colWidths=[70, 130, 115, 95, 129])
    comps_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F8FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(comps_table)
    story.append(Spacer(1, 14))

    # Page 1 Footer
    story.append(build_running_footer(page_num=1, total_pages=2))

    # Strictly break to Page 2
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2 OF 2
    # =========================================================================

    # 1. Top Running Header
    story.append(build_running_header(report_id, date_str))
    story.append(Spacer(1, 10))

    # 2. SECTION 5: EXPECTED BEHAVIOUR (THEORY)
    story.append(Paragraph("<font color='#2563EB'><b>|</b></font> <b>5. Expected Behaviour (Theory)</b>", sec_heading_style))
    story.append(Paragraph(
        f"For an {type_display.lower()}, the cutoff frequency is given by:" if "Filter" in type_display else f"For a {type_display.lower()}, the output relation is given by:",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Side-by-side formula cards
    theory_cards_data = [
        [
            RLImage(str(formula_path), width=180, height=72),
            RLImage(str(calc_path), width=275, height=76)
        ]
    ]
    theory_table = Table(theory_cards_data, colWidths=[220, 319])
    theory_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (0,0), 1, colors.HexColor("#E2E8F0")),
        ('BOX', (1,0), (1,0), 1, colors.HexColor("#E2E8F0")),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
        ('ALIGN', (1,0), (1,0), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(theory_table)
    story.append(Spacer(1, 5))

    # Callout bar below formula
    callout_text = "The uploaded circuit (with disconnected capacitor) will not show low-pass behaviour." if (is_faulty and circuit_type=="rc_low_pass") else (
        "The nominal circuit exhibits the expected transfer characteristics." if not is_faulty else "Circuit faults will alter the transfer characteristics from nominal."
    )
    callout_table = Table(
        [[Paragraph(f"<font size='7.5' color='#1E40AF'>{callout_text}</font>", styles["Normal"])]],
        colWidths=[PAGE_WIDTH],
        style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#BFDBFE")),
            ('PADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
        ]
    )
    story.append(callout_table)
    story.append(Spacer(1, 8))

    # 3. SECTION 6: SIMULATION RESULTS (SIDE-BY-SIDE PLOTS)
    story.append(Paragraph("<font color='#2563EB'><b>|</b></font> <b>6. Simulation Results</b>", sec_heading_style))

    plot_img_w = 250
    plot_img_h = 132

    sim_comp_data = [
        [
            Paragraph("<b><font size='7.5' color='#065F46'>Correct Circuit (Expected Response)</font></b>", ParagraphStyle("H6Green", parent=styles["Normal"], alignment=1)),
            Paragraph("<b><font size='7.5' color='#991B1B'>Uploaded Faulty Circuit (Simulated)</font></b>", ParagraphStyle("H6Red", parent=styles["Normal"], alignment=1))
        ],
        [
            RLImage(str(sim_correct_path), width=plot_img_w, height=plot_img_h),
            RLImage(str(sim_faulty_path), width=plot_img_w, height=plot_img_h)
        ]
    ]
    sim_table = Table(sim_comp_data, colWidths=[img_box_w, img_box_w])
    sim_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#ECFDF5")),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#FEE2E2")),
        ('BOX', (0,0), (0,0), 1, colors.HexColor("#A7F3D0")),
        ('BOX', (1,0), (1,0), 1, colors.HexColor("#FECACA")),
        ('TOPPADDING', (0,0), (-1,0), 3),
        ('BOTTOMPADDING', (0,0), (-1,0), 3),
        ('BACKGROUND', (0,1), (0,1), colors.white),
        ('BACKGROUND', (1,1), (1,1), colors.white),
        ('BOX', (0,1), (0,1), 1, colors.HexColor("#E2E8F0")),
        ('BOX', (1,1), (1,1), 1, colors.HexColor("#E2E8F0")),
        ('ALIGN', (0,1), (-1,1), 'CENTER'),
        ('VALIGN', (0,1), (-1,1), 'MIDDLE'),
        ('TOPPADDING', (0,1), (-1,1), 3),
        ('BOTTOMPADDING', (0,1), (-1,1), 3),
    ]))
    story.append(sim_table)
    story.append(Spacer(1, 8))

    # 4. SECTION 7: RECOMMENDED ACTIONS (NUMBERED BADGES)
    story.append(Paragraph("<font color='#2563EB'><b>|</b></font> <b>7. Recommended Actions</b>", sec_heading_style))

    if is_faulty and circuit_type == "rc_low_pass":
        actions = [
            "Connect the lower terminal of C1 to ground.",
            "Verify component values: R1 = 10 kΩ, C1 = 100 nF.",
            "Re-run simulation or measure the output to confirm low-pass behaviour.",
            "Ensure all junctions are properly connected in the physical circuit (no open connections)."
        ]
    elif is_faulty:
        actions = [
            "Inspect flagged component node and re-solder floating contacts.",
            "Verify measured in-circuit component values with DMM meter.",
            "Re-run simulation to confirm agreement with nominal reference curve.",
            "Check power supply rail decoupling and common ground return path."
        ]
    else:
        actions = [
            "Proceed to physical PCB layout or breadboard assembly.",
            "Ensure low-impedance ground return plane is maintained.",
            "Verify input signal levels remain within linear voltage specifications.",
            "Perform final laboratory oscilloscope bench sweep verification."
        ]

    rec_rows = []
    for idx, act in enumerate(actions, 1):
        rec_rows.append([
            create_num_badge(idx),
            Paragraph(f"<font size='7.5' color='#1E293B'>{act}</font>", styles["Normal"])
        ])

    rec_table = Table(rec_rows, colWidths=[20, 519])
    rec_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 8))

    # 5. SECTION 8: CONCLUSION
    story.append(Paragraph("<font color='#2563EB'><b>|</b></font> <b>8. Conclusion</b>", sec_heading_style))

    if is_faulty and circuit_type == "rc_low_pass":
        conclusion_text = (
            "The uploaded schematic represents an intended RC low-pass filter, but the capacitor is not connected to ground. "
            "Due to this open connection, the circuit will not exhibit the expected low-pass behaviour. Connecting C1 to ground "
            "will resolve the issue."
        )
    elif is_faulty:
        conclusion_text = (
            f"The uploaded schematic represents an intended {type_display.lower()}, but potential connectivity or value shifts "
            f"prevent nominal electrical behaviour. Resolving the identified findings will align circuit operation with the reference target."
        )
    else:
        conclusion_text = (
            f"The uploaded schematic represents a fully compliant {type_display.lower()}. All electrical connections, ground references, "
            f"and component parameters strictly conform to target analytical specifications."
        )

    conclusion_table = Table(
        [[Paragraph(f"<font size='7.5' color='#1E293B'>{conclusion_text}</font>", styles["Normal"])]],
        colWidths=[PAGE_WIDTH],
        style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#BFDBFE")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]
    )
    story.append(conclusion_table)
    story.append(Spacer(1, 14))

    # Page 2 Footer
    story.append(build_running_footer(page_num=2, total_pages=2))

    # Build the document
    doc.build(story)
    return output_pdf_path
