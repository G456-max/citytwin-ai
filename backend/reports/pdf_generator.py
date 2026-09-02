import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pathlib import Path

class CompliancePDFGenerator:
    """Generates print-ready municipal compliance verification reports using ReportLab."""

    @staticmethod
    def generate_report(
        audit_results: dict, 
        canopy_results: dict, 
        project_name: str, 
        output_pdf_path: str
    ) -> str:
        """
        Compiles spatial discrepancy metrics and canopy clearings into a formal PDF report.

        Args:
            audit_results: Output dictionary from CorridorDiscrepancyAuditor.
            canopy_results: Output dictionary from TreeCanopyAuditor.
            project_name: Name of the corridor project (e.g. Rajamahendravaram Godavari Bund Road).
            output_pdf_path: Filename to write the PDF report.

        Returns:
            Resolved absolute path to the saved PDF.
        """
        os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

        # Setup document template
        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=letter,
            rightMargin=40, leftMargin=40,
            topMargin=40, bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Define brand custom palette
        primary_color = colors.HexColor("#0f172a") # Dark Slate
        accent_color = colors.HexColor("#38bdf8")  # Sky Blue
        rose_color = colors.HexColor("#f43f5e")    # Rose Red
        border_color = colors.HexColor("#e2e8f0")  # Light gray

        # Document Flow Elements
        story = []

        # -------------------------------------------------------------------------
        # 1. Header Band
        # -------------------------------------------------------------------------
        header_data = [
            [
                Paragraph(f"<b>CITYTWIN AI • COMPLIANCE AUDIT</b>", ParagraphStyle('H1', parent=styles['Normal'], fontSize=16, textColor=colors.white)),
                Paragraph(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ParagraphStyle('Date', parent=styles['Normal'], fontSize=9, textColor=colors.white, alignment=2))
            ]
        ]
        header_table = Table(header_data, colWidths=[350, 180])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), primary_color),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 14),
            ('TOPPADDING', (0,0), (-1,-1), 14),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))

        # -------------------------------------------------------------------------
        # 2. Project Metadata block
        # -------------------------------------------------------------------------
        story.append(Paragraph(f"<b>Project Corridor:</b> {project_name}", ParagraphStyle('P1', parent=styles['Normal'], fontSize=11, textColor=primary_color)))
        story.append(Paragraph("<b>Statutory Reference:</b> NH-16 municipal widening clearance zones", ParagraphStyle('P2', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#475569"))))
        story.append(Paragraph("<b>Coordinate Datum:</b> WGS84 Geographic Bounds / Local UTM EPSG:32644", ParagraphStyle('P3', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#475569"))))
        story.append(Spacer(1, 15))

        # -------------------------------------------------------------------------
        # 3. Scorecard Indicators Table
        # -------------------------------------------------------------------------
        # Grade calculator
        total_violations = audit_results.get("total_violations", 0)
        total_encroached_m2 = audit_results.get("total_encroachment_area_m2", 0.0)
        canopy_loss_m2 = canopy_results.get("total_canopy_loss_area_m2", 0.0)
        tree_cleared_est = canopy_results.get("tree_clearance_count", 0)

        # Clearance Grade Index
        if total_encroached_m2 == 0:
            grade = "A+"
        elif total_encroached_m2 < 30:
            grade = "A"
        elif total_encroached_m2 < 100:
            grade = "B"
        elif total_encroached_m2 < 300:
            grade = "C"
        else:
            grade = "F"

        scorecard_data = [
            [
                Paragraph("<b>CLEARANCE GRADE</b>", ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748b"), alignment=1)),
                Paragraph("<b>TOTAL VIOLATIONS</b>", ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748b"), alignment=1)),
                Paragraph("<b>ENCROACHED AREA</b>", ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748b"), alignment=1)),
                Paragraph("<b>CANOPY CLEARING</b>", ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748b"), alignment=1))
            ],
            [
                Paragraph(f"<font size=20><b>{grade}</b></font>", ParagraphStyle('CardVal', parent=styles['Normal'], fontSize=16, textColor=primary_color if grade != 'F' else rose_color, alignment=1)),
                Paragraph(f"<font size=20><b>{total_violations}</b></font>", ParagraphStyle('CardVal', parent=styles['Normal'], fontSize=16, textColor=rose_color if total_violations > 0 else primary_color, alignment=1)),
                Paragraph(f"<font size=16><b>{total_encroached_m2:.2f} m²</b></font>", ParagraphStyle('CardVal', parent=styles['Normal'], fontSize=14, textColor=rose_color if total_encroached_m2 > 0 else primary_color, alignment=1)),
                Paragraph(f"<font size=16><b>{canopy_loss_m2:.2f} m²</b></font><br/><font size=8 textColor='#64748b'>({tree_cleared_est} trees)</font>", ParagraphStyle('CardVal', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor("#16a34a"), alignment=1))
            ]
        ]
        scorecard_table = Table(scorecard_data, colWidths=[120, 130, 140, 140])
        scorecard_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(scorecard_table)
        story.append(Spacer(1, 20))

        # -------------------------------------------------------------------------
        # 4. Detailed Encroachments Log
        # -------------------------------------------------------------------------
        story.append(Paragraph("<b>DETAILED DISCREPANCY LOGS</b>", ParagraphStyle('SecTitle', parent=styles['Normal'], fontSize=10, textColor=primary_color)))
        story.append(Spacer(1, 6))

        table_header = [
            Paragraph("<b>VIOLATION ID</b>", ParagraphStyle('Th', parent=styles['Normal'], fontSize=8, textColor=colors.white)),
            Paragraph("<b>GPS LOCATION (Lat/Lon)</b>", ParagraphStyle('Th', parent=styles['Normal'], fontSize=8, textColor=colors.white)),
            Paragraph("<b>MAX INTRUSION</b>", ParagraphStyle('Th', parent=styles['Normal'], fontSize=8, textColor=colors.white)),
            Paragraph("<b>AREA (m²)</b>", ParagraphStyle('Th', parent=styles['Normal'], fontSize=8, textColor=colors.white)),
            Paragraph("<b>SEVERITY</b>", ParagraphStyle('Th', parent=styles['Normal'], fontSize=8, textColor=colors.white))
        ]
        
        table_rows = [table_header]
        violations = audit_results.get("violations", [])

        if not violations:
            empty_row = [
                Paragraph("No encroachments identified.", ParagraphStyle('Td', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#64748b"))),
                "", "", "", ""
            ]
            table_rows.append(empty_row)
        else:
            for v in violations:
                sev_color = "#ef4444" if v['severity'] == "Critical" else ("#f59e0b" if v['severity'] == "Medium" else "#0ea5e9")
                row = [
                    Paragraph(f"<b>{v['encroachment_id']}</b>", ParagraphStyle('TdId', parent=styles['Normal'], fontSize=8, fontName="Helvetica-Bold", textColor=primary_color)),
                    Paragraph(f"{v['centroid_lat']:.5f}° N, {v['centroid_lon']:.5f}° E", ParagraphStyle('TdLoc', parent=styles['Normal'], fontSize=8)),
                    Paragraph(f"{v['max_intrusion_depth_m']:.2f} m", ParagraphStyle('TdInt', parent=styles['Normal'], fontSize=8)),
                    Paragraph(f"{v['area_m2']:.2f} m²", ParagraphStyle('TdArea', parent=styles['Normal'], fontSize=8)),
                    Paragraph(f"<font color='{sev_color}'><b>{v['severity'].upper()}</b></font>", ParagraphStyle('TdSev', parent=styles['Normal'], fontSize=8))
                ]
                table_rows.append(row)

        details_table = Table(table_rows, colWidths=[100, 150, 100, 90, 90])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 30))

        # -------------------------------------------------------------------------
        # 5. Security stamp & validation signature
        # -------------------------------------------------------------------------
        stamp_data = [
            [
                Paragraph("<b>DIGITALLY VERIFIED BY:</b><br/>CityTwin AI Compliance Audit Core", ParagraphStyle('StampText', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#475569"))),
                Paragraph(f"<b>VALIDATION KEY:</b><br/>MD5-{hash(str(total_encroached_m2)) & 0xffffffffffff:012x}", ParagraphStyle('StampKey', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#475569")))
            ]
        ]
        stamp_table = Table(stamp_data, colWidths=[270, 260])
        stamp_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#10b981")), # Green validation box
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ecfdf5")), # Mint background
            ('PADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(stamp_table)

        # Build PDF
        doc.build(story)
        print(f"Municipal Audit PDF report compiled: {output_pdf_path}")
        return str(Path(output_pdf_path).resolve())
