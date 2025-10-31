from typing import List
from pathlib import Path
from itertools import groupby
from operator import attrgetter

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from scanners import ScanResult, ScanStatus
from utils.logging_helper import get_logger

class ConsoleHelper:
    
    logger = get_logger(__name__)
    console = Console()

    @classmethod
    def _create_details_table(self, results: List[ScanResult]) -> Table:
        """
        Method to create the main table with scanner results details

        Args:
            results: List of ScanResult

        Returns:
            Table: rich Table object
        """
        table = Table(
            title="Pickle File Scan Results",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            show_lines=True
        )
        
        table.add_column("Scanner", style="green")
        table.add_column("Scanner Results")

        # Group results by filename
        sorted_results = sorted(results, key=attrgetter('filename'))
        grouped_results = groupby(sorted_results, key=attrgetter('filename'))

        # Status styling
        status_style = {
            ScanStatus.LIKELY_SAFE: "[green]SAFE[/green]",
            ScanStatus.SUSPICIOUS: "[yellow]SUSPICIOUS[/yellow]",
            ScanStatus.OVERTLY_MALICIOUS: "[red]MALICIOUS[/red]",
            ScanStatus.FAILED: "[red]FAILED[/red]"
        }

        # Add rows with nested scanner results
        for filename, group in grouped_results:
            # Create inner table for scanner results
            scanner_table = Table(
                box=box.SIMPLE,
                show_header=False,
                show_lines=False,
                pad_edge=True,
                padding=(0,1,1,0),
                collapse_padding=False
            )
            scanner_table.add_column("Scanner", style="blue")
            scanner_table.add_column("Status", style="bold")
            scanner_table.add_column("Details", style="grey70")

            # Add each scanner result as a row in the inner table
            for result in group:
                details_str = "\n".join(f"{k}: {v}" for k, v in result.details.items())
                scanner_table.add_row(
                    result.scanner,
                    status_style[result.status],
                    details_str or "No details available"
                )

            # Add the file and its nested scanner results to the main table
            table.add_row(
                Path(filename).name,  # Show only filename, not full path
                scanner_table
            )

        return table

    @classmethod
    def _create_summary(self, results: List[ScanResult]) -> Panel:
        """
        Method to create the summary pannel with scanner results details

        Args:
            results: List of ScanResult

        Returns:
            Panel: rich Panel object
        """
        # Compute stats to show
        total_files = len({r.filename for r in results})  # Count unique files
        total_scans = len(results)
        safe = sum(1 for r in results if r.status == ScanStatus.LIKELY_SAFE)
        suspicious = sum(1 for r in results if r.status == ScanStatus.SUSPICIOUS)
        malicious = sum(1 for r in results if r.status == ScanStatus.OVERTLY_MALICIOUS)
        failed = sum(1 for r in results if r.status == ScanStatus.FAILED)

        # Create the main summary container
        summary_container = Table(
            show_header=False,
            box=None,
            padding=0,
            collapse_padding=True
        )
        
        # Add totals section
        totals = Table(
            show_header=False,
            box=None,
            padding=(0, 2),
            collapse_padding=True
        )
        totals.add_row("Total files scanned:", str(total_files))
        totals.add_row("Total scans performed:", str(total_scans))

        # Create statistics table
        summary_table = Table(
            show_header=False,
            box=None,
            padding=(0, 2),
            collapse_padding=True
        )
        
        summary_table.add_column("Icon", style="bold")
        summary_table.add_column("Label", style="bold")
        summary_table.add_column("Count", justify="right")

        # Add the statistics rows
        summary_table.add_row("✅", "Safe", str(safe))
        summary_table.add_row("⚠️", "Suspicious", str(suspicious))
        summary_table.add_row("❌", "Malicious", str(malicious))
        summary_table.add_row("⚡", "Failed", str(failed))

        # Combine all elements
        summary_container.add_row(totals)
        summary_container.add_row("")  # Empty row for spacing
        summary_container.add_row(summary_table)

        summary = Panel(
            summary_container,
            title="Summary",
            box=box.ROUNDED
        )

        return summary

    @classmethod
    def display_scan_results(self, results: List[ScanResult]) -> None:
        """
        Display scan results formatted using rich library
        """
        # Adding an empty line for spacing
        print(" ")

        if not results:
            self.console.print("[yellow]No scan results to display[/yellow]")
            return

        # Create main table
        table = self._create_details_table(results)

        # Create summary panel
        summary = self._create_summary(results)

        self.console.print(table)
        self.console.print(summary)