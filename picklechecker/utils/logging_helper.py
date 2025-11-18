"""
Utility functions for configuring logging in the application.
"""

import logging
import sys


def setup_logging(level=logging.INFO) -> None:
    """
    Sets up the global logging configuration.

    1. Silences all loggers outside of the 'MyProject' hierarchy (third-party libraries).
    2. Configures the root logger for the project.

    Args:
        level: The minimum logging level to display for the root logger.
    """
    # Silence third-party loggers to reduce noise
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    logging.getLogger("filelock").setLevel(logging.CRITICAL)
    logging.getLogger("PIL").setLevel(logging.CRITICAL)

    # Configure the project root logger
    project_root_logger = logging.getLogger()
    project_root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    # Ensure no duplicate handlers if setup_logging is called multiple times
    if not project_root_logger.handlers:
        project_root_logger.addHandler(handler)


def set_global_logging_level(level=logging.INFO) -> None:
    """
    Sets the global logging level for the root logger.

    Args:
        level: The new logging level (e.g., logging.DEBUG, logging.INFO).
    """
    project_root_logger = logging.getLogger()
    project_root_logger.setLevel(level)
