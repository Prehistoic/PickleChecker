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
from picklechecker.config import HF_ALLOW_PATTERNS, HF_IGNORE_PATTERNS

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

# Download Options (relevant for --model)
@optgroup.group("Download Options", help="Options for downloading Hugging Face models")
@optgroup.option(
    "--download-dir",
    "download_dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Directory to download HF models to (uses temp dir if not specified)",
)
@optgroup.option(
    "--full-download",
    "full_download",
    is_flag=True,
    help="Toggle full download of Huggingface model files",
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
    type=click.Choice(["pdf"]),
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
    download_dir: str | None,
    full_download: bool,
    output_path: str | None,
    output_format: str | None,
) -> int:
    """
    CLI entrypoint for PickleChecker
    """
    # Set logging level
    if verbose:
        set_global_logging_level(logging.DEBUG)

    # Update globals
    GlobalHelper.update_globals(add_safe, "safe")
    GlobalHelper.update_globals(add_unsafe, "unsafe")

    # Determine target and run scan
    if scan_dir:
        logger.info("Launching directory scan: %s", scan_dir)
        results = PickleScanner.scan_directory(scan_dir)
        target = scan_dir
        target_type = "dir"
    elif scan_file:
        logger.info("Launching file scan: %s", scan_file)
        results = [PickleScanner.scan_file(scan_file)]
        target = scan_file
        target_type = "file"
    else:
        logger.info("Launching Huggingface model scan: %s", hf_model)

        # Download directory handling
        if download_dir:
            shutil.rmtree(download_dir, ignore_errors=True)
            os.makedirs(download_dir, exist_ok=True)
        else:
            temp_dir = tempfile.TemporaryDirectory()
            download_dir = temp_dir.name

        try:
            hf_client = HuggingfaceClient(download_dir)

            params = {"repo_name": hf_model}
            if not full_download:
                params["allow_patterns"] = HF_ALLOW_PATTERNS
                params["ignore_patterns"] = HF_IGNORE_PATTERNS

            hf_client.download_repo(**params)
        except HuggingfaceClientError as e:
            logger.error(f"Failed to download model from Huggingface: {str(e)}")
            return 1

        results = PickleScanner.scan_directory(download_dir)
        target = hf_model
        target_type = "hf"

    # Exporting results if an output_format has been chosen
    if output_path is None:
        logger.info("No output path specified. Skipping export...")

    else:
        logger.info(f"Launching {output_format.upper()} export...")
        handler = ReportHandler(output_path, output_format)
        handler.save_report(target, target_type, results)

    # Displaying results to console
    ConsoleResultsFormatter.display_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
