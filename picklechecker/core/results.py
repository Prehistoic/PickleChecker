from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

@dataclass
class GlobalReference:
    module: str
    name: str
    opcode: str
    line: int  # sequential index of opcode

@dataclass
class AnalysisResult:
    source_path: Path
    globals_found: List[GlobalReference] = field(default_factory=list)
    opcode_counts: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def add_global(self, module: str, name: str, opcode: str, line: int) -> None:
        self.globals_found.append(GlobalReference(module, name, opcode, line))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "globals_found": [g.__dict__ for g in self.globals_found],
            "opcode_counts": self.opcode_counts,
            "errors": self.errors,
        }