from typing import List, Dict
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Flowable,
    PageBreak,
)

from picklechecker.reports.pdf.icons import PdfIcons
from picklechecker.core.results import AnalysisResult, AnalysisStatus
from picklechecker.core.safety import SafetyLevel


class PdfCover:
    @classmethod
    def build_cover(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        target: str | None,
        target_type: str | None,
        results: List[AnalysisResult],
    ) -> List[Flowable]:
        """Builds the cover page flowables, including title, target, and summary."""
        story = []

        # Big black-grey block with project name
        block = Table(
            [[Paragraph("PICKLECHECKER", custom_styles["title_large"])]],
            colWidths=[doc.width],
            rowHeights=[doc.height * 0.25],
        )
        block.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), custom_colors["title_bg"]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(block)
        story.append(Spacer(1, 18))

        # Generated on (centered small)
        story.append(
            Paragraph(
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                custom_styles["meta"],
            )
        )
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
        total_files = len({r.source_path for r in results})
        completed_scans = sum(1 for r in results if r.status == AnalysisStatus.COMPLETED)
        partial_scans = sum(1 for r in results if r.status == AnalysisStatus.COMPLETED_WITH_ERRORS)
        failed_scans = sum(1 for r in results if r.status == AnalysisStatus.FAILED)
        safe = sum(1 for r in results if r.safety == SafetyLevel.INNOCUOUS)
        suspicious = sum(1 for r in results if r.safety == SafetyLevel.SUSPICIOUS)
        dangerous = sum(1 for r in results if r.safety == SafetyLevel.DANGEROUS)

        # Left key/value table (file counts)
        totals_rows = [
            [
                Paragraph("Total files scanned", custom_styles["key_bold"]),
                Paragraph(f"{total_files}", custom_styles["value_bold_right"]),
            ],
            [
                Paragraph("- Completed", custom_styles["key_simple"]),
                Paragraph(f"{completed_scans}", custom_styles["value_right"]),
            ],
            [
                Paragraph("- Completed with errors", custom_styles["key_simple"]),
                Paragraph(f"{partial_scans}", custom_styles["value_right"]),
            ],
            [
                Paragraph("- Failed", custom_styles["key_simple"]),
                Paragraph(f"{failed_scans}", custom_styles["value_right"]),
            ],
        ]
        totals_table = Table(totals_rows, colWidths=[200, 150])
        totals_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        # Wrap totals_table in a full-width table to center it on the page
        totals_wrapper = Table([[totals_table]], colWidths=[doc.width])
        totals_wrapper.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))

        story.append(totals_wrapper)
        story.append(Spacer(1, 30))

        # Status summary table (colored)
        safety_results_headers = [
            Paragraph("<b>Safe</b>", custom_styles["value_bold_center"]),
            Paragraph("<b>Suspicious</b>", custom_styles["value_bold_center"]),
            Paragraph("<b>Dangerous</b>", custom_styles["value_bold_center"]),
        ]
        safety_results_value = [
            Paragraph(f"<b>{safe}</b>", custom_styles["value_bold_center"]),
            Paragraph(f"<b>{suspicious}</b>", custom_styles["value_bold_center"]),
            Paragraph(f"<b>{dangerous}</b>", custom_styles["value_bold_center"]),
        ]
        safety_results_table = Table(
            [safety_results_headers, safety_results_value],
            colWidths=[doc.width / 4.0] * 4,
            hAlign="CENTER",
        )
        safety_results_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), custom_colors["header_safe"]),
                    ("BACKGROUND", (1, 0), (1, 0), custom_colors["header_susp"]),
                    ("BACKGROUND", (2, 0), (2, 0), custom_colors["header_dang"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, 1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("BACKGROUND", (0, 1), (0, 1), custom_colors["value_safe"]),
                    ("BACKGROUND", (1, 1), (1, 1), custom_colors["value_susp"]),
                    ("BACKGROUND", (2, 1), (2, 1), custom_colors["value_dang"]),
                ]
            )
        )
        story.append(safety_results_table)
        story.append(PageBreak())
        return story
