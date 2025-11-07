import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
import tempfile
import logging
import sys

from picklechecker.utils.logging_helper import set_global_logging_level
from picklechecker.huggingface.client import HuggingfaceClient

logger = logging.getLogger(__name__)

@click.command()
@click.option("--verbose", "-v", is_flag=True, default=False, help="Verbose mode")
@optgroup.group("Scan Target", cls=RequiredMutuallyExclusiveOptionGroup, help='Exactly one option must be chosen to specify the scan target')
@optgroup.option("--directory", "-d", "scan_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Path to a directory to scan')
@optgroup.option("--file", "-f", "scan_file", type=click.Path(exists=True, file_okay=True, dir_okay=False), help='Path to a specific file to scan')
@optgroup.option("--model", "-m", "hf_model", type=str, help='Huggingface model name to scan')
@click.option("--output-format", "output_format", type=click.Choice(["pdf"]), default=None, help="Output format: pdf. If not provided, no output is generated")
def main(verbose: bool, scan_dir: str | None, scan_file: str | None, hf_model: str | None, output_format: str | None):
    """
    CLI entrypoint for PickleChecker
    """
    # Set logging level
    if verbose:
        set_global_logging_level(logging.DEBUG)

    # Determine target and run scan
    if scan_dir:
        logger.info("Launching directory scan: %s", scan_dir)
    elif scan_file:
        logger.info("Launching file scan: %s", scan_file)
    else:
        logger.info("Launching Huggingface model scan: %s", hf_model)

        try:
            with tempfile.TemporaryDirectory() as download_dir:
                hf_client = HuggingfaceClient(download_dir)
                hf_client.download_repo(hf_model, allow_patterns=[])
        except:
            logger.error("Failed to download model from Huggingface. Exiting...")
            sys.exit(1)

    # Exporting results if an output_format has been chosen
    if output_format is None:
        logger.info("No output format specified. Skipping export...")

    elif output_format == "pdf":
        logger.info("Launching export to PDF")

if __name__ == "__main__":
    main()