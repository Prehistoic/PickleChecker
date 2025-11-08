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
    def safety_style(cls, level: SafetyLevel) -> str:
        """
        Assign color based on safety level
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
        Method to create the table displaying the result for a single file

        Args:
            result: AnalysisResult

        Returns:
            Panel: rich Panel object
        """
        result_container = Table(show_header=False, box=None, padding=0, collapse_padding=True)

        imports_table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
            show_lines=True,
            expand=False,
        )

        imports_table.add_column("Global Import")
        imports_table.add_column("Safety Level")

        if not result.globals_found:
            imports_table.add_row("[italic]No global imports found[/italic]", "")
        else:
            for global_import in result.globals_found:
                module = global_import.module
                name = global_import.name
                safety = global_import.safety

                imports_table.add_row(
                    f"[blue]{module}[/blue].[bold]{name}[/bold]",
                    f"[{cls.safety_style(safety)} bold]{safety.name}[/]",
                )

        result_container.add_row(
            f"[bold]{result.source_path.name}[/bold] --> [{cls.safety_style(result.safety)}]{result.safety.name}[/]"
        )
        result_container.add_row(imports_table)

        return result_container

    @classmethod
    def _create_summary_panel(cls, results: List[AnalysisResult]) -> Panel:
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
        summary_container = Table(show_header=False, box=None, padding=0, collapse_padding=True)

        # Add totals section
        totals_table = Table(show_header=False, box=None, padding=(0, 2), collapse_padding=True)
        totals_table.add_row("Total files scanned: ", str(total_files))
        totals_table.add_row(" - Completed:", str(completed_scans))
        totals_table.add_row(" - Completed with errors: ", str(partial_scans))
        totals_table.add_row(" - Failed: ", str(failed_scans))

        # Create safety_results_table table
        safety_results_table = Table(
            show_header=False, box=None, padding=(0, 2), collapse_padding=True
        )

        safety_results_table.add_column("Icon", style="bold", no_wrap=True)
        safety_results_table.add_column("Label", style="bold", no_wrap=True)
        safety_results_table.add_column(
            "Count", justify="right", no_wrap=True
        )  # No need for ratio here

        # Add the statistics rows
        safety_results_table.add_row(" ")  # For better alignment with totals_table
        safety_results_table.add_row("✅", "Safe", str(safe))
        safety_results_table.add_row("⚠️", "Suspicious", str(suspicious))
        safety_results_table.add_row("❌", "Dangerous", str(dangerous))

        # Combine all elements
        summary_container.add_row(totals_table, safety_results_table)

        summary = Panel(
            summary_container, title="Summary", box=box.ROUNDED, expand=False, padding=(1, 2)
        )

        return summary

    @classmethod
    def display_results(cls, results: List[AnalysisResult]):
        """
        Display scan results formatted using rich library
        """
        print(" ")  # Adding an empty line for spacing

        # Create a panel for each file result
        for result in results:
            result_panel = cls._create_result_panel(result)
            cls.console.print(result_panel)

            print(" ")  # Adding an empty line for spacing

        # Create summary panel
        if results:
            summary = cls._create_summary_panel(results)
            cls.console.print(summary)
