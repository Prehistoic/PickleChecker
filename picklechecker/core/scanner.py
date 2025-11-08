import logging
from typing import IO, List
from pathlib import Path
import pickletools

from picklechecker.core.results import AnalysisResult, AnalysisStatus
from picklechecker.core.extractor import PickleExtractor


class PickleScanner:
    logger = logging.getLogger(__name__)

    @classmethod
    def _list_globals(cls, data: IO[bytes], result: AnalysisResult) -> None:
        ops = []
        got_an_error = False

        # We attempt to scan imports for as much as we can until we encounter an error.
        # If the opcodes are still empty after the error we consider the analysis completely failed
        # If not we consider it has at least worked to some extent
        try:
            for op in pickletools.genops(data):
                ops.append(op)
        except Exception as e:
            cls.logger.warning(f"Error while parsing pickle: {e}")
            got_an_error = True

        memo = {}
        globals_set = set()

        for n, op in enumerate(ops):
            op_name = op[0].name
            op_value = op[1]

            # Update opcode counts
            result.opcode_counts[op_name] = result.opcode_counts.get(op_name, 0) + 1

            # Handle memoization
            if op_name == "MEMOIZE" and n > 0:
                memo[len(memo)] = ops[n - 1][1]
            elif op_name in ["PUT", "BINPUT", "LONG_BINPUT"] and n > 0:
                memo[op_value] = ops[n - 1][1]

            # Handle GLOBAL and INST (similar to GLOBAL)
            elif op_name in ("GLOBAL", "INST"):
                try:
                    module, name = op_value.split(" ", 1)
                except ValueError:
                    module, name = ("<unknown>", str(op_value))
                globals_set.add((module, name))
                result.add_global(module, name, op_name, n)

            # Handle STACK_GLOBAL by inspecting the stack
            elif op_name == "STACK_GLOBAL":
                values = []
                for offset in range(1, n + 1):
                    prev_op = ops[n - offset]
                    prev_name = prev_op[0].name
                    if prev_name in ["MEMOIZE", "PUT", "BINPUT", "LONG_BINPUT"]:
                        continue
                    if prev_name in ["GET", "BINGET", "LONG_BINGET"]:
                        values.append(memo.get(int(prev_op[1]), "unknown"))
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
                        values.append(prev_op[1])
                    if len(values) == 2:
                        break
                if len(values) != 2:
                    result.errors.append(
                        f"STACK_GLOBAL at position {n}: found {len(values)} values instead of 2"
                    )
                    continue
                module, name = values[1], values[0]
                globals_set.add((module, name))
                result.add_global(module, name, "STACK_GLOBAL", n)

        if got_an_error:
            result.status = AnalysisStatus.COMPLETED_WITH_ERRORS if ops else AnalysisStatus.FAILED
        else:
            result.status = AnalysisStatus.COMPLETED

    @classmethod
    def scan_file(cls, filepath: str | Path) -> AnalysisResult:
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
                cls._list_globals(blob, result)
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
        target_dirpath = Path(dirpath)
        results = []

        # rglob('*') recursively yields every file and directory in the tree.
        # We then filter for files and extensions associated with pickle.
        for file_path in target_dirpath.rglob("*"):
            if file_path.is_file() and not any(
                part.startswith(".") for part in file_path.parts
            ):  # Skip files in dot-directories or dot-files:
                cls.logger.debug(f"Analyzing {file_path}...")
                result = cls.scan_file(file_path)
                result.compute_safety_level()
                results.append(result)

        cls.logger.info(f"Scan finished for directory {dirpath}")
        return results
