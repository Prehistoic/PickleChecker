from typing import List
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from reports import Report
from reports.pdf_report.styles import PdfStyles
from reports.pdf_report.cover import PdfCover
from reports.pdf_report.details import PdfDetails

from utils.pickle_helper import PickleAnalysis
from utils.scanners_helper import ScanResult

class PdfReport(Report):

    format = "pdf"

    def _create_report(self, target: str | None, target_type: str | None, scanner_results: List[ScanResult], pickle_analyses: List[PickleAnalysis]) -> Path:
        # Document setup
        doc = SimpleDocTemplate(
            str(self.output_filepath),
            pagesize=A4,
            rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72
        )

        # Get all styles
        base_styles, custom_styles, custom_colors = PdfStyles.create_styles()
        
        story = []

        # --- Build First Page ---
        story.extend(PdfCover.build_cover(
            doc, custom_styles, custom_colors,
            target, target_type, scanner_results
        ))

        # --- Build Detail Pages ---
        story.extend(PdfDetails.build_detail_pages(
            doc, custom_styles, custom_colors,
            scanner_results, pickle_analyses
        ))

        # Build PDF
        doc.build(story)
        self.logger.debug("PDF export completed successfully")