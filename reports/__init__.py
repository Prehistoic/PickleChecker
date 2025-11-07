import os
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod

from utils.logging_helper import get_logger
from utils.scanners_helper import ScanResult
from utils.pickle_helper import PickleAnalysis
from config import OUTPUT_DIR, OUTPUT_FILENAME_NO_EXT

class Report(ABC):
    """Helper class for exporting scan results to different formats."""

    logger = get_logger(__name__)

    @property
    @abstractmethod
    def format(self):
        pass

    def __init__(self, output_filepath: str | None = None):
        self.output_filepath = output_filepath if output_filepath else Path(OUTPUT_DIR) / f"{OUTPUT_FILENAME_NO_EXT}.{self.format}"

    def _ensure_output_dir(self) -> None:
        """Ensure the output directory exists."""
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            self.logger.debug(f"Ensured output directory exists: {OUTPUT_DIR}")
        except Exception as e:
            self.logger.error(f"Failed to create output directory {OUTPUT_DIR}: {e}")
            raise

    @abstractmethod
    def _create_report(self, target: str | None, target_type: str | None, scanner_results: List[ScanResult], pickle_analyses: List[PickleAnalysis]) -> Path:
        pass
    
    def export(self, target: str | None, target_type: str | None, scanner_results: List[ScanResult], pickle_analyses: List[PickleAnalysis]) -> Path:
        self._ensure_output_dir()

        self.logger.info(f"Exporting results to {self.format}: {self.output_filepath}")
        try:
            self._create_report(target, target_type, scanner_results, pickle_analyses)
        except Exception as e:
            self.logger.error(f"Failed to export {self.format} to {self.output_filepath}: {e}")
            raise