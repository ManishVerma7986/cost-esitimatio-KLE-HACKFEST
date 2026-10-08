"""Export service for CSV, JSON, Excel, and PDF reports."""

from __future__ import annotations

import io
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas.estimate import EstimateResponse
from app.security.file_validator import defang_csv_formula_injection


def export_estimate_json(estimate: EstimateResponse, project_name: str = "Project") -> str:
    """Export complete estimate data as structured JSON string."""
    data = {
        "project_name": project_name,
        "exported_at": datetime.now().isoformat(),
        "estimate": estimate.model_dump(mode="json"),
    }
    return json.dumps(data, indent=2)


def export_estimate_csv(estimate: EstimateResponse, project_name: str = "Project") -> str:
    """Export itemized estimate components as CSV with formula injection defense."""
    rows = []
    for comp in estimate.components:
        rows.append({
            "Project": defang_csv_formula_injection(project_name),
            "Category": defang_csv_formula_injection(comp.category),
            "Subcategory": defang_csv_formula_injection(comp.subcategory or ""),
            "Item Name": defang_csv_formula_injection(comp.name),
            "Quantity": comp.quantity or "",
            "Unit": defang_csv_formula_injection(comp.unit or ""),
            "Unit Cost ($)": f"{comp.unit_cost:.2f}" if comp.unit_cost is not None else "",
            "Total Amount ($)": f"{comp.total_amount:.2f}",
            "Source / Basis": defang_csv_formula_injection(comp.source),
            "Formula / Notes": defang_csv_formula_injection(comp.formula or ""),
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def export_estimate_excel(estimate: EstimateResponse, project_name: str = "Project") -> bytes:
    """Export styled multi-tab Excel workbook with summary and line-item breakdown."""
    wb = Workbook()

    # Sheet 1: Executive Summary
    ws_summary = wb.active
    ws_summary.title = "Executive Summary"

    header_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    label_font = Font(name="Calibri", size=11, bold=True)

    ws_summary["A1"] = f"Software Cost Estimate: {project_name}"
    ws_summary["A1"].font = header_font
    ws_summary["A1"].fill = header_fill
    ws_summary.merge_cells("A1:D1")

    cb = estimate.cost_breakdown
    summary_data = [
        ("Version", f"v{estimate.version}"),
        ("Status", estimate.status.title()),
        ("Estimation Method", estimate.estimation_method or "Hybrid Ensemble"),
        ("Total Effort (Hours)", f"{estimate.total_effort_hours:,.1f} hrs"),
        ("Estimated Duration", f"{estimate.estimated_duration_weeks:.1f} weeks"),
        ("Personnel Cost", f"${cb.personnel:,.2f}"),
        ("Tooling & Licenses", f"${cb.tooling:,.2f}"),
        ("Cloud Infrastructure", f"${cb.cloud:,.2f}"),
        ("Contingency Buffer", f"${cb.contingency:,.2f}"),
        ("TOTAL ESTIMATED COST", f"${cb.total:,.2f}"),
    ]

    if estimate.uncertainty:
        u = estimate.uncertainty
        summary_data.extend([
            ("P50 Expected Cost (Median)", f"${u.p50:,.2f}" if u.p50 else "N/A"),
            ("P80 High-Confidence Budget", f"${u.p80:,.2f}" if u.p80 else "N/A"),
            ("Simulation Iterations", f"{u.simulation_count:,}" if u.simulation_count else "10,000"),
        ])

    for row_idx, (label, val) in enumerate(summary_data, start=3):
        ws_summary.cell(row=row_idx, column=1, value=label).font = label_font
        ws_summary.cell(row=row_idx, column=2, value=val)

    # Sheet 2: Itemized Components
    ws_items = wb.create_sheet(title="Cost Components")
    headers = ["Category", "Subcategory", "Item Description", "Quantity", "Unit", "Unit Cost ($)", "Total Amount ($)", "Source", "Formula"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws_items.cell(row=1, column=col_idx, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="203764", end_color="203764", fill_type="solid")

    for row_idx, comp in enumerate(estimate.components, start=2):
        ws_items.cell(row=row_idx, column=1, value=comp.category)
        ws_items.cell(row=row_idx, column=2, value=comp.subcategory or "")
        ws_items.cell(row=row_idx, column=3, value=comp.name)
        ws_items.cell(row=row_idx, column=4, value=comp.quantity)
        ws_items.cell(row=row_idx, column=5, value=comp.unit or "")
        ws_items.cell(row=row_idx, column=6, value=float(comp.unit_cost) if comp.unit_cost else None)
        ws_items.cell(row=row_idx, column=7, value=float(comp.total_amount))
        ws_items.cell(row=row_idx, column=8, value=comp.source)
        ws_items.cell(row=row_idx, column=9, value=comp.formula or "")

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def export_estimate_pdf(estimate: EstimateResponse, project_name: str = "Project") -> bytes:
    """Generate a clean, professional PDF executive estimation brief."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    story = []

    # Title
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
    )
    story.append(Paragraph(f"Software Cost & Effort Estimate: {project_name}", title_style))
    story.append(Spacer(1, 10))

    meta_text = (
        f"<b>Version:</b> v{estimate.version} | "
        f"<b>Method:</b> {estimate.estimation_method or 'Hybrid Ensemble'} | "
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
    )
    story.append(Paragraph(meta_text, styles["Normal"]))
    story.append(Spacer(1, 15))

    # Executive Summary Paragraph
    if estimate.recommendation:
        story.append(Paragraph("<b>Executive Summary & Advisory:</b>", styles["Heading3"]))
        story.append(Paragraph(estimate.recommendation, styles["Normal"]))
        story.append(Spacer(1, 15))

    # Cost Breakdown Table
    story.append(Paragraph("<b>Cost Breakdown by Category</b>", styles["Heading3"]))
    cb = estimate.cost_breakdown

    table_data = [
        ["Category", "Allocated Budget ($)", "% of Total"],
        ["Personnel Labor", f"${cb.personnel:,.2f}", f"{(float(cb.personnel) / float(cb.total) * 100):.1f}%" if cb.total > 0 else "0%"],
        ["Tooling & Software SaaS", f"${cb.tooling:,.2f}", f"{(float(cb.tooling) / float(cb.total) * 100):.1f}%" if cb.total > 0 else "0%"],
        ["Cloud Infrastructure", f"${cb.cloud:,.2f}", f"{(float(cb.cloud) / float(cb.total) * 100):.1f}%" if cb.total > 0 else "0%"],
        ["Contingency Buffer (15%)", f"${cb.contingency:,.2f}", f"{(float(cb.contingency) / float(cb.total) * 100):.1f}%" if cb.total > 0 else "0%"],
        ["TOTAL ESTIMATED BUDGET", f"${cb.total:,.2f}", "100.0%"],
    ]

    t = Table(table_data, colWidths=[200, 160, 120])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F2F4F8")),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Uncertainty Table
    if estimate.uncertainty:
        story.append(Paragraph("<b>Uncertainty Quantification (Monte Carlo Simulation)</b>", styles["Heading3"]))
        u = estimate.uncertainty
        unc_data = [
            ["Confidence Metric", "Simulated Budget ($)", "Interpretation"],
            ["P50 (Median)", f"${u.p50:,.2f}" if u.p50 else "N/A", "50% likelihood budget is sufficient"],
            ["P80 (Recommended Baseline)", f"${u.p80:,.2f}" if u.p80 else "N/A", "80% confidence standard executive reserve"],
            ["P90 (Conservative)", f"${u.p90:,.2f}" if u.p90 else "N/A", "High-risk mitigation upper bound"],
        ]
        ut = Table(unc_data, colWidths=[180, 150, 150])
        ut.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B4C7E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ]))
        story.append(ut)

    doc.build(story)
    return buffer.getvalue()
