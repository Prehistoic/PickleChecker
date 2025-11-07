from typing import Dict, Tuple

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, StyleSheet1

class PdfStyles():

    @classmethod
    def create_styles(cls) -> Tuple[StyleSheet1, Dict[str, ParagraphStyle], Dict[str, colors.Color]]:
        """Creates and returns all styles and colors for the PDF report."""
        base_styles = getSampleStyleSheet()
        
        custom_styles = {
            "title_large": ParagraphStyle(
                "TitleLarge", parent=base_styles["Title"], alignment=1,
                textColor=colors.white, fontSize=36, leading=42
            ),
            "target": ParagraphStyle(
                "Target", parent=base_styles["Normal"], alignment=1, fontSize=16,
                textColor=colors.HexColor("#222222"), leading=20
            ),
            "meta": ParagraphStyle(
                "Meta", parent=base_styles["Normal"], fontSize=9,
                textColor=colors.grey, alignment=1
            ),
            "left_key_bold": ParagraphStyle(
                "LeftKeyBold", parent=base_styles["Normal"],
                fontName="Helvetica-Bold", fontSize=11, leading=14
            ),
            "value_bold_center": ParagraphStyle(
                "ValueBoldCenter", parent=base_styles["Normal"],
                fontName="Helvetica-Bold", fontSize=11, alignment=1, leading=14
            ),
            "value_bold_left": ParagraphStyle(
                "ValueBoldLeft", parent=base_styles["Normal"],
                fontName="Helvetica-Bold", fontSize=11, alignment=0, leading=14
            ),
            "file_title": ParagraphStyle(
                "FileTitle", parent=base_styles["Title"], fontSize=18,
                alignment=0, leading=22, spaceBefore=6, spaceAfter=6
            ),
            "block_header": ParagraphStyle(
                "BlockHeader", parent=base_styles["Normal"],
                fontName="Helvetica-Bold", fontSize=11
            ),
            "details_field": ParagraphStyle(
                'Field', parent=base_styles['Normal'], fontSize=9, leftIndent=4
            ),
            "details_value": ParagraphStyle(
                'Value', parent=base_styles['Normal'], fontSize=9
            )
        }

        custom_colors = {
            "header_safe": colors.HexColor("#4EA24E"),
            "value_safe": colors.HexColor("#E1F3E1"),
            "header_susp": colors.HexColor("#E0C93A"),
            "value_susp": colors.HexColor("#FFF8D6"),
            "header_mal": colors.HexColor("#E24A3F"),
            "value_mal": colors.HexColor("#FFE3E2"),
            "header_failed": colors.HexColor("#9E9E9E"),
            "value_failed": colors.HexColor("#F0F0F0"),
            "underline": colors.HexColor("#EEEEEE"),
            "header_bg": colors.HexColor("#F5F5F5"),
            "grid": colors.HexColor("#DDDDDD"),
            "title_bg": colors.HexColor("#222222"),
        }

        return base_styles, custom_styles, custom_colors