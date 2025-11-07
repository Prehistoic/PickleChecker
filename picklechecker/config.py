import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project metadata
PROJECT_NAME = "PickleChecker"
__version__ = "1.0.0"

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILENAME_NO_EXT = f"{PROJECT_NAME.lower()}_results"

# Huggingface config
HF_TOKEN = os.getenv("HF_TOKEN")
HF_DOWNLOAD_DIR = "downloads"
HF_ETAG_TIMEOUT = 86400

# Logging
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"