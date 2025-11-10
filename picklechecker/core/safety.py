"""
Module defining safety levels for analysis results.
"""

from enum import Enum


class SafetyLevel(Enum):
    """
    Enumeration of safety levels for global references and overall file analysis.

    Values are ordered by increasing risk level, with higher values indicating greater danger.
    """

    UNKNOWN = -1  # Safety level not determined (e.g., no globals found)
    INNOCUOUS = 0  # Safe, no known risks
    SUSPICIOUS = 1  # Potentially risky, requires review
    DANGEROUS = 2  # Known dangerous, high risk
