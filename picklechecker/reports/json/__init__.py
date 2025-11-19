"""
Module for generating JSON reports from scan results.
"""

import json
from pathlib import Path

from picklechecker.core.safety import SafetyLevel
from picklechecker.core.results import AnalysisStatus
from picklechecker.reports import Report


class JsonReportGenerator(Report):
    """
    Generator for JSON format reports.
    """

    format = "json"

    def save(self, output_filepath: str | Path):
        """
        Saves the scan results to a JSON file.

        Args:
            output_filepath (str | Path): The path where the JSON will be saved.
        """
        # Build the report structure
        report = {
            "target": self.target,
            "target_type": self.target_type,
            "stats": {
                "total_files": len(self.results),
                "safety_counters": {
                    "innocuous": sum(1 for r in self.results if r.safety == SafetyLevel.INNOCUOUS),
                    "suspicious": sum(
                        1 for r in self.results if r.safety == SafetyLevel.SUSPICIOUS
                    ),
                    "dangerous": sum(1 for r in self.results if r.safety == SafetyLevel.DANGEROUS),
                },
                "status_counters": {
                    "completed": sum(
                        1 for r in self.results if r.status == AnalysisStatus.COMPLETED
                    ),
                    "completed_with_errors": sum(
                        1 for r in self.results if r.status == AnalysisStatus.COMPLETED_WITH_ERRORS
                    ),
                    "failed": sum(1 for r in self.results if r.status == AnalysisStatus.FAILED),
                },
            },
            "results": [
                {
                    "filename": str(result.source_path),
                    "safety": result.safety.name,
                    "scan_errors": result.errors,
                    "globals": [
                        {
                            "module": g.module,
                            "name": g.name,
                            "safety": g.safety.name,
                        }
                        for g in result.globals_found
                    ],
                }
                for result in self.results
            ],
        }

        # Write to file
        output_file = Path(output_filepath)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
