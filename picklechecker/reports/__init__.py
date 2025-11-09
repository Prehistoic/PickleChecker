"""
This module defines the abstract base class for generating reports from scan results.
Concrete implementations (e.g., PDF reports) inherit from this class to handle specific formats.
"""

from pathlib import Path
from typing import List
import logging
from abc import ABC, abstractmethod

from picklechecker.core.results import AnalysisResult


class Report(ABC):
    """Helper class for exporting scan results to different formats."""

    logger = logging.getLogger(__name__)

    @property
    @abstractmethod
    def format(self) -> str:
        """
        Abstract property that returns the file extension for this report format (e.g., '.pdf').

        Returns:
            str: The file extension including the leading dot.
        """
        pass

    def __init__(self, target: str, target_type: str, results: List[AnalysisResult]):
        """
        Initiate the Report object

        Args:
            target: The original scan target
            target_type: The original scan target type (file, directory, hf_model)
            results: List of AnalysisResult to include in the report.
        """
        self.target = target
        self.target_type = target_type
        self.results = results

    @abstractmethod
    def save(self, output_filepath: str | Path):
        """
        Class method to save the report

        Args:
            output_filepath: The corrected output file path.
        """
        pass
