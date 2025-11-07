from picklescan.scanner import scan_file_path

from utils.logging_helper import get_logger
from scanners import Scanner, ScanStatus, ScanResult

class PicklescanScanner(Scanner):

    logger = get_logger(__name__)

    def _perform_file_scan(self, filepath: str) -> ScanResult:
        picklescan_result = scan_file_path(filepath)

        # If picklescan returns an error we return ScanStatus.FAILED
        if picklescan_result.scan_err:
            return self._build_failed_result(filepath, "Unknown error when running picklescan")
        
        details = {
            "scanned_files": picklescan_result.scanned_files,
            "issues_count": picklescan_result.issues_count,
            "infected_files": picklescan_result.infected_files
        }

        status = ScanStatus.OVERTLY_MALICIOUS if picklescan_result.issues_count != 0 else ScanStatus.LIKELY_SAFE
        
        return ScanResult(
            scanner=self.name,
            filename=filepath,
            status=status,
            details=details
        )