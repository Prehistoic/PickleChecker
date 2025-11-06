import pickletools
import torch
import zipfile
from pathlib import Path
from dataclasses import dataclass
from typing import Set, List, Tuple

from utils.logging_helper import get_logger
from config import PICKLE_FILE_FORMATS, PYTORCH_FILE_FORMATS, MAX_FILES, MAX_TOTAL_UNCOMPRESSED, MAX_UNCOMPRESSED_PER_ENTRY

@dataclass
class PickleAnalysis:
    filename: str
    disassembly: str
    global_imports: Set[str]

class PickleAnalyzer:

    logger = get_logger(__name__)

    @classmethod
    def _is_pytorch_file(cls, path: Path) -> bool:
        return path.suffix.lower() in PYTORCH_FILE_FORMATS

    @classmethod
    def _read_file_bytes(cls, path: Path) -> bytes:
        """
        Read raw bytes for a file. For PyTorch files, attempt the existing
        behavior but fall back to raw read if the torch-based approach fails.
        """
        cls.logger.debug(f"Reading bytes for: {path}")
        if cls._is_pytorch_file(path):
            cls.logger.debug("Detected PyTorch model file; attempting safe read strategy")
            try:
                # preserve previous behavior but guard it - if it fails, fallback
                temp_path = Path("temp_model.pkl")
                torch.save(torch.load(str(path), map_location="cpu"), temp_path)
                with open(temp_path, "rb") as f:
                    data = f.read()
                temp_path.unlink(missing_ok=True)
                return data
            except Exception as e:
                cls.logger.warning(f"PyTorch handling failed ({e}); falling back to raw read")
                # fallback to raw read
        with open(path, "rb") as f:
            return f.read()

    @classmethod
    def _disassemble_bytes(cls, data: bytes, tag: str = "") -> Tuple[str, Set[str]]:
        """
        Disassemble bytes with pickletools.genops and collect GLOBAL imports.
        Returns (disassembly_text, set_of_imports). On failure, disassembly_text
        contains an explanatory message and imports is empty.
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
        Inspect ZIP entries safely (no extraction), disassembling entries that
        look like pickles according to PICKLE_FILE_FORMATS. Returns list of
        disassembly lines and collected global imports.
        """
        dis_lines: List[str] = []
        global_imports: Set[str] = set()

        with zipfile.ZipFile(path, "r") as z:
            infos = z.infolist()
            if len(infos) > MAX_FILES:
                msg = f"[Archive contains too many entries ({len(infos)}); skipping detailed analysis]"
                cls.logger.warning(msg)
                return ([msg], set())

            total_uncompressed = 0
            for info in infos:
                if info.is_dir():
                    continue
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                    cls.logger.warning("Archive total uncompressed size exceeds limit; aborting detailed inspection.")
                    break
                name = info.filename
                if not any(name.lower().endswith(ext) for ext in PICKLE_FILE_FORMATS):
                    continue
                if info.file_size > MAX_UNCOMPRESSED_PER_ENTRY:
                    cls.logger.warning(f"Skipping {name}: uncompressed size {info.file_size} > per-entry limit.")
                    dis_lines.append(f"{name}: [skipped - too large]")
                    continue
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
                    cls.logger.debug(f"Failed to read/archive-entry {name}: {e}")
                    dis_lines.append(f"{name}: [read error: {e}]")

        return (dis_lines, global_imports)

    @classmethod
    def analyze_pickle(cls, filepath: str) -> PickleAnalysis:
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
            return PickleAnalysis(filename=str(path), disassembly=f"[Analysis error: {e}]", global_imports=set(), error=str(e))

    @classmethod
    def analyze_directory(self, dirpath: str) -> List[PickleAnalysis]:
        """Calls analyze_pickle on all pickle files inside target directory"""
        pickle_analyses = []

        for file_path in Path(dirpath).rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in PICKLE_FILE_FORMATS:
                try:
                    analysis = self.analyze_pickle(file_path)
                    pickle_analyses.append(analysis)
                except Exception as e:
                    self.logger.error(f"Failed to analyze pickle file {file_path}: {e}")

        return pickle_analyses