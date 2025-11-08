from dataclasses import dataclass
from typing import List
import logging
import json
import os

from picklechecker.core.safety import SafetyLevel
from picklechecker.config import SAFE_GLOBALS_FILEPATH, UNSAFE_GLOBALS_FILEPATH

SAFE_GLOBALS = json.load(open(SAFE_GLOBALS_FILEPATH))
UNSAFE_GLOBALS = json.load(open(UNSAFE_GLOBALS_FILEPATH))


@dataclass
class GlobalReference:
    module: str
    name: str
    opcode: str
    line: int  # sequential index of opcode
    safety: SafetyLevel


class GlobalHelper:
    logger = logging.getLogger(__name__)

    @classmethod
    def update_globals(cls, items: List[str], label: str):
        if not items:
            cls.logger.debug(f"No {label} globals update: empty list")
            return

        if label not in ["safe", "unsafe"]:
            cls.logger.error(f"Unknown label {label}. Skipping globals update...")
            return

        globals_dict = UNSAFE_GLOBALS if label == "unsafe" else SAFE_GLOBALS

        for item in items:
            if os.path.isfile(item):
                # Load from JSON file
                try:
                    with open(item, "r") as f:
                        data = json.load(f)

                    # Merge into globals_dict
                    for module, names in data.items():
                        if module not in globals_dict:
                            globals_dict[module] = {}

                        globals_dict[module].update(names)

                    cls.logger.info(f"Loaded {label} globals from {item}")

                except Exception as e:
                    cls.logger.error(f"Failed to load JSON from {item}: {e}")

            else:
                # Parse as module:name string
                try:
                    module, name = item.split(":", 1)

                    if module not in globals_dict:
                        globals_dict[module] = {}
                    globals_dict[module][name] = True

                    cls.logger.info(f"Added {module}:{name} to {label} globals")
                except ValueError:
                    cls.logger.error(f"Invalid format for --add-{label}: {item}. Use 'module:name'")
