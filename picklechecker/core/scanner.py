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


class PickleScanner:
    """
    Scanner class for analyzing pickle files and extracting global references.
    """

    logger = logging.getLogger(__name__)

    @classmethod
    def _list_globals(cls, data: IO[bytes], result: AnalysisResult) -> None:
        """
        Parses pickle opcodes from the data stream and extracts global references.

        This method attempts to scan as much as possible, even if errors occur.
        If opcodes are found despite errors, status is COMPLETED_WITH_ERRORS; otherwise FAILED.

        Args:
            data (IO[bytes]): Binary stream of pickle data.
            result (AnalysisResult): The result object to update with findings.
        """
        ops = []
        got_an_error = False

        # Attempt to parse all opcodes; continue even if errors occur
        try:
            for op in pickletools.genops(data):
                ops.append(op)
        except Exception as e:
            cls.logger.warning(f"Error while parsing pickle: {e}")
            got_an_error = True

        memo: dict[int, Any] = {}
        globals_set = set()

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
                            memo.get(int(prev_op[1]) if prev_op[1] is not None else 0, "unknown")
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
                        values.append("unknown")
                    else:
                        values.append(prev_op[1] if prev_op[1] is not None else "unknown")
                    if len(values) == 2:
                        break
                if len(values) != 2:
                    result.errors.append(
                        f"STACK_GLOBAL at position {n}: found {len(values)} values instead of 2"
                    )
                    continue
                module, name = (
                    values[1] if values[1] is not None else "unknown",
                    values[0] if values[0] is not None else "unknown",
                )
                globals_set.add((module, name))
                result.add_global(module, name, "STACK_GLOBAL", n)

        # Set status based on whether errors occurred and opcodes were found
        if got_an_error:
            result.status = AnalysisStatus.COMPLETED_WITH_ERRORS if ops else AnalysisStatus.FAILED
        else:
            result.status = AnalysisStatus.COMPLETED

    @classmethod
    def scan_file(cls, filepath: str | Path) -> AnalysisResult:
        """
        Scans a single file for pickle safety.

        Args:
            filepath (str | Path): Path to the file to scan.

        Returns:
            AnalysisResult: The analysis result for the file.
        """
        target_filepath = Path(filepath)
        result = AnalysisResult(source_path=target_filepath)

        try:
            blobs = PickleExtractor.extract_pickles_from_filepath(target_filepath)
        except Exception as e:
            cls.logger.error(
                f"Failed to extract pickles from {target_filepath}: {str(e)}", exc_info=True
            )
            result.status = AnalysisStatus.FAILED
            return result

        for blob in blobs:
            try:
                cls._list_globals(io.BytesIO(blob), result)
            except Exception as e:
                cls.logger.error(
                    f"Failed to list globals for blob in {target_filepath}: {str(e)}", exc_info=True
                )
                result.status = AnalysisStatus.FAILED
                return result

        result.compute_safety_level()
        return result

    @classmethod
    def scan_directory(cls, dirpath: str | Path) -> List[AnalysisResult]:
        """
        Scans all files in a directory recursively for pickle safety.

        Skips files in dot-directories or dot-files.

        Args:
            dirpath (str | Path): Path to the directory to scan.

        Returns:
            List[AnalysisResult]: List of analysis results for each file.
        """
        target_dirpath = Path(dirpath)
        results = []

        # Recursively find all files, skipping hidden ones
        for file_path in target_dirpath.rglob("*"):
            if file_path.is_file() and not any(
                part.startswith(".") for part in file_path.parts
            ):  # Skip files in dot-directories or dot-files
                cls.logger.debug(f"Analyzing {file_path}...")
                result = cls.scan_file(file_path)
                result.compute_safety_level()  # Ensure safety level is computed
                results.append(result)

        cls.logger.info(f"Scan finished for directory {dirpath}")
        return results
