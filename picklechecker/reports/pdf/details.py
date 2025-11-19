"""
Module for building the detail pages of PDF reports.
"""

from typing import List, Dict
from pathlib import Path

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


class PdfDetails:
    """
    Class for constructing the detail pages elements of a PDF report.
    """

    @classmethod
    def _build_status_block(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        result: AnalysisResult,
    ) -> List[Flowable]:
        """
        Builds the status block for a single file result.

        Displays the AnalysisStatus with color coding.
        If failed, shows errors below in a less prominent way.
        """
        block_story = []

        # Status color mapping
        status_colors = {
            AnalysisStatus.COMPLETED: custom_colors["header_safe"],
            AnalysisStatus.COMPLETED_WITH_ERRORS: custom_colors["header_susp"],
            AnalysisStatus.FAILED: custom_colors["header_dang"],
            AnalysisStatus.ONGOING: colors.grey,
        }
        status_color = status_colors.get(result.status, colors.black)

        # Status paragraph (not bold, smaller font)
        status_text = (
            f"Scan Status: <font color='{status_color}' size='10'>{result.status.name}</font>"
        )
        block_story.append(Paragraph(status_text, custom_styles["block_header"]))

        # If there was any, show errors
        if result.errors:
            block_story.append(Spacer(1, 6))
            error_text = "<br/>".join([f"<i> - {error}</i>" for error in result.errors])
            block_story.append(Paragraph(error_text, custom_styles["details_value"]))
            block_story.append(Spacer(1, 4))

        return block_story

    @classmethod
    def _build_safety_block(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        result: AnalysisResult,
    ) -> List[Flowable]:
        """
        Builds the safety level block for a single file result.

        Displays the SafetyLevel clearly with color.
        """
        block_story = []

        # Safety color mapping
        safety_colors = {
            SafetyLevel.INNOCUOUS: custom_colors["header_safe"],
            SafetyLevel.SUSPICIOUS: custom_colors["header_susp"],
            SafetyLevel.DANGEROUS: custom_colors["header_dang"],
            SafetyLevel.UNKNOWN: colors.grey,
        }
        safety_color = safety_colors.get(result.safety, colors.black)

        # Safety paragraph
        safety_text = (
            f"<b>Safety: <font color='{safety_color}' size='14'>{result.safety.name}</font></b>"
        )
        block_story.append(Paragraph(safety_text, custom_styles["block_header"]))

        return block_story

    @classmethod
    def _build_globals_table(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        result: AnalysisResult,
    ) -> List[Flowable]:
        """
        Builds the globals table for a single file result.

        Displays global imports and their safety levels in a colored table.
        """
        block_story = []

        if not result.globals_found:
            block_story.append(
                Paragraph("No global imports found.", custom_styles["details_value"])
            )
            return block_story

        # Table headers
        headers = [
            Paragraph("<b>Global Import</b>", custom_styles["key_bold"]),
            Paragraph("<b>Safety Level</b>", custom_styles["key_bold"]),
        ]

        # Table rows
        rows = [headers]
        for global_ref in result.globals_found:
            module_name = f"<b>{global_ref.module}.{global_ref.name}</b>"
            safety_color = {
                SafetyLevel.INNOCUOUS: custom_colors["header_safe"],
                SafetyLevel.SUSPICIOUS: custom_colors["header_susp"],
                SafetyLevel.DANGEROUS: custom_colors["header_dang"],
                SafetyLevel.UNKNOWN: colors.grey,
            }.get(global_ref.safety, colors.black)

            row = [
                Paragraph(module_name, custom_styles["details_field"]),
                Paragraph(
                    f"<b><font color='{safety_color}'>{global_ref.safety.name}</font></b>",
                    custom_styles["details_value"],
                ),
            ]
            rows.append(row)

        # Create table
        globals_table = Table(rows, colWidths=[doc.width * 0.7, doc.width * 0.3])
        globals_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, custom_colors["grid"]),
                    ("BACKGROUND", (0, 0), (-1, 0), custom_colors["header_bg"]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        block_story.append(globals_table)
        return block_story

    @classmethod
    def build_detail_pages(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        results: List[AnalysisResult],
    ) -> List[Flowable]:
        """
        Builds all the per-file detail pages from the list of AnalysisResult.

        Each result gets its own page with filename title, safety, status, and globals table.
        """
        story = []

        for result in results:
            # Page title: filename
            filename = str(result.source_path)
            story.append(Paragraph(filename, custom_styles["file_title"]))

            # Thin underline for separation
            underline = Table([[""]], colWidths=[doc.width], rowHeights=[1])
            underline.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), custom_colors["underline"]),
                    ]
                )
            )
            story.append(Spacer(1, 6))
            story.append(underline)
            story.append(Spacer(1, 12))

            # Safety block (moved first)
            story.extend(cls._build_safety_block(doc, custom_styles, custom_colors, result))
            story.append(Spacer(1, 18))

            # Status block (moved after safety)
            story.extend(cls._build_status_block(doc, custom_styles, custom_colors, result))
            story.append(Spacer(1, 18))

            # Globals table
            story.extend(cls._build_globals_table(doc, custom_styles, custom_colors, result))

            # Page break after each file
            story.append(PageBreak())

        return story
