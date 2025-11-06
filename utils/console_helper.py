from typing import List
from pathlib import Path
from itertools import groupby
from operator import attrgetter

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from scanners import ScanResult, ScanStatus
from utils.pickle_helper import PickleAnalysis
from utils.logging_helper import get_logger

class ConsoleHelper:
    
    logger = get_logger(__name__)
    console = Console()

    @classmethod
    def _create_scanner_results_table(self, results: List[ScanResult]) -> Table:
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
            show_lines=True,
            expand=True
        )
        
        table.add_column("File", style="green", no_wrap=True)  # No wrap for filenames
        table.add_column("Scanner Results", ratio=1)  # This column will expand to fill space

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
                collapse_padding=False,
                expand=True
            )
            scanner_table.add_column("Scanner", style="blue", no_wrap=True)
            scanner_table.add_column("Status", style="bold", no_wrap=True)
            scanner_table.add_column("Details", style="grey70", ratio=1)  # Expand details column

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
    def _create_global_imports_table(self, pickle_analyses: List[PickleAnalysis]) -> Table:
        """
        Method to create the table displaying the list of global imports for each analyzed pickle files

        Args:
            pickle_analyses: List of PickleAnalysis

        Returns:
            Table: rich Table object
        """
        table = Table(
            title="Pickle Files Global Imports",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            show_lines=True,
            expand=True
        )
        
        table.add_column("File", style="cyan", no_wrap=True)  # No wrap for filenames
        table.add_column("Global Imports", ratio=1)  # This column will expand to fill space

        for analysis in pickle_analyses:
            # Create inner table for global imports
            imports_table = Table(
                box=box.SIMPLE,
                show_header=False,
                show_lines=True,
                pad_edge=True,
                padding=(0,1,0,1),
                collapse_padding=False,
                expand=True
            )
            
            # Sort imports for consistent display
            sorted_imports = sorted(analysis.global_imports)
            
            if sorted_imports:
                # Create rows of imports with module and name separated
                for import_path in sorted_imports:
                    try:
                        module, name = import_path.rsplit('.', 1)
                        imports_table.add_row(
                            f"[blue]{module}[/blue].[bold]{name}[/bold]"
                        )
                    except ValueError:
                        # Handle case where import doesn't have a dot
                        imports_table.add_row(f"[bold]{import_path}[/bold]")
            else:
                imports_table.add_row("[italic]No global imports found[/italic]")

            # Add the file and its imports to the main table
            table.add_row(
                Path(analysis.filename).name,
                imports_table
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
        
        summary_table.add_column("Icon", style="bold", no_wrap=True)
        summary_table.add_column("Label", style="bold", no_wrap=True)
        summary_table.add_column("Count", justify="right", no_wrap=True)  # No need for ratio here

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
            box=box.ROUNDED,
            expand=True
        )

        return summary

    @classmethod
    def display_results(self, scanner_results: List[ScanResult], pickle_analyses: List[PickleAnalysis]) -> None:
        """
        Display scan results formatted using rich library
        """
        print(" ") # Adding an empty line for spacing

        # Create scanner results table
        if scanner_results:
            scanner_results_table = self._create_scanner_results_table(scanner_results)
            self.console.print(scanner_results_table)
        else:
            self.console.print("[yellow]No scan results to display[/yellow]")

        print(" ") # Adding an empty line for spacing

        # Create global imports table
        if pickle_analyses:
            global_imports_table = self._create_global_imports_table(pickle_analyses)
            self.console.print(global_imports_table)
        else:
            self.console.print("[yellow]No pickle analysis to display[/yellow]")

        print(" ") # Adding an empty line for spacing

        # Create summary panel
        if scanner_results:
            summary = self._create_summary(scanner_results)
            self.console.print(summary)