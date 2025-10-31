from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any
from pathlib import Path
import traceback

from utils.logging_helper import get_logger
from config import PICKLE_FILE_FORMATS

class ScanStatus(Enum):
    """
    Defines the possible outcomes of a scan operation as an enumeration.
    """
    LIKELY_SAFE = 0         # Scan completed, no malicious content found
    SUSPICIOUS = 1          # Scan completed, suspicious content was detected
    OVERTLY_MALICIOUS = 2   # Scan completed, malicious content was detected
    FAILED = 3              # The scan itself failed to complete

@dataclass
class ScanResult:
    """
    Stores the results of a scan operation for a single file.
    """
    scanner: str
    filename: str
    status: ScanStatus
    details: Dict[str, Any] = field(default_factory=dict)

    def add_detail(self, key: str, value: Any) -> None:
        """Add a detail to the scan result"""
        self.details[key] = value

class Scanner(ABC):
    """
    An Abstract Base Class (ABC) that defines the 'contract' for any scanner.
    It acts as an interface ensuring that any concrete scanner class
    that inherits from it *must* implement the '_perform_file_scan' method.
    """

    logger = get_logger("Scanner")

    def __init__(self, name: str):
        self.name = name

     # --- Reusable Failure Builder ---
    def _build_failed_result(self, filepath: str, error_msg: str) -> ScanResult:
        """Helper to standardize FAILED ScanResult creation."""
        return ScanResult(
            scanner=self.name,
            filename=filepath,
            status=ScanStatus.FAILED,
            details={"error": error_msg}
        )

    @abstractmethod
    def _perform_file_scan(self, filepath: str) -> ScanResult:
        """
        An abstract class method that must be implemented by any subclass.
        This method should define the logic for scanning a single file.

        Args:
            filepath (str): The full path to the file to be scanned

        Returns:
            ScanResult: Object containing the scan results
        """
        pass

    def run_file_scan(self, filepath: str) -> ScanResult:
        """
        A wrapper method around _perform_file_scan to have a common logging and 
        exception handling across scanners.

        Args:
            filepath (str): The full path to the file to be scanned

        Returns:
            ScanResult: Object containing the scan results
        """
        self.logger.info(f"Starting scan on file {filepath}")

        try:
            result = self._perform_file_scan(filepath)

            self.logger.info(f"Scan finished for {filepath}. Result: {result.status.name}")
            return result
        except Exception as e:
            self.logger.error(f"Scan failed for {filepath}:\n{traceback.format_exc()}")
            return self._build_failed_result(filepath, error_msg=e)
        
    def run_directory_scan(self, dirpath: str) -> List[ScanResult]:
        """
        A concrete class method that scans all relevant files in a given directory.
        It iterates through the directory, finds files matching PICKLE_FILE_FORMATS and 
        uses 'run_file_scan' on them.

        Args:
            dirpath (str): The full path to the directory to scan

        Returns:
            List[ScanResult]: A list of objects containing the scans results
        """
        self.logger.info(f"Starting scan on directory {dirpath}")

        results = []
        target_dir = Path(dirpath)

        # rglob('*') recursively yields every file and directory in the tree.
        # We then filter for files and extensions associated with pickle.
        for file_path in target_dir.rglob('*'):
            if file_path.is_file():
                if file_path.suffix.lower() in PICKLE_FILE_FORMATS:
                    self.logger.debug(f"Found pickle file: {file_path}")

                    result = self.run_file_scan(str(file_path))
                    results.append(result)

        self.logger.info(f"Scan finished for directory {dirpath}")
        return results