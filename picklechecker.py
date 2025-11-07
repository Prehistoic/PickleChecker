import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
import logging

from utils.logging_helper import setup_logging, get_logger
from utils.huggingface_client import HuggingfaceClient
from utils.scanners_helper import ScannersHelper
from utils.console_helper import ConsoleHelper
from reports.pdf_report import PdfReport
from utils.banner import display_banner
from config import PICKLE_FILE_PATTERNS

@click.command()
@click.option("--verbose", "-v", is_flag=True, default=False, help="Verbose mode")
@optgroup.group("Scan Target", cls=RequiredMutuallyExclusiveOptionGroup, help='Exactly one option must be chosen to specify the scan target')
@optgroup.option("--directory", "-d", "scan_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Path to a directory to scan')
@optgroup.option("--file", "-f", "scan_file", type=click.Path(exists=True, file_okay=True, dir_okay=False), help='Path to a specific file to scan')
@optgroup.option("--model", "-m", "hf_model", type=str, help='Huggingface model name to scan')
@click.option("--output-format", "output_format", type=click.Choice(["pdf"]), default=None, help="Output format: pdf. If not provided, no output is generated")
def main(verbose: bool, scan_dir: str | None, scan_file: str | None, hf_model: str | None, output_format: str | None):
    """
    CLI entrypoint for Picklechecker.
    """
    # Display banner
    display_banner()

    # Setup logging
    setup_logging(level=logging.DEBUG) if verbose else setup_logging(level=logging.INFO)
    logger = get_logger(__name__)

    # Determine target and run scans
    if scan_dir:
        logger.info("Launching directory scan: %s", scan_dir)
        scanner_results, pickle_analyses = ScannersHelper.run_directory_scan_all_scanners(scan_dir)
        target = scan_dir
        target_type = "dir"
    elif scan_file:
        logger.info("Launching file scan: %s", scan_file)
        scanner_results, pickle_analyses = ScannersHelper.run_file_scan_all_scanners(scan_file)
        target = scan_file
        target_type = "file"
    else:
        logger.info("Launching Huggingface model scan: %s", hf_model)
        hf_client = HuggingfaceClient()
        download_dir = hf_client.download_repo(hf_model, allow_patterns=PICKLE_FILE_PATTERNS)
        scanner_results, pickle_analyses = ScannersHelper.run_directory_scan_all_scanners(download_dir)
        target = hf_model
        target_type = "hf"

    # Exporting results if an output_format has been chosen
    if output_format is None:
        logger.info("No output format specified. Skipping export...")

    elif output_format == "pdf":
        logger.info("Launching export to PDF")
        PdfReport().export(target, target_type, scanner_results, pickle_analyses)

    # Console output
    ConsoleHelper.display_results(scanner_results, pickle_analyses)

if __name__ == "__main__":
    main()