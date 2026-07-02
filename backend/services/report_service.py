"""
Mentora – PDF Report Service
Generates a clean session report PDF using ReportLab.
"""

import io
import time
import logging

logger = logging.getLogger(__name__)


def build_pdf_report(report: dict) -> bytes:
    """Returns PDF bytes for the given report dict."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )

        buf    = io.BytesIO()
        doc    = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
                                   topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        story  = []

        # ── Header ────────────────────────────────────────────────────────────
        title_style = ParagraphStyle("title", parent=styles["Title"],
                                     fontSize=22, textColor=colors.HexColor("#6C63FF"),
                                     spaceAfter=4)
        story.append(Paragraph("Mentora – Session Report", title_style))
        story.append(Paragraph(
            f"Generated: {time.strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#6C63FF")))
        story.append(Spacer(1, 6*mm))

        # ── Session info ──────────────────────────────────────────────────────
        session   = report.get("session", {})
        analytics = report.get("analytics", {})

        started = time.strftime("%Y-%m-%d %H:%M:%S",
                                time.localtime(session.get("started_at", 0)))
        session_data = [
            ["Session ID",        session.get("session_id", "N/A")[:16] + "…"],
            ["Started",           started],
            ["Duration",          f"{analytics.get('duration_minutes', 0)} min"],
            ["Frames Analysed",   str(analytics.get("total_frames", 0))],
        ]
        t = Table(session_data, colWidths=[55*mm, 110*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0EEFF")),
            ("FONTNAME",   (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE",   (0, 0), (-1, -1), 10),
            ("GRID",       (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1),
             [colors.whitesmoke, colors.white]),
        ]))
        story.append(t)
        story.append(Spacer(1, 6*mm))

        # ── Analytics ─────────────────────────────────────────────────────────
        story.append(Paragraph("Analytics Summary", styles["Heading2"]))
        analytics_data = [
            ["Metric",            "Value"],
            ["Average Fatigue",   f"{analytics.get('avg_fatigue_score', 0)}/100"],
            ["Peak Fatigue",      f"{analytics.get('peak_fatigue_score', 0)}/100"],
            ["Normal Time",       f"{analytics.get('state_distribution', {}).get('Normal', 0)} frames"],
            ["Stressed Time",     f"{analytics.get('state_distribution', {}).get('Stressed', 0)} frames"],
            ["Fatigued Time",     f"{analytics.get('state_distribution', {}).get('Fatigued', 0)} frames"],
        ]
        t2 = Table(analytics_data, colWidths=[80*mm, 85*mm])
        t2.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#6C63FF")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 0), (-1, -1), 10),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F9F9F9")]),
        ]))
        story.append(t2)
        story.append(Spacer(1, 6*mm))

        # ── Recommendations ───────────────────────────────────────────────────
        avg = analytics.get("avg_fatigue_score", 0)
        story.append(Paragraph("Recommendations", styles["Heading2"]))
        if avg >= 65:
            rec = ("High fatigue detected. Consider longer breaks (15–20 min), "
                   "improve sleep hygiene, and consult an occupational health professional "
                   "if this pattern persists.")
        elif avg >= 35:
            rec = ("Moderate fatigue/stress detected. Apply the Pomodoro technique "
                   "(25-min focus + 5-min break), stay hydrated, and practice "
                   "4-7-8 breathing during breaks.")
        else:
            rec = ("Cognitive load appears well-managed. Keep up your current "
                   "routine and maintain regular short breaks every 45–60 minutes.")
        story.append(Paragraph(rec, styles["Normal"]))

        # ── Footer ────────────────────────────────────────────────────────────
        story.append(Spacer(1, 10*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Paragraph(
            "Mentora – Cognitive Fatigue & Well-Being Tracker | For informational purposes only.",
            ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey)
        ))

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        logger.warning("ReportLab not installed – returning stub PDF bytes.")
        return b"%PDF-1.4 stub"
