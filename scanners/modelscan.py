from modelscan.modelscan import ModelScan
from modelscan.issues import IssueCode
from modelscan.settings import DEFAULT_SETTINGS

from utils.logging_helper import get_logger
from scanners import Scanner, ScanStatus, ScanResult

class ModelscanScanner(Scanner):

    logger = get_logger(__name__)

    def _perform_file_scan(self, filepath: str) -> ScanResult:
        # Initialize ModelScan with default settings
        modelscan = ModelScan(settings=DEFAULT_SETTINGS)

        # Scan a model file or directory
        modelscan_result = modelscan.scan(filepath)

        #self.logger.debug(modelscan_result)

        # If modelscan returns an error we return ScanStatus.FAILED
        if modelscan.errors:
            return self._build_failed_result(filepath, ", ".join(error.to_dict().get("description") for error in modelscan.errors))
        
        # Format issues into something readable
        issues = []
        for issue in modelscan.issues.all_issues:
            if issue.code.value == IssueCode.UNSAFE_OPERATOR.value:
                issues.append(issue.details.output_lines()[0]) # The first line gives the essential info
            else:
                self.logger.warning(f"Skipping unknown issue type : {issue.code.name}")

        details = {
            "issues": "None" if not issues else "\n - " + "\n - ".join(issues)
        }

        status = ScanStatus.OVERTLY_MALICIOUS if modelscan.issues.all_issues else ScanStatus.LIKELY_SAFE
        
        return ScanResult(
            scanner=self.name,
            filename=filepath,
            status=status,
            details=details
        )