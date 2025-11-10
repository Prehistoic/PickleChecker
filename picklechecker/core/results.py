"""
Module for representing analysis results, statuses, and global references.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any
from enum import Enum

from picklechecker.core.safety import SafetyLevel
from picklechecker.core.globals import SAFE_GLOBALS, UNSAFE_GLOBALS, RUNTIME_SAFE_GLOBALS, RUNTIME_UNSAFE_GLOBALS, GlobalReference


class AnalysisStatus(Enum):
    """
    Enumeration of possible analysis statuses for a scan result.
    """

    ONGOING = 0
    COMPLETED = 1
    COMPLETED_WITH_ERRORS = 2
    FAILED = 3


@dataclass
class AnalysisResult:
    """
    Represents the result of analyzing a single file for pickle safety.

    Attributes:
        source_path (Path): Path to the analyzed file.
        globals_found (List[GlobalReference]): List of global references found.
        opcode_counts (Dict[str, int]): Counts of pickle opcodes encountered.
        status (AnalysisStatus): Current status of the analysis.
        safety (SafetyLevel): Overall safety level of the file.
        errors (List[str]): List of error messages encountered during analysis.
    """

    source_path: Path
    globals_found: List[GlobalReference] = field(default_factory=list)
    opcode_counts: Dict[str, int] = field(default_factory=dict)
    status: AnalysisStatus = AnalysisStatus.ONGOING
    safety: SafetyLevel = SafetyLevel.UNKNOWN
    errors: List[str] = field(default_factory=list)

    def add_global(self, module: str, name: str, opcode: str, line: int) -> None:
        """
        Adds a global reference to the result and determines its safety level.

        Safety priority: RUNTIME_UNSAFE_GLOBALS > RUNTIME_SAFE_GLOBALS > UNSAFE_GLOBALS > SAFE_GLOBALS

        Checks for module prefixes (e.g., if 'posix' is unsafe, 'posix.toto' is also unsafe).

        Args:
            module (str): The module name.
            name (str): The function/attribute name.
            opcode (str): The pickle opcode.
            line (int): The line/index in the stream.
        """
        def is_in_globals(mod: str, nm: str, globals_dict: dict[str, list[str]]) -> bool:
            for key, values in globals_dict.items():
                if mod == key or mod.startswith(key + "."):
                    if "*" in values or nm in values:
                        return True
            return False

        # If module or name == <unknown> we must assume it is RCE
        if module == "<unknown>" or name == "<unknown>":
            safety = SafetyLevel.DANGEROUS
        # Check runtime unsafe globals first (highest priority)
        elif is_in_globals(module, name, RUNTIME_UNSAFE_GLOBALS):
            safety = SafetyLevel.DANGEROUS
        # Check runtime safe globals
        elif is_in_globals(module, name, RUNTIME_SAFE_GLOBALS):
            safety = SafetyLevel.INNOCUOUS
        # Check static unsafe globals
        elif is_in_globals(module, name, UNSAFE_GLOBALS):
            safety = SafetyLevel.DANGEROUS
        # Check static safe globals
        elif is_in_globals(module, name, SAFE_GLOBALS):
            safety = SafetyLevel.INNOCUOUS
        else:
            # Default to suspicious if not explicitly listed
            safety = SafetyLevel.SUSPICIOUS

        reference = GlobalReference(module, name, opcode, line, safety)
        self.globals_found.append(reference)

    def compute_safety_level(self) -> None:
        """
        Computes the overall safety level of the file based on the highest risk global found.
        """
        if not self.globals_found:
            self.safety = SafetyLevel.UNKNOWN
            return

        # Find the maximum safety value (highest risk)
        max_safety_value = max(g.safety.value for g in self.globals_found)
        self.safety = SafetyLevel(max_safety_value)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the result to a dictionary for serialization.

        Returns:
            Dict[str, Any]: Dictionary representation of the result.
        """
        return {
            "source_path": str(self.source_path),
            "globals_found": [g.__dict__ for g in self.globals_found],
            "opcode_counts": self.opcode_counts,
            "errors": self.errors,
        }
