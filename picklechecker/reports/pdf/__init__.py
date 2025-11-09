from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from picklechecker.reports import Report
from picklechecker.reports.pdf.styles import PdfStyles
from picklechecker.reports.pdf.cover import PdfCover

# from picklechecker.reports.pdf.details import PdfDetails


class PdfReport(Report):
    format = "pdf"

    def save(self, output_filepath: str | Path):
        # Document setup
        doc = SimpleDocTemplate(
            str(output_filepath),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Get all styles
        base_styles, custom_styles, custom_colors = PdfStyles.create_styles()

        story = []

        # --- Build First Page ---
        story.extend(
            PdfCover.build_cover(
                doc, custom_styles, custom_colors, self.target, self.target_type, self.results
            )
        )

        # --- Build Detail Pages ---
        """story.extend(PdfDetails.build_detail_pages(
            doc, custom_styles, custom_colors,
            self.results
        ))"""

        # Build PDF
        doc.build(story)
        self.logger.debug(f"{self.format.upper()} export completed successfully")
