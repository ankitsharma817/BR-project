"""
Generate a PDF report for a matching result.
Uses reportlab — install: pip install reportlab
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Wedge, String
from reportlab.graphics import renderPDF

from ...models.matching import MatchingResult, MatchAnalysis
from ...models.proposal import Proposal

LABEL_COLORS = {
    "strong_match": colors.HexColor("#52c41a"),
    "partial_match": colors.HexColor("#faad14"),
    "gap_identified": colors.HexColor("#fa8c16"),
    "missing": colors.HexColor("#f5222d"),
}
LABEL_TEXT = {
    "strong_match": "✓ Strong Match",
    "partial_match": "~ Partial Match",
    "gap_identified": "! Gap Identified",
    "missing": "✗ Missing",
}


def _score_to_color(score: float) -> colors.Color:
    if score >= 0.80: return colors.HexColor("#52c41a")
    if score >= 0.60: return colors.HexColor("#faad14")
    if score >= 0.30: return colors.HexColor("#fa8c16")
    return colors.HexColor("#f5222d")


def generate_match_pdf(
    proposal: Proposal,
    result: MatchingResult,
    analysis: MatchAnalysis | None,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=18, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=4)
    h3 = ParagraphStyle("h3", parent=styles["Heading3"], fontSize=11, spaceBefore=8, spaceAfter=2)
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=9, textColor=colors.grey)

    story = []

    # ── Header ──────────────────────────────────────────────────────────────────
    story.append(Paragraph("BR Matching Analysis Report", title_style))
    story.append(Paragraph(f"Vendor: <b>{proposal.vendor_name}</b>", body))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", small))
    story.append(Paragraph(f"Report Version: {result.version}", small))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1677ff"), spaceAfter=12))

    # ── Overall score ────────────────────────────────────────────────────────────
    pct = round(result.overall_score * 100, 1)
    story.append(Paragraph("Overall Match Score", h2))
    score_color = _score_to_color(result.overall_score)
    story.append(Paragraph(
        f'<font size="28" color="{score_color.hexval()}"><b>{pct}%</b></font>',
        ParagraphStyle("big", parent=body, alignment=1),
    ))
    if result.executive_summary:
        story.append(Spacer(1, 6))
        story.append(Paragraph(result.executive_summary, body))

    # ── Category scores table ────────────────────────────────────────────────────
    story.append(Paragraph("Category Scores", h2))
    cat_data = [["Category", "Score", "Status"]]
    cats = [
        ("Functional", result.functional_score),
        ("Technical", result.technical_score),
        ("Compliance", result.compliance_score),
        ("Security", result.security_score),
        ("Timeline", result.timeline_score),
        ("Resource", result.resource_score),
        ("Deliverables", result.deliverables_score),
    ]
    for name, score in cats:
        if score is None:
            continue
        s_pct = f"{round(score * 100, 1)}%"
        status = "Strong" if score >= 0.8 else "Partial" if score >= 0.6 else "Weak"
        cat_data.append([name, s_pct, status])

    cat_table = Table(cat_data, colWidths=[80 * mm, 40 * mm, 50 * mm])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1677ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f2f5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9d9d9")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(cat_table)

    # ── Analysis ─────────────────────────────────────────────────────────────────
    if analysis:
        if analysis.risks:
            story.append(Paragraph("Risks", h2))
            for r in analysis.risks:
                level = r.get("level", "").upper() if isinstance(r, dict) else r.level.upper()
                desc = r.get("description", "") if isinstance(r, dict) else r.description
                story.append(Paragraph(f"<b>[{level}]</b> {desc}", body))

        if analysis.recommendations:
            story.append(Paragraph("Recommendations", h2))
            for rec in analysis.recommendations:
                prio = rec.get("priority", "") if isinstance(rec, dict) else rec.priority
                action = rec.get("action", "") if isinstance(rec, dict) else rec.action
                story.append(Paragraph(f"<b>{prio}:</b> {action}", body))

        if analysis.gaps:
            story.append(Paragraph("Identified Gaps", h2))
            for g in (analysis.gaps or []):
                story.append(Paragraph(f"• {g}", body))

    # ── Requirement-by-requirement ────────────────────────────────────────────────
    if result.requirement_matchings:
        story.append(Paragraph("Requirement Breakdown", h2))
        req_data = [["Requirement", "Category", "Score", "Status"]]
        for rm in result.requirement_matchings:
            br = rm.br_requirement
            req_text = (br.text[:80] + "…") if br and len(br.text) > 80 else (br.text if br else "")
            score_pct = f"{round(rm.score * 100)}%"
            req_data.append([req_text, br.category if br else "", score_pct, LABEL_TEXT.get(rm.label, rm.label)])

        req_table = Table(req_data, colWidths=[90 * mm, 30 * mm, 20 * mm, 35 * mm])
        req_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1677ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f2f5")]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d9d9d9")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("WORDWRAP", (0, 1), (0, -1), True),
        ]))
        story.append(req_table)

    doc.build(story)
    return buf.getvalue()
