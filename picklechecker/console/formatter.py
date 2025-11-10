"""
Console results formatter using Rich library for displaying scan results in the terminal.
"""

import logging
from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from picklechecker.core.results import AnalysisResult, AnalysisStatus
from picklechecker.core.safety import SafetyLevel


class ConsoleResultsFormatter:
    """
    Formatter class for displaying PickleChecker scan results in the console using Rich.
    """

    logger = logging.getLogger(__name__)
    console = Console()

    @classmethod
    def safety_style(cls, level: SafetyLevel) -> str:
        """
        Returns the Rich color style string for a given safety level.

        Args:
            level (SafetyLevel): The safety level enum value.

        Returns:
            str: The color style (e.g., "green", "yellow").
        """
        if level == SafetyLevel.INNOCUOUS:
            return "green"
        elif level == SafetyLevel.SUSPICIOUS:
            return "yellow"
        elif level == SafetyLevel.DANGEROUS:
            return "red"
        else:  # UNKNOWN or others
            return "dim white"

    @classmethod
    def _create_result_panel(cls, result: AnalysisResult) -> Panel:
        """
        Creates a Rich panel displaying the scan result for a single file.

        Args:
            result (AnalysisResult): The analysis result for the file.

        Returns:
            Panel: A Rich Panel containing the file result summary and global imports table.
        """
        # Main container for the result (file name + imports table)
        result_container = Table(show_header=False, box=None, padding=0, collapse_padding=True)

        # Table for global imports
        imports_table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            show_lines=True,
            expand=False,
        )
        imports_table.add_column("Global Import")
        imports_table.add_column("Safety Level")

        # Populate the imports table
        if not result.globals_found:
            imports_table.add_row("[italic]No global imports found[/italic]", "")
        else:
            for global_import in result.globals_found:
                module = global_import.module
                name = global_import.name
                safety = global_import.safety
                # Format the row with colors for safety level
                imports_table.add_row(
                    f"[blue]{module}[/blue].[bold]{name}[/bold]",
                    f"[{cls.safety_style(safety)} bold]{safety.name}[/]",
                )

        # Add file summary and imports table to the container
        result_container.add_row(
            f"[bold]{result.source_path.name}[/bold] --> [{cls.safety_style(result.safety)}]{result.safety.name}[/]"
        )
        result_container.add_row(imports_table)

        return result_container

    @classmethod
    def _create_summary_panel(cls, results: List[AnalysisResult]) -> Panel:
        """
        Creates a Rich panel with a summary of all scan results.

        Args:
            results (List[AnalysisResult]): List of all analysis results.

        Returns:
            Panel: A Rich Panel with aggregated statistics.
        """
        # Compute aggregate statistics from results
        total_files = len({r.source_path for r in results})
        completed_scans = sum(1 for r in results if r.status == AnalysisStatus.COMPLETED)
        partial_scans = sum(1 for r in results if r.status == AnalysisStatus.COMPLETED_WITH_ERRORS)
        failed_scans = sum(1 for r in results if r.status == AnalysisStatus.FAILED)
        safe = sum(1 for r in results if r.safety == SafetyLevel.INNOCUOUS)
        suspicious = sum(1 for r in results if r.safety == SafetyLevel.SUSPICIOUS)
        dangerous = sum(1 for r in results if r.safety == SafetyLevel.DANGEROUS)

        # Main container for summary (totals + safety stats side by side)
        summary_container = Table(show_header=False, box=None, padding=0, collapse_padding=True)

        # Table for scan status totals
        totals_table = Table(show_header=False, box=None, padding=(0, 2), collapse_padding=True)
        totals_table.add_row("Total files scanned: ", str(total_files))
        totals_table.add_row(" - Completed:", str(completed_scans))
        totals_table.add_row(" - Completed with errors: ", str(partial_scans))
        totals_table.add_row(" - Failed: ", str(failed_scans))

        # Table for safety level counts
        safety_results_table = Table(
            show_header=False, box=None, padding=(0, 2), collapse_padding=True
        )
        safety_results_table.add_column("Icon", style="bold", no_wrap=True)
        safety_results_table.add_column("Label", style="bold", no_wrap=True)
        safety_results_table.add_column("Count", justify="right", no_wrap=True)

        # Add safety statistics rows
        safety_results_table.add_row(" ")  # Spacer for alignment
        safety_results_table.add_row("✅", "Safe", str(safe))
        safety_results_table.add_row("⚠️", "Suspicious", str(suspicious))
        safety_results_table.add_row("❌", "Dangerous", str(dangerous))

        # Combine totals and safety tables side by side
        summary_container.add_row(totals_table, safety_results_table)

        # Wrap in a panel with title
        summary = Panel(
            summary_container, title="Summary", box=box.ROUNDED, expand=False, padding=(1, 2)
        )

        return summary

    @classmethod
    def display_results(cls, results: List[AnalysisResult]) -> None:
        """
        Displays the scan results in the console using Rich formatting.

        Args:
            results (List[AnalysisResult]): List of analysis results to display.
        """
        print(" ")  # Add spacing before results

        # Display each file's result panel
        for result in results:
            result_panel = cls._create_result_panel(result)
            cls.console.print(result_panel)
            print(" ")  # Add spacing between results

        # Display summary if there are results
        if results:
            summary = cls._create_summary_panel(results)
            cls.console.print(summary)
