import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
import logging

from utils.logging_helper import setup_logging, get_logger
from utils.huggingface_client import HuggingfaceClient
from utils.scanners_helper import ScannersHelper
from utils.banner import display_banner
from config import PICKLE_FILE_PATTERNS

@click.command()
@click.option("--verbose", "-v", is_flag=True, default=False, help="Verbose mode")
@optgroup.group('Scan Target', cls=RequiredMutuallyExclusiveOptionGroup, help='Exactly one option must be chosen to specify the scan target')
@optgroup.option('--directory', '-d', type=click.Path(exists=True, file_okay=False, dir_okay=True), help='Path to a directory to scan')
@optgroup.option('--file', '-f', type=click.Path(exists=True, file_okay=True, dir_okay=False), help='Path to a specific file to scan')
@optgroup.option('--model', '-m', type=str, help='Huggingface model name to scan')
def main(verbose: bool, directory: str | None, file: str | None, model: str | None):
    # Display banner
    display_banner()

    # Setup logging
    setup_logging(level=logging.DEBUG) if verbose else setup_logging(level=logging.INFO)
    logger = get_logger(__name__)

    if directory:
        ScannersHelper.run_directory_scan_all_scanners(directory)
    elif file:
        ScannersHelper.run_file_scan_all_scanners(file)
    elif model:
        hf_client = HuggingfaceClient()
        download_dir = hf_client.download_repo(model, allow_patterns=PICKLE_FILE_PATTERNS)
        ScannersHelper.run_directory_scan_all_scanners(download_dir)
    else:
        logger.error("No valid scan target provided.")

if __name__ == "__main__":
    main()