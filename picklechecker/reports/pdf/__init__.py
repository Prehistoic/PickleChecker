"""
PDF report generation module.
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4  # type: ignore
from reportlab.platypus import SimpleDocTemplate  # type: ignore

from picklechecker.reports import Report
from picklechecker.reports.pdf.styles import PdfStyles
from picklechecker.reports.pdf.cover import PdfCover
from picklechecker.reports.pdf.details import PdfDetails


class PdfReport(Report):
    """
    Class for generating PDF reports from pickle scan results.
    """

    format = "pdf"

    def save(self, output_filepath: str | Path):
        """
        Saves the scan results to a PDF file.

        Args:
            output_filepath (str | Path): The path where the PDF will be saved.
        """
        # Document setup with A4 page size and margins
        doc = SimpleDocTemplate(
            str(output_filepath),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Retrieve styles and colors for the PDF
        base_styles, custom_styles, custom_colors = PdfStyles.create_styles()

        story = []

        # Build the cover page with summary information
        story.extend(
            PdfCover.build_cover(
                doc, custom_styles, custom_colors, self.target, self.target_type, self.results
            )
        )

        # Build detail pages for individual file results
        story.extend(PdfDetails.build_detail_pages(
            doc, custom_styles, custom_colors,
            self.results
        ))

        # Generate the PDF document
        doc.build(story)
        self.logger.debug(f"{self.format.upper()} export completed successfully")
