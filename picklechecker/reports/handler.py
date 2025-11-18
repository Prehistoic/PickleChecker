import os
from pathlib import Path
from typing import List, Any
import logging

from picklechecker.reports.pdf import PdfReportGenerator
from picklechecker.reports.json import JsonReportGenerator
from picklechecker.core.results import AnalysisResult


class ReportHandler:
    """
    Handles report output logic: path validation, format correction,
    directory creation, and delegation to the correct Report class.
    """

    logger = logging.getLogger(__name__)

    # Map CLI format string to the corresponding Report Class
    FORMAT_MAP = {"pdf": PdfReportGenerator, "json": JsonReportGenerator}

    def __init__(self, output_path: str, format_key: str):
        """
        Initializes the ReportHandler with user-provided output path and format.

        Args:
            output_path (str): The user-specified output file path.
            format_key (str): The desired report format (e.g., 'pdf').
        """
        # Store user-provided arguments
        self.user_path = output_path
        self.format_key = format_key.lower()
        self.report_class = self._get_report_class()
        self.final_path = self._determine_final_path()
        self.directory = Path(self.final_path).parent

    def _get_report_class(self) -> Any:
        """
        Retrieves the correct Report class from the map.

        Returns:
            The Report class corresponding to the format_key.

        Raises:
            ValueError: If the format_key is not supported.
        """
        report_class = self.FORMAT_MAP.get(self.format_key)
        if not report_class:
            # This should ideally be caught by argparse choices, but acts as a safeguard
            raise ValueError(f"Unsupported report format: {self.format_key}")

        return report_class

    def _determine_final_path(self) -> str:
        """
        Corrects the file extension if it doesn't match the requested format.

        Returns:
            str: The corrected output file path.
        """
        expected_ext = f".{self.format_key}"
        root, current_ext = os.path.splitext(self.user_path)

        # Check if the user-provided extension matches the format
        if current_ext.lower() != expected_ext:
            # Auto-Correction Logic
            final_path = root + expected_ext
            self.logger.warning(
                f"Filename extension '{current_ext}' does not match requested format '{self.format_key}'. "
                f"Automatically correcting filename to: {final_path}"
            )
            return final_path

        return self.user_path

    def _ensure_directory_exists(self) -> None:
        """
        Creates the directory non-recursively, failing if parent is missing.

        Raises:
            FileNotFoundError: If the parent directory does not exist.
            RuntimeError: For other creation errors.
        """
        try:
            # Using mkdir() with exist_ok=True and default parents=False
            self.directory.mkdir(exist_ok=True)
            self.logger.debug(f"Directory ensured/created: {self.directory}")
        except FileNotFoundError:
            # Raise an informative error if a parent directory is missing
            raise FileNotFoundError(
                f"Cannot save report to '{self.final_path}'. "
                f"The parent directory '{self.directory}' does not exist and will not be created automatically."
            )
        except Exception as e:
            # Handle other errors like permission issues
            raise RuntimeError(f"Failed to create directory '{self.directory}': {e}")

    def save_report(self, target: str, target_type: str, results: List[AnalysisResult]) -> None:
        """
        Executes the file saving process.

        Args:
            target: The original scan target
            target_type: The original scan target type (file, directory, hf_model)
            results: The data to include in the report (list of AnalysisResult)
        """
        self.logger.info(f"Initiating report save for format: {self.format_key.upper()}")

        # 1. Ensure the target directory is ready
        self._ensure_directory_exists()

        # 2. Delegate the actual saving to the correct Report Class
        report = self.report_class(target, target_type, results)
        report.save(self.final_path)

        self.logger.info("Report save complete")
