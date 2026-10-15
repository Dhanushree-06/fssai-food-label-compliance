"""
ReportLab PDF Audit Report Generator
AI-Based Food Label Compliance Verification Platform
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from app.services.fssai_rules import FIELD_DEFINITIONS


class PDFReportGenerator:
    """Generates professional FSSAI Compliance Audit PDF reports using ReportLab."""

    @classmethod
    def generate_report(cls, scan_data, output_path):
        """
        Builds a multi-page PDF audit report for a food label verification scan.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1b5e20"),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#424242"),
            spaceAfter=12
        )
        heading2_style = ParagraphStyle(
            "Heading2Custom",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0d47a1"),
            spaceBefore=10,
            spaceAfter=6
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            fontName="Helvetica-Bold"
        )
        cell_text = ParagraphStyle(
            "CellText",
            parent=styles["Normal"],
            fontSize=8,
            leading=10
        )
        cell_evidence = ParagraphStyle(
            "CellEvidence",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#37474f")
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerStyle",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#616161")
        )

        elements = []

        # Header Title
        elements.append(Paragraph("AI-Based Food Label Compliance Verification Platform", title_style))
        elements.append(Paragraph("FSSAI Statutory Labelling & Display Regulations, 2020 — Audit Report", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2e7d32"), spaceAfter=10))

        # Metadata & Overview Box
        scan_id = scan_data.get("id", "N/A")
        prod_name = scan_data.get("product_name", "Packaged Food Product")
        scan_date = scan_data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
        score = scan_data.get("score", 0.0)
        status = scan_data.get("compliance_status", "UNKNOWN")

        # Status badge color
        status_colors = {
            "COMPLIANT": colors.HexColor("#2e7d32"),
            "NON_COMPLIANT": colors.HexColor("#c62828")
        }
        badge_color = status_colors.get(status, colors.HexColor("#424242"))

        status_cell = Paragraph(
            f"<b><font color='{badge_color.hexval()}'>{status.replace('_', ' ')} ({score}%)</font></b>",
            cell_bold
        )

        overview_data = [
            [
                Paragraph("<b>Audit Scan ID:</b>", cell_bold),
                Paragraph(f"#{scan_id}", cell_text),
                Paragraph("<b>Product Name:</b>", cell_bold),
                Paragraph(prod_name, cell_text)
            ],
            [
                Paragraph("<b>Audit Date:</b>", cell_bold),
                Paragraph(str(scan_date), cell_text),
                Paragraph("<b>Compliance Status:</b>", cell_bold),
                status_cell
            ],
            [
                Paragraph("<b>Evidence Coverage:</b>", cell_bold),
                Paragraph(f"{score}%", cell_text),
                Paragraph("<b>OCR Engine:</b>", cell_bold),
                Paragraph(scan_data.get("ocr_engine", "Unified Multi-Tier Engine"), cell_text)
            ]
        ]

        overview_table = Table(overview_data, colWidths=[90, 175, 110, 165])
        overview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cfd8dc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#eceff1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(overview_table)
        elements.append(Spacer(1, 10))

        # Status Counters
        counts = scan_data.get("status_counts", {})
        cnt_present = counts.get("PRESENT", 0)
        cnt_missing = counts.get("MISSING", 0)

        counter_data = [[
            Paragraph(f"<font color='#2e7d32'><b>PRESENT: {cnt_present} / 14</b></font>", cell_bold),
            Paragraph(f"<font color='#c62828'><b>MISSING: {cnt_missing} / 14</b></font>", cell_bold),
        ]]
        counter_table = Table(counter_data, colWidths=[270, 270])
        counter_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(counter_table)
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            "MISSING means the declaration was not found in extracted OCR text; "
            "confirm it on the original package before treating it as physically absent.",
            cell_text
        ))
        elements.append(Spacer(1, 12))

        # 14 Mandatory Fields Breakdown Table
        elements.append(Paragraph("14 FSSAI Mandatory Fields Statutory Verification Breakdown", heading2_style))

        field_table_data = [[
            Paragraph("<b>#</b>", cell_bold),
            Paragraph("<b>Field Name</b>", cell_bold),
            Paragraph("<b>Weight</b>", cell_bold),
            Paragraph("<b>Status</b>", cell_bold),
            Paragraph("<b>Extracted Evidence & Finding</b>", cell_bold),
            Paragraph("<b>Action / Recommendation</b>", cell_bold)
        ]]

        field_results = scan_data.get("fields", {})
        idx = 1
        for field_key, defn in FIELD_DEFINITIONS.items():
            f_res = field_results.get(field_key, {})
            f_status = f_res.get("status", "MISSING")
            f_evidence = f_res.get("evidence", "No evidence extracted")
            f_recom = f_res.get("recommendation", "Review FSSAI 2020 requirements")
            weight = defn["weight"]

            f_status = "PRESENT" if f_status == "PRESENT" else "MISSING"
            st_color = "#2e7d32" if f_status == "PRESENT" else "#c62828"

            status_p = Paragraph(f"<b><font color='{st_color}'>{f_status}</font></b>", cell_bold)
            title_p = Paragraph(f"<b>{defn['title']}</b><br/><font size=6 color='#757575'>{defn['regulation'][:35]}...</font>", cell_text)
            evidence_p = Paragraph(f_evidence, cell_evidence)
            recom_p = Paragraph(f_recom, cell_evidence)

            field_table_data.append([
                Paragraph(str(idx), cell_text),
                title_p,
                Paragraph(f"{weight} pts", cell_text),
                status_p,
                evidence_p,
                recom_p
            ])
            idx += 1

        field_table = Table(
            field_table_data,
            colWidths=[18, 110, 42, 60, 160, 150],
            repeatRows=1
        )
        field_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263238")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (3, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8dc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(field_table)
        elements.append(Spacer(1, 14))

        # Legal Disclaimer Footer
        disclaimer_text = (
            "<b>STATUTORY DISCLAIMER:</b> This compliance report was generated algorithmically by the "
            "Food Label Compliance Verification Platform using computer vision and rule-based parsing. "
            "It is provided for advisory, screening, and guidance purposes only. This report DOES NOT constitute "
            "an official certification, endorsement, or approval by the Food Safety and Standards Authority of India (FSSAI) "
            "or any government agency. OCR can miss declarations; missing text therefore requires review of the original label. "
            "Definite compliance requires qualified statutory review under applicable law."
        )
        elements.append(KeepTogether([
            HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#b0bec5"), spaceAfter=6),
            Paragraph(disclaimer_text, disclaimer_style)
        ]))

        doc.build(elements)
        return output_path
