"""
Module for managing global references and safety levels for modules and functions.
Loads safe and unsafe globals from JSON files and provides utilities for runtime updates.
"""

from dataclasses import dataclass
from typing import List
import logging
import json
import os

from picklechecker.core.safety import SafetyLevel
from picklechecker.config import SAFE_GLOBALS_FILEPATH, UNSAFE_GLOBALS_FILEPATH

# Load safe and unsafe globals from JSON files
# These are used to determine safety levels of imported modules/functions
try:
    with open(SAFE_GLOBALS_FILEPATH, "r") as f:
        SAFE_GLOBALS = json.load(f)
except FileNotFoundError:
    logging.warning(f"SAFE_GLOBALS_FILEPATH not found: {SAFE_GLOBALS_FILEPATH}. Using empty dict.")
    SAFE_GLOBALS = {}
except json.JSONDecodeError as e:
    logging.error(f"Error loading SAFE_GLOBALS: {e}. Using empty dict.")
    SAFE_GLOBALS = {}

try:
    with open(UNSAFE_GLOBALS_FILEPATH, "r") as f:
        UNSAFE_GLOBALS = json.load(f)
except FileNotFoundError:
    logging.warning(
        f"UNSAFE_GLOBALS_FILEPATH not found: {UNSAFE_GLOBALS_FILEPATH}. Using empty dict."
    )
    UNSAFE_GLOBALS = {}
except json.JSONDecodeError as e:
    logging.error(f"Error loading UNSAFE_GLOBALS: {e}. Using empty dict.")
    UNSAFE_GLOBALS = {}


@dataclass
class GlobalReference:
    """
    Represents a reference to a global module/function found in a pickle stream.

    Attributes:
        module (str): The module name (e.g., 'os').
        name (str): The function or attribute name (e.g., 'system').
        opcode (str): The pickle opcode where this was found.
        line (int): Sequential index of the opcode in the stream.
        safety (SafetyLevel): The determined safety level.
    """

    module: str
    name: str
    opcode: str
    line: int  # sequential index of opcode
    safety: SafetyLevel


class GlobalHelper:
    """
    Helper class for managing and updating global safety dictionaries.
    """

    logger = logging.getLogger(__name__)

    @classmethod
    def update_globals(cls, items: List[str], label: str) -> None:
        """
        Updates the global safety dictionaries with new entries from strings or JSON files.

        Args:
            items (List[str]): List of items to add, either 'module:name' strings or JSON file paths.
            label (str): The type of globals to update ('safe' or 'unsafe').

        Raises:
            ValueError: If label is not 'safe' or 'unsafe'.
        """
        if not items:
            cls.logger.debug(f"No {label} globals update: empty list")
            return

        if label not in ["safe", "unsafe"]:
            cls.logger.error(f"Unknown label {label}. Skipping globals update...")
            return

        # Select the appropriate globals dictionary
        globals_dict = UNSAFE_GLOBALS if label == "unsafe" else SAFE_GLOBALS

        for item in items:
            if os.path.isfile(item):
                # Load from JSON file and merge into globals_dict
                try:
                    with open(item, "r") as f:
                        data = json.load(f)

                    # Merge the loaded data
                    for module, names in data.items():
                        if module not in globals_dict:
                            globals_dict[module] = []

                        globals_dict[module].extend(names)

                    cls.logger.info(f"Loaded {label} globals from {item}")

                except Exception as e:
                    cls.logger.error(f"Failed to load JSON from {item}: {e}")

            else:
                # Parse as 'module:name' string
                try:
                    module, name = item.split(":", 1)

                    if module not in globals_dict:
                        globals_dict[module] = []

                    globals_dict[module].append(name)

                    cls.logger.info(f"Added {module}:{name} to {label} globals")
                except ValueError:
                    cls.logger.error(f"Invalid format for --add-{label}: {item}. Use 'module:name'")
                except Exception as e:
                    cls.logger.error(f"Unknown error when adding new gloabl {item} : {str(e)}", exc_info=True)
