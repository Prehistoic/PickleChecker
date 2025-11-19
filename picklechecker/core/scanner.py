"""
Module for scanning files and directories for pickle safety.
"""

import logging
from typing import IO, List, Any
from pathlib import Path
import pickletools
import io

from picklechecker.core.results import AnalysisResult, AnalysisStatus
from picklechecker.core.extractor import PickleExtractor

from picklechecker.config import EXCLUDE_FILES, EXCLUDE_DIRECTORIES


class PickleScanner:
    """
    Scanner class for analyzing pickle files and extracting global references.
    """

    logger = logging.getLogger(__name__)

    @classmethod
    def _list_globals(
        cls, data: IO[bytes], result: AnalysisResult, multiple_pickles: bool = True
    ) -> None:
        """
        Parses pickle opcodes from the data stream and extracts global references.

        This method attempts to scan as much as possible, even if errors occur.
        If opcodes are found despite errors, status is COMPLETED_WITH_ERRORS; otherwise FAILED.

        Args:
            data (IO[bytes]): Binary stream of pickle data.
            result (AnalysisResult): The result object to update with findings.
            multiple_pickles (bool): whether the data can contain several pickles at once
        """
        memo: dict[int, Any] = {}
        globals_set = set()

        last_byte = b"dummy"

        while last_byte != b"":
            # Attempt to parse all opcodes; continue even if errors occur
            ops = []
            try:
                for op in pickletools.genops(data):
                    ops.append(op)
            except Exception as e:
                cls.logger.warning(f"Error while parsing pickle: {e}")
                result.errors.append(f"Pickle parsing error: {str(e)}")

            last_byte = data.read(1)
            data.seek(-1, 1)

            for n, op in enumerate(ops):
                op_name = op[0].name
                op_value = op[1]

                # Update opcode counts for analysis
                result.opcode_counts[op_name] = result.opcode_counts.get(op_name, 0) + 1

                # Handle memoization opcodes
                if op_name == "MEMOIZE" and n > 0:
                    memo[len(memo)] = ops[n - 1][1]
                elif op_name in ["PUT", "BINPUT", "LONG_BINPUT"] and n > 0:
                    memo[op_value] = ops[n - 1][1]

                # Handle GLOBAL and INST opcodes (direct module:name)
                elif op_name in ("GLOBAL", "INST"):
                    try:
                        module, name = op_value.split(" ", 1)
                    except ValueError:
                        module, name = ("<unknown>", str(op_value))
                    globals_set.add((module, name))
                    result.add_global(module, name, op_name, n)

                # Handle STACK_GLOBAL by inspecting the stack for module and name
                elif op_name == "STACK_GLOBAL":
                    values = []
                    # Look back through previous opcodes to find the values on the stack
                    for offset in range(1, n + 1):
                        prev_op = ops[n - offset]
                        prev_name = prev_op[0].name
                        if prev_name in ["MEMOIZE", "PUT", "BINPUT", "LONG_BINPUT"]:
                            continue
                        if prev_name in ["GET", "BINGET", "LONG_BINGET"]:
                            values.append(
                                memo.get(
                                    int(prev_op[1]) if prev_op[1] is not None else 0, "<unknown>"
                                )
                            )
                        elif prev_name not in [
                            "SHORT_BINUNICODE",
                            "UNICODE",
                            "BINUNICODE",
                            "BINUNICODE8",
                            "STRING",
                            "BINSTRING",
                            "SHORT_BINSTRING",
                        ]:
                            values.append("<unknown>")
                        else:
                            values.append(prev_op[1] if prev_op[1] is not None else "<unknown>")
                        if len(values) == 2:
                            break
                    if len(values) != 2:
                        result.errors.append(
                            f"STACK_GLOBAL at position {n}: found {len(values)} values instead of 2"
                        )
                        continue
                    module, name = (
                        values[1] if values[1] is not None else "<unknown>",
                        values[0] if values[0] is not None else "<unknown>",
                    )
                    globals_set.add((module, name))
                    result.add_global(module, name, "STACK_GLOBAL", n)

            if not multiple_pickles:
                break

    @classmethod
    def _disassemble_pickle(
        cls, data: IO[bytes], result: AnalysisResult, multiple_pickles: bool = True
    ) -> None:
        """
        Disassembles pickle data into human-readable opcodes.

        Args:
            data (bytes): The pickle data to disassemble
            result (AnalysisResult): The result object to update with findings.
            multiple_pickles (bool): whether the data can contain several pickles at once
        """

        last_byte = b"dummy"

        while last_byte != b"":
            # Attempt to disassemble all streams; continue even if errors occur
            output = io.StringIO()
            try:
                pickletools.dis(data, out=output)
                result.disassembly += output.getvalue()
            except Exception as e:
                cls.logger.warning(f"Error while disassembling pickle: {e}")
                result.errors.append(f"Pickle disassembling error: {str(e)}")
            finally:
                output.close()

            last_byte = data.read(1)
            data.seek(-1, 1)

            if not multiple_pickles:
                break

    @classmethod
    def _should_skip_path(cls, path: Path) -> bool:
        """
        Determines if a path should be skipped during scanning.

        Args:
            path (Path): The path to check.

        Returns:
            bool: True if the path should be skipped, False otherwise.
        """
        # Check if filename is in EXCLUDE_FILES
        if path.name in EXCLUDE_FILES:
            return True

        # Check if any directory in the path is in EXCLUDE_DIRECTORIES
        if any(part in EXCLUDE_DIRECTORIES for part in path.parts):
            return True

        return False

    @classmethod
    def scan_file(cls, filepath: str | Path, scandir: str | Path = None) -> AnalysisResult:
        """
        Scans a single file for pickle safety.

        Args:
            filepath (str | Path): Path to the file to scan.
            scandir (str | Path): Path of the directory scanned (not relevant for single file scans)

        Returns:
            AnalysisResult: The analysis result for the file.
        """
        target_filepath = Path(filepath)
        scandir_path = Path(scandir) if scandir else None

        # Get relative path if scandir is provided, otherwise use absolute path
        if scandir_path:
            try:
                source_path = target_filepath.relative_to(scandir_path)
            except ValueError:
                # If not relative, fall back to absolute path
                source_path = target_filepath
        else:
            source_path = target_filepath

        result = AnalysisResult(source_path=source_path)

        try:
            blobs = PickleExtractor.extract_pickles_from_filepath(target_filepath)
        except Exception as e:
            cls.logger.error(
                f"Failed to extract pickles from {target_filepath}: {str(e)}", exc_info=True
            )
            result.errors.append(f"Extraction failed: {str(e)}")
            result.status = AnalysisStatus.FAILED
            return result

        if not blobs:
            result.errors.append("No pickle streams found in the file.")
            result.status = AnalysisStatus.FAILED
            return result

        for blob in blobs:
            try:
                cls._disassemble_pickle(io.BytesIO(blob), result)
            except Exception as e:
                cls.logger.error(
                    f"Failed to disassemble for blob in {target_filepath}: {str(e)}", exc_info=True
                )
                result.errors.append(f"Disassembling failed for a blob: {str(e)}")
                result.status = AnalysisStatus.FAILED
                return result

            try:
                cls._list_globals(io.BytesIO(blob), result)
            except Exception as e:
                cls.logger.error(
                    f"Failed to list globals for blob in {target_filepath}: {str(e)}", exc_info=True
                )
                result.errors.append(f"Global listing failed for a blob: {str(e)}")
                result.status = AnalysisStatus.FAILED
                return result

        result.status = (
            AnalysisStatus.COMPLETED_WITH_ERRORS if result.errors else AnalysisStatus.COMPLETED
        )
        result.compute_safety_level()
        return result

    @classmethod
    def scan_directory(cls, dirpath: str | Path) -> List[AnalysisResult]:
        """
        Scans all files in a directory recursively for pickle safety.

        Args:
            dirpath (str | Path): Path to the directory to scan.

        Returns:
            List[AnalysisResult]: List of analysis results for each file.
        """
        target_dirpath = Path(dirpath)
        results = []

        # Recursively find all files, skipping hidden ones
        for file_path in target_dirpath.rglob("*"):
            if file_path.is_file() and not cls._should_skip_path(file_path):
                cls.logger.debug(f"Analyzing {file_path}...")
                result = cls.scan_file(filepath=file_path, scandir=target_dirpath)
                result.compute_safety_level()
                results.append(result)

        cls.logger.info(f"Scan finished for directory {dirpath}")
        return results
