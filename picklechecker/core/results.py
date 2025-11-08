from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

from picklechecker.core.safety import SafetyLevel
from picklechecker.core.globals import SAFE_GLOBALS, UNSAFE_GLOBALS, GlobalReference

@dataclass
class AnalysisResult:
    source_path: Path
    globals_found: List[GlobalReference] = field(default_factory=list)
    opcode_counts: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    safety: SafetyLevel = SafetyLevel.UNKNOWN

    def add_global(self, module: str, name: str, opcode: str, line: int) -> None:
        # Determine safety level based on UNSAFE_GLOBALS and SAFE_GLOBALS
        # Priority: DANGEROUS if explicitly unsafe, then INNOCUOUS if explicitly safe, else SUSPICIOUS
        if module in UNSAFE_GLOBALS and name in UNSAFE_GLOBALS[module]:
            safety = SafetyLevel.DANGEROUS
        elif module in SAFE_GLOBALS and name in SAFE_GLOBALS[module]:
            safety = SafetyLevel.INNOCUOUS
        else:
            safety = SafetyLevel.SUSPICIOUS
        
        reference = GlobalReference(module, name, opcode, line, safety)
        self.globals_found.append(reference)

    def compute_safety_level(self):
        self.safety = SafetyLevel(max([g.safety.value for g in self.globals_found]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "globals_found": [g.__dict__ for g in self.globals_found],
            "opcode_counts": self.opcode_counts,
            "errors": self.errors,
        }