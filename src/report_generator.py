from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.config import REPORTS_DIR


def generate_executive_report(kpis: dict[str, object], recommendations: pd.DataFrame, model_outputs: dict[str, object]) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORTS_DIR / "executive_summary.md"
    dept_table = kpis["department_table"].head(10).copy()
    text = f"""# Executive Summary: Hospital Resource Reallocation & Capacity Optimization

## Business Problem
Hospital leadership needs to reduce avoidable patient waiting time, improve bed and ICU utilization, and reallocate scarce staff and diagnostic resources across departments without compromising care quality.

## Key Findings
- Total patient records analyzed: {kpis['total_patients']:,}
- Average wait time: {kpis['avg_wait_time']} minutes
- Average bed occupancy: {kpis['avg_bed_occupancy']}%
- Average ICU utilization: {kpis['avg_icu_utilization']}%
- 30-day readmission rate: {kpis['readmission_rate']}%
- Emergency cases represent {kpis['emergency_share']}% of patient volume
- Over-utilized departments: {', '.join(kpis['over_utilized_departments']) or 'None'}
- Under-utilized departments: {', '.join(kpis['under_utilized_departments']) or 'None'}

## Strategic Recommendations
"""
    for _, rec in recommendations.head(8).iterrows():
        text += f"- **{rec['priority']} | {rec['area']}**: {rec['recommendation']} {rec['estimated_impact']}\n"
    text += """
## Financial Impact Estimate
Reducing average wait time by 10-18% can improve throughput, reduce overtime, and recover capacity leakage. A conservative 5% reduction in avoidable length-of-stay pressure and diagnostic delays can create meaningful bed-day capacity without major capital expansion.

## Operating Model
Implement a weekly capacity control tower, flexible staffing pools, weekend surge protocols, and diagnostic slot governance. Refresh the model monthly with updated admissions, staffing, equipment, and discharge data.
"""
    md_path.write_text(text, encoding="utf-8")

    pdf_path = REPORTS_DIR / "executive_summary.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
    story = [
        Paragraph("Hospital Resource Reallocation & Capacity Optimization", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Executive Summary", styles["Heading2"]),
        Paragraph(
            f"Analyzed {kpis['total_patients']:,} patient encounters with average wait time of {kpis['avg_wait_time']} minutes, "
            f"bed occupancy of {kpis['avg_bed_occupancy']}%, and ICU utilization of {kpis['avg_icu_utilization']}%.",
            styles["BodyText"],
        ),
        Spacer(1, 12),
    ]
    table_data = [["Priority", "Area", "Recommendation", "Impact"]] + recommendations.head(6)[
        ["priority", "area", "recommendation", "estimated_impact"]
    ].values.tolist()
    table = Table(table_data, colWidths=[55, 75, 235, 155])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    return md_path
