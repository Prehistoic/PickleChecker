from typing import List, Dict
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, PageBreak

from reports.pdf_report.icons import PdfIcons
from utils.scanners_helper import ScanResult
from config import PROJECT_NAME

class PdfCover:

    @classmethod
    def build_cover(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        target: str | None,
        target_type: str | None,
        scanner_results: List[ScanResult]
    ) -> List[Flowable]:
        """Builds the cover page flowables, including title, target, and summary."""
        story = []
        
        # Big black-grey block with project name
        block = Table(
            [[Paragraph(PROJECT_NAME.upper(), custom_styles["title_large"])]],
            colWidths=[doc.width],
            rowHeights=[doc.height * 0.25]
        )
        block.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), custom_colors["title_bg"]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(block)
        story.append(Spacer(1, 18))

        # Generated on (centered small)
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", custom_styles["meta"]))
        story.append(Spacer(1, 30))

        # Draw icon
        if target_type in ("dir", "file", "hf"):
            icon = PdfIcons(target_type, size=36)
            icon_table = Table([[icon]], colWidths=[doc.width])
            icon_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            story.append(icon_table)
            story.append(Spacer(1, 8))

        # Format directory target to look nice
        display_target = target
        try:
            if target and target_type == "dir":
                p = Path(target)
                parts = [part for part in p.parts if part not in (".", "..")]
                display_target = "\\".join(parts) if parts else str(p)
        except Exception:
            display_target = target

        if display_target:
            story.append(Paragraph(f"<b>{display_target}</b>", custom_styles["target"]))

        story.append(Spacer(1, 60))

        # Build summary values
        total_files = len({r.filename for r in scanner_results})
        total_scans = len(scanner_results)
        safe = sum(1 for r in scanner_results if r.status.name == "LIKELY_SAFE")
        suspicious = sum(1 for r in scanner_results if r.status.name == "SUSPICIOUS")
        malicious = sum(1 for r in scanner_results if r.status.name == "OVERTLY_MALICIOUS")
        failed = sum(1 for r in scanner_results if r.status.name == "FAILED")

        # Left key/value table (file counts)
        left_rows = [
            [Paragraph("<b>Total files scanned</b>", custom_styles["left_key_bold"]), Paragraph(f"<b>{total_files}</b>", custom_styles["value_bold_left"])],
            [Paragraph("<b>Total scans performed</b>", custom_styles["left_key_bold"]), Paragraph(f"<b>{total_scans}</b>", custom_styles["value_bold_left"])]
        ]
        left_table = Table(left_rows, colWidths=[doc.width * 0.6, doc.width * 0.4], hAlign="LEFT")
        left_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(left_table)
        story.append(Spacer(1, 30))

        # Status summary table (colored)
        status_headers = [
            Paragraph("<b>Safe</b>", custom_styles["value_bold_center"]),
            Paragraph("<b>Suspicious</b>", custom_styles["value_bold_center"]),
            Paragraph("<b>Malicious</b>", custom_styles["value_bold_center"]),
            Paragraph("<b>Failed</b>", custom_styles["value_bold_center"])
        ]
        status_values = [
            Paragraph(f"<b>{safe}</b>", custom_styles["value_bold_center"]),
            Paragraph(f"<b>{suspicious}</b>", custom_styles["value_bold_center"]),
            Paragraph(f"<b>{malicious}</b>", custom_styles["value_bold_center"]),
            Paragraph(f"<b>{failed}</b>", custom_styles["value_bold_center"])
        ]
        status_table = Table([status_headers, status_values], colWidths=[doc.width / 4.0] * 4, hAlign="CENTER")
        status_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), custom_colors["header_safe"]),
            ("BACKGROUND", (1, 0), (1, 0), custom_colors["header_susp"]),
            ("BACKGROUND", (2, 0), (2, 0), custom_colors["header_mal"]),
            ("BACKGROUND", (3, 0), (3, 0), custom_colors["header_failed"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, 1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (0, 1), custom_colors["value_safe"]),
            ("BACKGROUND", (1, 1), (1, 1), custom_colors["value_susp"]),
            ("BACKGROUND", (2, 1), (2, 1), custom_colors["value_mal"]),
            ("BACKGROUND", (3, 1), (3, 1), custom_colors["value_failed"]),
        ]))
        story.append(status_table)
        story.append(PageBreak())
        return story