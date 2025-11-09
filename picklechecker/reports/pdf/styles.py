"""
Module for defining styles and colors used in PDF reports.
"""

from typing import Dict, Tuple

from reportlab.lib import colors  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1  # type: ignore


class PdfStyles:
    """
    Class for creating and managing PDF styles and colors.
    """

    @classmethod
    def create_styles(
        cls,
    ) -> Tuple[StyleSheet1, Dict[str, ParagraphStyle], Dict[str, colors.Color]]:
        """
        Creates and returns all styles and colors for the PDF report.

        Returns:
            Tuple[StyleSheet1, Dict[str, ParagraphStyle], Dict[str, colors.Color]]:
            Base styles, custom paragraph styles, and custom colors.
        """
        base_styles = getSampleStyleSheet()

        # Define base styles to reduce duplication
        simple_base = ParagraphStyle(
            "SimpleBase",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
        )
        bold_base = ParagraphStyle(
            "BoldBase",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
        )
        details_base = ParagraphStyle("DetailsBase", parent=base_styles["Normal"], fontSize=9)

        custom_styles = {
            # Large title for the main header block
            "title_large": ParagraphStyle(
                "TitleLarge",
                parent=base_styles["Title"],
                alignment=1,
                textColor=colors.white,
                fontSize=36,
                leading=42,
            ),
            # Target display (e.g., file or directory path)
            "target": ParagraphStyle(
                "Target",
                parent=base_styles["Normal"],
                alignment=1,
                fontSize=16,
                textColor=colors.HexColor("#222222"),
                leading=20,
            ),
            # Metadata like generation date
            "meta": ParagraphStyle(
                "Meta", parent=base_styles["Normal"], fontSize=9, textColor=colors.grey, alignment=1
            ),
            # Simple key text (non-bold)
            "key_simple": simple_base,
            # Bold key text
            "key_bold": bold_base,
            # Value alignments (left, center, right)
            "value_left": ParagraphStyle("ValueLeft", parent=simple_base, alignment=0),
            "value_center": ParagraphStyle("ValueCenter", parent=simple_base, alignment=1),
            "value_right": ParagraphStyle("ValueRight", parent=simple_base, alignment=2),
            # Bold value alignments
            "value_bold_left": ParagraphStyle("ValueBoldLeft", parent=bold_base, alignment=0),
            "value_bold_center": ParagraphStyle("ValueBoldCenter", parent=bold_base, alignment=1),
            "value_bold_right": ParagraphStyle("ValueBoldRight", parent=bold_base, alignment=2),
            # Title for individual file sections
            "file_title": ParagraphStyle(
                "FileTitle",
                parent=base_styles["Title"],
                fontSize=18,
                alignment=0,
                leading=22,
                spaceBefore=6,
                spaceAfter=6,
            ),
            # Header for blocks or sections
            "block_header": ParagraphStyle(
                "BlockHeader", parent=base_styles["Normal"], fontName="Helvetica-Bold", fontSize=11
            ),
            # Details field with indentation
            "details_field": ParagraphStyle("DetailsField", parent=details_base, leftIndent=4),
            # Details value without indentation
            "details_value": details_base,
        }

        custom_colors = {
            # Colors for safe status headers and values
            "header_safe": colors.HexColor("#4EA24E"),
            "value_safe": colors.HexColor("#E1F3E1"),
            # Colors for suspicious status headers and values
            "header_susp": colors.HexColor("#E0C93A"),
            "value_susp": colors.HexColor("#FFF8D6"),
            # Colors for dangerous status headers and values
            "header_dang": colors.HexColor("#E24A3F"),
            "value_dang": colors.HexColor("#FFE3E2"),
            # Underline color for tables
            "underline": colors.HexColor("#EEEEEE"),
            # Background color for headers
            "header_bg": colors.HexColor("#F5F5F5"),
            # Grid color for tables
            "grid": colors.HexColor("#DDDDDD"),
            # Background color for the title block
            "title_bg": colors.HexColor("#222222"),
        }

        return base_styles, custom_styles, custom_colors
