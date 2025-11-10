"""PickleChecker - A security analysis tool for Python pickle files and ML models."""

__version__ = "1.0.0"
__author__ = "Prehistoic"
__license__ = "BSD-3-Clause"

from picklechecker.console.banner import display_banner

display_banner()

from picklechecker.utils.logging_helper import setup_logging

setup_logging()
