from typing import List, Dict
from pathlib import Path
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, PageBreak

from reports.pdf_report.icons import PdfIcons
from utils.scanners_helper import ScanResult
from utils.pickle_helper import PickleAnalysis

class PdfDetails:

    @classmethod
    def _build_scanner_results_block(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        results: List[ScanResult]
    ) -> List[Flowable]:
        """Builds the 'Scanner Results' block for a single file."""
        block_story = []
        
        # --- 1. Create the INNER table for the header (icon + title) ---
        gear = PdfIcons("gear", size=18)
        inner_data = [[gear, Spacer(6, 1), Paragraph("SCANNER RESULTS", custom_styles["block_header"])]]
        inner_table = Table(inner_data, colWidths=[18, 6, None]) # 18 for icon, 6 for spacer
        inner_table.width = '100%'
        inner_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        # --- 2. Create the OUTER table (the visible header bar) ---
        header_table = Table([[inner_table]], colWidths=[doc.width])
        header_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, custom_colors["grid"]),
            ("BACKGROUND", (0, 0), (-1, -1), custom_colors["header_bg"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        block_story.append(header_table)

        # --- 3. Build the content table with scanner results ---
        content_rows = []
        sev_map = {
            "LIKELY_SAFE": custom_colors["header_safe"],
            "SUSPICIOUS": custom_colors["header_susp"],
            "OVERTLY_MALICIOUS": custom_colors["header_mal"],
            "FAILED": custom_colors["header_failed"]
        }
        
        for res in results:
            sev_col = sev_map.get(res.status.name, colors.black)
            # Scanner line: "ScannerName -> STATUS"
            content_rows.append([Paragraph(
                f"<b>{res.scanner} → <font color='{sev_col}'><b>{res.status.name}</b></font></b>",
                custom_styles["details_field"]
            )])
            
            # Details table for this scanner result
            details = res.details or {}
            if details:
                det_rows = []
                for k, v in details.items():
                    # Format values for clean PDF display
                    if v is None:
                        display = "None"
                    elif isinstance(v, (list, tuple, set)):
                        items = "".join([f"- {str(item)}<br/>" for item in v])
                        display = items.lstrip("<br/>").lstrip()
                    else:
                        display = str(v).lstrip("\n").replace("\n", "<br/>").lstrip("<br/>")
                    
                    det_rows.append([
                        Paragraph(str(k), custom_styles["details_field"]),
                        Paragraph(display, custom_styles["details_value"])
                    ])
                
                # Use 100% width inner table to constrain it
                det_table = Table(det_rows, colWidths=['25%', '75%'])
                det_table.width = '100%' 
                det_table.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, custom_colors["grid"]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]))
                content_rows.append([det_table])
            else:
                content_rows.append([Paragraph("No details", custom_styles["details_value"])])

        content_table = Table(content_rows, colWidths=[doc.width])
        content_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, custom_colors["grid"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
        ]))
        block_story.append(content_table)
        return block_story

    @classmethod
    def _build_global_imports_block(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        filename: str,
        pickle_analyses: List[PickleAnalysis]
    ) -> List[Flowable]:
        """Builds the 'Global Imports' block for a single file."""
        block_story = []

        # --- 1. Create the INNER table for the header (icon + title) ---
        dl = PdfIcons("download", size=18)
        inner_data = [[dl, Spacer(6, 1), Paragraph("GLOBAL IMPORTS", custom_styles["block_header"])]]
        inner_table = Table(inner_data, colWidths=[18, 6, None]) # 18 for icon, 6 for spacer
        inner_table.width = '100%'
        inner_table.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        # --- 2. Create the OUTER table (the visible header bar) ---
        header_table = Table([[inner_table]], colWidths=[doc.width])
        header_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, custom_colors["grid"]),
            ("BACKGROUND", (0, 0), (-1, -1), custom_colors["header_bg"]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        block_story.append(header_table)
        
        # --- 3. Build the content table with import data ---
        imports_for_file = set()
        for pa in pickle_analyses:
            if Path(pa.filename).name == Path(filename).name:
                imports_for_file.update(pa.global_imports)

        if imports_for_file:
            imp_rows = [[Paragraph(imp, custom_styles["details_value"])] for imp in sorted(imports_for_file)]
            imports_content_table = Table(imp_rows, colWidths=[doc.width])
            imports_content_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, custom_colors["grid"]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.whitesmoke, colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
        else:
            # Create a table for "No imports" to match the box style
            imports_content_table = Table(
                [[Paragraph("No global imports found.", custom_styles["details_value"])]],
                colWidths=[doc.width]
            )
            imports_content_table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, custom_colors["grid"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
        
        block_story.append(imports_content_table)
        return block_story

    @classmethod
    def build_detail_pages(
        cls,
        doc: SimpleDocTemplate,
        custom_styles: Dict[str, ParagraphStyle],
        custom_colors: Dict[str, colors.Color],
        scanner_results: List[ScanResult],
        pickle_analyses: List[PickleAnalysis]
    ) -> List[Flowable]:
        """Builds all the per-file detail pages."""
        story = []
        
        # Group scanner results by filename
        grouped = defaultdict(list)
        for r in scanner_results:
            grouped[r.filename].append(r)

        underline_height = 1 

        for filename, results in grouped.items():
            # New page title (filename)
            story.append(Paragraph(Path(filename).name, custom_styles["file_title"]))
            
            # Thin underline
            underline = Table([[""]], colWidths=[doc.width], rowHeights=[underline_height])
            underline.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), custom_colors["underline"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))
            story.append(Spacer(1, 6))
            story.append(underline)
            story.append(Spacer(1, 12))

            # --- Scanner Results Block ---
            story.extend(cls._build_scanner_results_block(
                doc, custom_styles, custom_colors, results
            ))
            story.append(Spacer(1, 12))

            # --- Global Imports Block ---
            story.extend(cls._build_global_imports_block(
                doc, custom_styles, custom_colors, filename, pickle_analyses
            ))

            story.append(PageBreak())
        
        return story