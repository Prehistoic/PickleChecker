import io
import pickletools
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Tuple

from picklechecker.core.results import AnalysisResult


class FileFormatHandler(ABC):
    """Strategy for scanning a specific file format potentially containing pickle data."""

    format_name: str

    @abstractmethod
    def supports(self, path: Path) -> bool:
        """Return True if this handler can process the file."""
        raise NotImplementedError

    @abstractmethod
    def extract_pickles(self, path: Path) -> Iterable[Tuple[bytes, str]]:
        """
        Yield (pickle_bytes, label) tuples.
        For simple .pkl/.pickle files there is a single top-level pickle.
        For container formats (e.g. PyTorch .pt) you may yield multiple.
        """
        raise NotImplementedError

    def analyze(self, path: Path) -> AnalysisResult:
        result = AnalysisResult(source_path=path, format_name=self.format_name)
        try:
            for blob, label in self.extract_pickles(path):
                self._analyze_blob(blob, result, label)
        except Exception as e:
            result.errors.append(f"{self.format_name} handler failed: {e}")
        return result

    def _analyze_blob(self, data: bytes, result: AnalysisResult, label: str) -> None:
        stream = io.BytesIO(data)
        for idx, (opcode, arg, pos) in enumerate(pickletools.genops(stream)):
            result.opcode_counts[opcode.name] = result.opcode_counts.get(opcode.name, 0) + 1
            if opcode.name in {"GLOBAL", "STACK_GLOBAL"}:
                # arg for GLOBAL is "module name"
                try:
                    module, name = str(arg).split(" ", 1)
                except ValueError:
                    module, name = ("<unknown>", str(arg))
                result.add_global(module, name, opcode.name, idx)


