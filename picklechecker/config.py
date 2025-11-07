import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Huggingface config
HF_TOKEN = os.getenv("HF_TOKEN")
HF_ETAG_TIMEOUT = 86400

PICKLE_FILE_FORMATS = [
    ".pkl", ".pickle",                            # Raw Pickle extensions
    "pytorch_model.bin", ".pt", ".pth", ".ckpt",  # Pytorch extensions
    ".npy", ".npz"                                # Numpy extensions. Note: .npz is handled as zip files
    ".zip", ".7z",                                # Zip file extensions
    ".joblib", ".data", ".dat"                    # Less usual extensions that may contain pickled data
]
HF_ALLOW_PATTERNS = [f"*{format}" if format.startswith(".") else f"**/{format}" for format in PICKLE_FILE_FORMATS]
HF_IGNORE_PATTERNS = []