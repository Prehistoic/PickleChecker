import click
from typing import Tuple
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
import tempfile
import shutil
import logging
import sys
import os

from picklechecker.utils.logging_helper import set_global_logging_level
from picklechecker.huggingface.client import HuggingfaceClient, HuggingfaceClientError
from picklechecker.core.scanner import PickleScanner
from picklechecker.core.globals import GlobalHelper
from picklechecker.console.formatter import ConsoleResultsFormatter
from picklechecker.reports.handler import ReportHandler
from picklechecker.config import (
    HF_ALLOW_PATTERNS,
    HF_IGNORE_PATTERNS,
    ARTIFACTS_DIR,
    DISASSEMBLY_DIR,
    DOWNLOADS_DIR,
)

logger = logging.getLogger(__name__)


@click.command()
# General Options
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose logging for detailed output",
)

# Globals Update Options
@optgroup.group("Globals Update", help="Specify new Globals to allow/disallow")
@optgroup.option(
    "--add-safe",
    multiple=True,
    help="Add safe global in format 'module:name' or path to JSON file (can be used multiple times)",
)
@optgroup.option(
    "--add-unsafe",
    multiple=True,
    help="Add unsafe global in format 'module:name' or path to JSON file (can be used multiple times)",
)

# Scan Target Options (exactly one must be chosen)
@optgroup.group(
    "Scan Target", cls=RequiredMutuallyExclusiveOptionGroup, help="Specify the target to scan"
)
@optgroup.option(
    "--directory",
    "-d",
    "scan_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Scan all files in the specified directory",
)
@optgroup.option(
    "--file",
    "-f",
    "scan_file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Scan a specific file",
)
@optgroup.option(
    "--model",
    "-m",
    "hf_model",
    type=str,
    help='Scan a Hugging Face model by name (e.g., "bert-base-uncased")',
)

# Output Options
@optgroup.group("Output Options", help="Options for exporting scan results")
@optgroup.option(
    "--output",
    "output_path",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Path where results should be saved (no export if not specified)",
)
@optgroup.option(
    "--format",
    "output_format",
    type=click.Choice(["pdf", "json"]),
    default="pdf",
    help="Format for exported results (default=pdf)",
)
def main(
    verbose: bool,
    add_safe: Tuple[str, ...],
    add_unsafe: Tuple[str, ...],
    scan_dir: str | None,
    scan_file: str | None,
    hf_model: str | None,
    output_path: str | None,
    output_format: str,
) -> int:
    """
    CLI entrypoint for PickleChecker
    """
    # Set logging level
    if verbose:
        set_global_logging_level(logging.DEBUG)

    # Update globals
    GlobalHelper.update_globals(list(add_safe), "safe")
    GlobalHelper.update_globals(list(add_unsafe), "unsafe")

    # Prepare artifacts directories
    shutil.rmtree(ARTIFACTS_DIR, ignore_errors=True)
    os.makedirs(DISASSEMBLY_DIR, exist_ok=True)
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    # Determine target and run scan
    if scan_dir:
        logger.info("Launching directory scan: %s", scan_dir)
        results = PickleScanner.scan_directory(scan_dir)

    elif scan_file:
        logger.info("Launching file scan: %s", scan_file)
        results = [PickleScanner.scan_file(scan_file)]

    else:
        logger.info("Launching Huggingface model scan: %s", hf_model)

        try:
            hf_client = HuggingfaceClient(DOWNLOADS_DIR)

            hf_client.download_repo(
                repo_name=hf_model,
                allow_patterns=HF_ALLOW_PATTERNS,
                ignore_patterns=HF_IGNORE_PATTERNS,
            )
        except HuggingfaceClientError as e:
            logger.error(f"Failed to download model from Huggingface: {str(e)}")
            return 1

        results = PickleScanner.scan_directory(DOWNLOADS_DIR)

    target = scan_dir or scan_file or hf_model
    target_type = "dir" if scan_dir else "file" if scan_file else "hf"

    # Saving disassembled pickle objects
    logger.info(f"Saving disassembled pickle objects...")
    for result in results:
        with open(DISASSEMBLY_DIR / f"{result.source_path.name}.dis", "w") as f:
            f.write(result.disassembly)

    # Exporting results if an output_path has been chosen
    if output_path:
        logger.info(f"Launching {output_format.upper()} export...")
        handler = ReportHandler(output_path, output_format)
        handler.save_report(target, target_type, results)
    else:
        logger.info("No output path specified. Skipping export...")

    # Displaying results to console
    ConsoleResultsFormatter.display_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
