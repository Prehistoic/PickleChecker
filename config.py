import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Misc
PROJECT_NAME = "PickleChecker"

# Huggingface config
HF_TOKEN = os.getenv("HF_TOKEN", None)
HF_DOWNLOAD_DIR = os.getenv("HF_DOWNLOAD_DIR", "downloads")
HF_ETAG_TIMEOUT = int(os.getenv("HF_ETAG_TIMEOUT", 86400))

# Pickle files possible formats
BASIC_PICKLE_FILE_FORMATS = [".pkl", ".pickle", ".joblib", ".dat", ".data"]
PYTORCH_FILE_FORMATS = [".pt", ".pth", ".bin", ".ckpt"]
PICKLE_FILE_FORMATS = BASIC_PICKLE_FILE_FORMATS + PYTORCH_FILE_FORMATS
PICKLE_FILE_PATTERNS = [f"*{format}" for format in PICKLE_FILE_FORMATS]