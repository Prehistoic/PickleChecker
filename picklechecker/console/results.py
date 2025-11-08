import logging
from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from picklechecker.core.results import AnalysisResult, AnalysisStatus
from picklechecker.core.safety import SafetyLevel

class ConsoleResultsFormatter:

    logger = logging.getLogger(__name__)
    console = Console()

    @classmethod
    def _create_details_table(cls, result: List[AnalysisResult]):
        pass

    @classmethod
    def _create_summary(cls, results: List[AnalysisResult]):
        """
        Method to create the summary panel to aggregate analysis results

        Args:
            results: List of AnalysisResult

        Returns: 
            Panel: rich Panel object
        """
        # Compute stats to show
        total_files = len({r.source_path for r in results})
        completed_scans = sum(1 for r in results if r.status == AnalysisStatus.COMPLETED)
        partial_scans = sum(1 for r in results if r.status == AnalysisStatus.COMPLETED_WITH_ERRORS)
        failed_scans = sum(1 for r in results if r.status == AnalysisStatus.FAILED)
        safe = sum(1 for r in results if r.safety == SafetyLevel.INNOCUOUS)
        suspicious = sum(1 for r in results if r.safety == SafetyLevel.SUSPICIOUS)
        dangerous = sum(1 for r in results if r.safety == SafetyLevel.DANGEROUS)

        # Create the main summary container
        summary_container = Table(
            show_header=False,
            box=None,
            padding=0,
            collapse_padding=True
        )
        
        # Add totals section
        totals_table = Table(
            show_header=False,
            box=None,
            padding=(0, 2),
            collapse_padding=True
        )
        totals_table.add_row("Total files scanned: ", str(total_files))
        totals_table.add_row(" - Completed:", str(completed_scans))
        totals_table.add_row(" - Completed with errors: ", str(partial_scans))
        totals_table.add_row(" - Failed: ", str(failed_scans))

        # Create safety_results_table table
        safety_results_table = Table(
            show_header=False,
            box=None,
            padding=(0, 2),
            collapse_padding=True
        )
        
        safety_results_table.add_column("Icon", style="bold", no_wrap=True)
        safety_results_table.add_column("Label", style="bold", no_wrap=True)
        safety_results_table.add_column("Count", justify="right", no_wrap=True)  # No need for ratio here

        # Add the statistics rows
        safety_results_table.add_row(" ") # For better alignment with totals_table
        safety_results_table.add_row("✅", "Safe", str(safe))
        safety_results_table.add_row("⚠️", "Suspicious", str(suspicious))
        safety_results_table.add_row("❌", "Dangerous", str(dangerous))

        # Combine all elements
        summary_container.add_row(totals_table, safety_results_table)

        summary = Panel(
            summary_container,
            title="Summary",
            box=box.ROUNDED,
            expand=False,
            padding=(1, 2)
        )

        return summary

    @classmethod
    def display_results(cls, results: List[AnalysisResult]):
        """
        Display scan results formatted using rich library
        """
        print(" ") # Adding an empty line for spacing

        # Create results per file table
        for result in results:
            details_table = cls._create_details_table(result)
            cls.console.print(details_table)

            print(" ") # Adding an empty line for spacing

        # Create summary panel
        if results:
            summary = cls._create_summary(results)
            cls.console.print(summary)