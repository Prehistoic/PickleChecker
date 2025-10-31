from huggingface_hub import snapshot_download, hf_hub_download
from pathlib import Path
import shutil
import os

from utils.logging_helper import get_logger
from config import HF_TOKEN, HF_DOWNLOAD_DIR, HF_ETAG_TIMEOUT

class HuggingfaceClient:
    """
    A dedicated client for interacting with the Hugging Face Hub. 
    Handles authentication, and the downloading of models or individual files.
    """

    logger = get_logger(__name__)

    def __init__(self):
        """
        Initializes the client and prepares the local download directory.
        """

        self.token = HF_TOKEN
        self.download_dir = HF_DOWNLOAD_DIR
        self.etag_timeout = HF_ETAG_TIMEOUT

        shutil.rmtree(self.download_dir, ignore_errors=True)
        os.makedirs(self.download_dir, exist_ok=True)

    def download_repo(self, repo_name: str, allow_patterns: list) -> str:
        """
        Downloads a complete repository snapshot from Hugging Face.

        Args:
            repo_name (str): The repository ID on the Hugging Face Hub (e.g., 'bert-base-uncased')
            allow_patterns (list): A list of patterns to filter files to download

        Returns:
            str: The local path to the downloaded repository

        Raises:
            RuntimeError: If the download fails after logging the error
        """
        self.logger.info(f"Starting full repository download for: {repo_name}")
        try:
            local_path = snapshot_download(
                repo_id=repo_name,
                token=self.token,
                local_dir=self.download_dir,
                etag_timeout=self.etag_timeout,
                allow_patterns=allow_patterns
            )
            self.logger.info(f"Repository {repo_name} successfully downloaded to: {local_path}")
            return local_path
        except Exception as e:
            self.logger.error(f"Failed to download Huggingface repo {repo_name}: {str(e)}")
            return None

    def download_file(self, repo_name: str, filename: str) -> str:
        """
        Downloads a specific file from a Hugging Face repository

        Args:
            repo_name (str): The repository ID on the Hub
            filename (str): The file name to download (e.g., 'config.json')

        Returns:
            str: The local path to the downloaded file
        """
        self.logger.info(f"Starting file download for: {repo_name}/{filename}")
        try:
            file_path = hf_hub_download(
                repo_id=repo_name,
                filename=filename,
                token=self.token,
                local_dir=self.download_dir,
                etag_timeout=self.etag_timeout
            )
            self.logger.info(f"File {filename} successfully downloaded to: {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Failed to download {filename} from Huggingface repo {repo_name}: {str(e)}")
            return None