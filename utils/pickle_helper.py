"""
Helper module for analyzing pickle files and archives.
Provides safe disassembly and import analysis without executing any code.
"""

import pickletools
import zipfile
from pathlib import Path
from dataclasses import dataclass
from typing import Set, List, Tuple

from utils.logging_helper import get_logger
from config import (
    PICKLE_FILE_FORMATS,
    PYTORCH_FILE_FORMATS,
    MAX_FILES,
    MAX_TOTAL_UNCOMPRESSED,
    MAX_UNCOMPRESSED_PER_ENTRY
)

@dataclass
class PickleAnalysis:
    """
    Stores the results of a pickle file analysis.
    
    Attributes:
        filename: Name of the analyzed file
        disassembly: String containing the pickle operations disassembly
        global_imports: Set of all GLOBAL imports found in the pickle
    """
    filename: str
    disassembly: str
    global_imports: Set[str]
    error: str = None

class PickleAnalyzer:
    """
    Safely analyzes pickle files and archives containing pickles.
    Provides disassembly and import analysis without executing any code.
    """

    logger = get_logger(__name__)

    @classmethod
    def _is_pytorch_file(cls, path: Path) -> bool:
        """Check if file has a PyTorch model extension."""
        return path.suffix.lower() in PYTORCH_FILE_FORMATS

    @classmethod
    def _read_file_bytes(cls, path: Path) -> bytes:
        """
        Safely read raw bytes from a file.

        Args:
            path: Path to the file to read

        Returns:
            bytes: Raw content of the file

        Raises:
            IOError: If file cannot be read
        """
        cls.logger.debug(f"Reading bytes for: {path}")
        try:
            with open(path, 'rb') as f:
                data = f.read()
            cls.logger.debug(f"Successfully read {len(data)} bytes from {path}")
            return data
        except Exception as e:
            cls.logger.error(f"Failed to read file {path}: {e}")
            raise

    @classmethod
    def _disassemble_bytes(cls, data: bytes, tag: str = "") -> Tuple[str, Set[str]]:
        """
        Safely disassemble pickle bytes and collect GLOBAL imports.

        Args:
            data: Raw pickle bytes to analyze
            tag: Optional prefix for disassembly lines (useful for archive entries)

        Returns:
            Tuple containing:
                - Disassembly text (or error message if failed)
                - Set of GLOBAL imports found
        """
        dis_lines: List[str] = []
        global_imports: Set[str] = set()
        
        try:
            for opcode, arg, pos in pickletools.genops(data):
                dis_lines.append(f"{tag}{pos}: {opcode.name} {arg}")
                if opcode.name == "GLOBAL":
                    global_imports.add(str(arg))
        except Exception as e:
            cls.logger.debug(f"Disassembly failed for {tag}: {e}")
            return (f"[Failed to disassemble{(' ' + tag) if tag else ''}: {e}]", set())
            
        return ("\n".join(dis_lines), global_imports)

    @classmethod
    def _analyze_zip_entries(cls, path: Path) -> Tuple[List[str], Set[str]]:
        """
        Safely inspect ZIP archive entries without extraction.
        Only analyzes files matching pickle extensions.

        Args:
            path: Path to the ZIP archive

        Returns:
            Tuple containing:
                - List of disassembly lines for each entry
                - Set of all GLOBAL imports found across entries
        """
        dis_lines: List[str] = []
        global_imports: Set[str] = set()

        with zipfile.ZipFile(path, "r") as z:
            # Validate archive size constraints
            infos = z.infolist()
            if len(infos) > MAX_FILES:
                msg = f"[Archive contains too many entries ({len(infos)}); skipping detailed analysis]"
                cls.logger.warning(msg)
                return ([msg], set())

            total_uncompressed = 0
            for info in infos:
                if info.is_dir():
                    continue

                # Track total uncompressed size
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                    cls.logger.warning("Archive total uncompressed size exceeds limit; aborting inspection.")
                    break

                # Only process pickle files
                name = info.filename
                if not any(name.lower().endswith(ext) for ext in PICKLE_FILE_FORMATS):
                    continue

                # Check individual entry size
                if info.file_size > MAX_UNCOMPRESSED_PER_ENTRY:
                    cls.logger.warning(f"Skipping {name}: uncompressed size {info.file_size} > per-entry limit.")
                    dis_lines.append(f"{name}: [skipped - too large]")
                    continue

                # Analyze entry content
                try:
                    with z.open(info) as fh:
                        data = fh.read(MAX_UNCOMPRESSED_PER_ENTRY + 1)
                    if len(data) > MAX_UNCOMPRESSED_PER_ENTRY:
                        cls.logger.warning(f"Skipping {name}: actual size > per-entry limit.")
                        dis_lines.append(f"{name}: [skipped - too large]")
                        continue

                    dtext, imports = cls._disassemble_bytes(data, tag=f"{name}:")
                    dis_lines.append(dtext)
                    global_imports.update(imports)
                except Exception as e:
                    cls.logger.debug(f"Failed to read archive entry {name}: {e}")
                    dis_lines.append(f"{name}: [read error: {e}]")

        return (dis_lines, global_imports)

    @classmethod
    def analyze_pickle(cls, filepath: str) -> PickleAnalysis:
        """
        Analyze a single pickle file or archive.

        Args:
            filepath: Path to the file to analyze

        Returns:
            PickleAnalysis containing disassembly and found imports
        """
        path = Path(filepath)
        cls.logger.info(f"Starting pickle analysis for: {path}")

        try:
            if zipfile.is_zipfile(path):
                cls.logger.debug("ZIP archive detected; inspecting entries safely")
                dis_lines, imports = cls._analyze_zip_entries(path)
                dis_text = "\n".join(dis_lines)
                cls.logger.info(f"Analysis complete - Found {len(imports)} unique global imports in archive")
                return PickleAnalysis(filename=str(path), disassembly=dis_text, global_imports=imports)

            # Non-archive file
            data = cls._read_file_bytes(path)
            dtext, imports = cls._disassemble_bytes(data)
            cls.logger.info(f"Analysis complete - Found {len(imports)} unique global imports")
            return PickleAnalysis(filename=str(path), disassembly=dtext, global_imports=imports)

        except Exception as e:
            cls.logger.error(f"Failed to analyze file {path}: {e}")
            return PickleAnalysis(
                filename=str(path),
                disassembly=f"[Analysis error: {e}]",
                global_imports=set(),
                error=str(e)
            )

    @classmethod
    def analyze_directory(cls, dirpath: str) -> List[PickleAnalysis]:
        """
        Analyze all pickle files in a directory.

        Args:
            dirpath: Path to the directory to scan

        Returns:
            List of PickleAnalysis results, one per pickle file found
        """
        cls.logger.info(f"Starting directory analysis for: {dirpath}")
        analyses: List[PickleAnalysis] = []

        for file_path in Path(dirpath).rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in PICKLE_FILE_FORMATS:
                try:
                    analyses.append(cls.analyze_pickle(str(file_path)))
                except Exception as e:
                    cls.logger.error(f"Failed to analyze pickle file {file_path}: {e}")

        cls.logger.info(f"Directory analysis complete: {len(analyses)} files analyzed")
        return analyses