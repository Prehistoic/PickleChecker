import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
import tempfile
import shutil
import logging
import sys
import os

from picklechecker.utils.logging_helper import set_global_logging_level
from picklechecker.huggingface.client import HuggingfaceClient, HuggingfaceClientError
from picklechecker.core.scanner import PickleScanner
from picklechecker.config import HF_ALLOW_PATTERNS, HF_IGNORE_PATTERNS

logger = logging.getLogger(__name__)

@click.command()
# General Options
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable verbose logging for detailed output")

# Scan Target Options (exactly one must be chosen)
@optgroup.group("Scan Target", cls=RequiredMutuallyExclusiveOptionGroup, help='Specify the target to scan')
@optgroup.option("--directory", "-d", "scan_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Scan all files in the specified directory')
@optgroup.option("--file", "-f", "scan_file", type=click.Path(exists=True, file_okay=True, dir_okay=False), help='Scan a specific file')
@optgroup.option("--model", "-m", "hf_model", type=str, help='Scan a Hugging Face model by name (e.g., "bert-base-uncased")')

# Download Options (relevant for --model)
@optgroup.group("Download Options", help='Options for downloading Hugging Face models')
@optgroup.option("--download-dir", "download_dir", type=click.Path(file_okay=False, dir_okay=True), help="Directory to download HF models to (uses temp dir if not specified)")

# Output Options
@optgroup.group("Output Options", help='Options for exporting scan results')
@optgroup.option("--output-dir", "output_dir", type=click.Path(file_okay=False, dir_okay=True), help="Directory to save exported results")
@optgroup.option("--output-format", "output_format", type=click.Choice(["pdf"]), help="Format for exported results (pdf only; no export if not specified)")

def main(
    verbose: bool, 
    scan_dir: str | None, 
    scan_file: str | None, 
    hf_model: str | None,
    download_dir: str | None,
    output_dir: str | None,
    output_format: str | None
) -> int:
    """
    CLI entrypoint for PickleChecker
    """
    # Set logging level
    if verbose:
        set_global_logging_level(logging.DEBUG)

    # Determine target and run scan
    if scan_dir:
        logger.info("Launching directory scan: %s", scan_dir)
        results = PickleScanner.scan_directory(scan_dir)
        print(results)
    elif scan_file:
        logger.info("Launching file scan: %s", scan_file)
        results = PickleScanner.scan_file(scan_file)
        print(results)
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
            hf_client.download_repo(hf_model, allow_patterns=HF_ALLOW_PATTERNS, ignore_patterns=HF_IGNORE_PATTERNS)
        except HuggingfaceClientError:
            logger.error("Failed to download model from Huggingface. Exiting...")
            return 1

        results = PickleScanner.scan_directory(download_dir)
        print(results)

    # Exporting results if an output_format has been chosen
    if output_format is None:
        logger.info("No output format specified. Skipping export...")

    elif output_format == "pdf":
        logger.info("Launching export to PDF")

    return 0

if __name__ == "__main__":
    sys.exit(main())