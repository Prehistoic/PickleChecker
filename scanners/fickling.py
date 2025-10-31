from fickling.analysis import check_safety, Severity
from fickling.fickle import Pickled
from fickling.pytorch import PyTorchModelWrapper
from pathlib import Path
from typing import Optional, Tuple

from utils.logging_helper import get_logger
from scanners import Scanner, ScanStatus, ScanResult
from config import BASIC_PICKLE_FILE_FORMATS, PYTORCH_FILE_FORMATS

class FicklingScanner(Scanner):

    logger = get_logger(__name__)

    # --- Mapping from Fickling's Severity to internal ScanStatus ---
    SEVERITY_MAPPINGS = [
        (Severity.LIKELY_SAFE, ScanStatus.LIKELY_SAFE),
        (Severity.POSSIBLY_UNSAFE, ScanStatus.SUSPICIOUS),
        (Severity.SUSPICIOUS, ScanStatus.SUSPICIOUS),
        (Severity.LIKELY_UNSAFE, ScanStatus.SUSPICIOUS),
        (Severity.LIKELY_OVERTLY_MALICIOUS, ScanStatus.OVERTLY_MALICIOUS),
        (Severity.OVERTLY_MALICIOUS, ScanStatus.OVERTLY_MALICIOUS),
    ]

    def _map_severity_to_status(self, severity: Severity) -> ScanStatus:
        """Maps Fickling Severity to internal ScanStatus"""
        for sev, status in self.SEVERITY_MAPPINGS:
            if severity == sev:
                return status
        return ScanStatus.FAILED

    def _load_pickled_object(self, target_path: Path) -> Tuple[Optional[Pickled], Optional[str]]:
        """Helper to load the Pickled object based on file type."""
        
        # Use .lower() for robust case-insensitive extension matching
        suffix = target_path.suffix.lower() 

        try:
            if suffix in BASIC_PICKLE_FILE_FORMATS:
                self.logger.debug(f"File {target_path.name} is a basic pickle.")
                # Resource management with 'with' is already correct.
                with open(target_path, "rb") as f:
                    return Pickled.load(f), None

            elif suffix in PYTORCH_FILE_FORMATS:
                self.logger.debug(f"File {target_path.name} is a PyTorch model.")
                try:
                    fickled_model = PyTorchModelWrapper(target_path)
                    return fickled_model.pickled, None
                except ValueError as e:
                    self.logger.debug(f"Failed to load {target_path.name} as a PyTorch model. Trying with Pickled.load() instead")
                    with open(target_path, "rb") as f:
                        return Pickled.load(f), None

            else:
                msg = f"Unknown or unsupported file type for Fickling: {suffix}"
                self.logger.error(msg)
                return None, msg

        except Exception as e:
            msg = f"Failed to load file {target_path.name} with Fickling: {e.__class__.__name__}: {e}"
            self.logger.error(msg)
            return None, msg

    def _perform_file_scan(self, filepath: str) -> ScanResult:
        """
        Scans a single file using Fickling, determining the loading mechanism
        based on file extension.
        """
        target_path = Path(filepath)

        # 1. Initial Validation
        if not target_path.exists():
            msg = f"No file found at {filepath}"
            self.logger.error(msg)
            return self._build_failed_result(filepath, msg)

        # 2. Load Pickled Object using helper
        pickled, error_msg = self._load_pickled_object(target_path)

        if error_msg:
            # error_msg contains the failure reason from the loading step
            return self._build_failed_result(filepath, error_msg)

        # 3. Perform Analysis (If loading was successful)
        fickling_result = check_safety(pickled)
        #self.logger.debug(f"Fickling scan result: {fickling_result.to_dict()}")

        # 4. Map fickling severity to ScanStatus options
        status = self._map_severity_to_status(fickling_result.severity)

        # 5. Extract essential details from Fickling scan result

        # Get list of issues first
        issues_list = [
            result.message 
            for result in list(fickling_result.results) 
            if result.severity >= max(fickling_result.results, Severity.LIKELY_UNSAFE) # Filtering to limit the number of issues shown
        ]

        # Format issues based on whether the list is empty
        issues_str = "None" if not issues_list else "\n - " + "\n - ".join(issues_list)

        analysis_results = fickling_result.detailed_results().get('AnalysisResult', {})
        details = {
            "severity": fickling_result.severity.name,
            "non_standard_imports": analysis_results.get('NonStandardImports', 'None'),
            "unsafe_imports_ml": analysis_results.get('UnsafeImportsML', 'None'),
            "issues": issues_str
        }
        
        # Log final status (using the actual status name for clarity)
        self.logger.info(f"Fickling scan for {target_path.name} finished with status: {status.name}")

        return ScanResult(
            scanner=self.name,
            filename=filepath,
            status=status,
            details=details
        )