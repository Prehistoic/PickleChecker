from pathlib import Path
from typing import List
import logging

from picklechecker.core.handlers import FileFormatHandler
from picklechecker.core.handlers.raw_pickle_handler import RawPickleHandler
from picklechecker.core.results import AnalysisResult

class HandlersRegistry:

    logger = logging.getLogger(__name__)

    def __init__(self):
        self._handlers: List[FileFormatHandler] = [RawPickleHandler()]

    def register(self, handler: FileFormatHandler) -> None:
        self._handlers.append(handler)

    def pick(self, filepath: Path) -> FileFormatHandler | None:
        for h in self._handlers:
            if h.supports(filepath):
                self.logger.debug(f"{filepath} can be handled by {type(h)}")
                return h
        
        self.logger.warning(f"No handler found for {filepath}")
        return None

class PickleScanner:
    
    logger = logging.getLogger(__name__)
    registry = HandlersRegistry()

    @classmethod
    def scan_file(self, filepath: str | Path) -> AnalysisResult:
        target_filepath = Path(filepath)

        handler = self.registry.pick(target_filepath)

        if not handler:
            return AnalysisResult(source_path=target_filepath, format_name="unknown", errors=[f"No handler found for {target_filepath}"])
        
        return handler.analyze(target_filepath)
    
    @classmethod
    def scan_directory(self, dirpath: str | Path) -> List[AnalysisResult]:
        target_dirpath = Path(dirpath)
        results = []

        # rglob('*') recursively yields every file and directory in the tree.
        # We then filter for files and extensions associated with pickle.
        for file_path in target_dirpath.rglob('*'):
            if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):  # Skip files in dot-directories or dot-files:
                self.logger.debug(f"Analyzing {file_path}...")
                result = self.scan_file(file_path)
                results.append(result)

        self.logger.info(f"Scan finished for directory {dirpath}")
        return results