import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root relative to this config.py file
PROJECT_ROOT = Path(__file__).parent

# Data directory and file paths (now absolute and relative to PROJECT_ROOT)
DATA_DIR = PROJECT_ROOT / "data"
SAFE_GLOBALS_FILEPATH = DATA_DIR / "safe_globals.json"
UNSAFE_GLOBALS_FILEPATH = DATA_DIR / "unsafe_globals.json"

# Pickle files extensions
RAW_PICKLE_FILES_EXT = {".pkl", ".pickle"}
PYTORCH_FILES_EXT = {".pt", ".pth", ".bin"}
NUMPY_FILES_EXT = {".npy"}  # .npz is handled as a zip file
ZIP_FILES_EXT = {".zip", ".7z", ".npz"}
OTHER_FILES_EXT = {".joblib", ".data", ".dat"}

PICKLE_FILE_FORMATS = list(
    RAW_PICKLE_FILES_EXT | PYTORCH_FILES_EXT | NUMPY_FILES_EXT | ZIP_FILES_EXT | OTHER_FILES_EXT
)

# Pickle files magic bytes
RAW_PICKLE_FILES_MAGIC = {
    b"\x80\x02",  # Protocol 0, 1, 2
    b"\x80\x03",  # Protocol 3
    b"\x80\x04",  # Protocol 4
    b"\x80\x05",  # Protocol 5
}
NUMPY_FILES_MAGIC = b"\x93NUMPY"
ZIP_FILES_MAGIC = {b"PK\x03\x04", b"PK\x05\x06"}  # Empty zip
_7Z_FILES_MAGIC = b"7z\xbc\xaf'\x1c"

# copied from pytorch code
# https://github.com/pytorch/pytorch/blob/664058fa83f1d8eede5d66418abff6e20bd76ca8/torch/serialization.py#L28
PYTORCH_FILES_MAGIC = 0x1950A86A20F9469CFC6C

# Huggingface config
HF_TOKEN = os.getenv("HF_TOKEN")
HF_ETAG_TIMEOUT = 86400
HF_ALLOW_PATTERNS = [f"*{format}" for format in PICKLE_FILE_FORMATS]
HF_IGNORE_PATTERNS: list[str] = []
