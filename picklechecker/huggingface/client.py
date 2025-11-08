import logging
import tempfile
from typing import List

from huggingface_hub import snapshot_download, hf_hub_download

from picklechecker.config import HF_TOKEN, HF_ETAG_TIMEOUT


class HuggingfaceClientError(RuntimeError):
    """Raised for errors originating from HuggingfaceClient operations."""


class HuggingfaceClient:
    """
    A dedicated client for interacting with the Hugging Face Hub.
    Handles authentication, and the downloading of models or individual files.
    """

    logger = logging.getLogger(__name__)

    def __init__(self, download_dir: str):
        """
        Initializes the client and prepares the local download directory.
        """
        self.hf_token = HF_TOKEN
        self.etag_timeout = HF_ETAG_TIMEOUT

        if not self.hf_token:
            self.logger.warning("Environment variable HF_TOKEN is not set !")

        self.download_dir = download_dir

    def download_repo(
        self, repo_name: str, allow_patterns: List = [], ignore_patterns: List = []
    ) -> None:
        """
        Downloads a complete repository snapshot from Hugging Face.

        Args:
            repo_name (str): The repository ID on the Hugging Face Hub (e.g., 'bert-base-uncased')
            allow_patterns (list): A list of patterns to filter files to download

        Raises:
            HuggingfaceClientError: If the download fails
        """
        self.logger.info(f"Starting full repository download for: {repo_name}")
        try:
            params = {
                "repo_id": repo_name,
                "local_dir": self.download_dir,
                "etag_timeout": self.etag_timeout,
            }
            if allow_patterns:
                self.logger.debug(f"Allow Patterns: {allow_patterns}")
                params["allow_patterns"] = allow_patterns

            if ignore_patterns:
                self.logger.debug(f"Ignore Patterns: {ignore_patterns}")
                params["ignore_patterns"] = ignore_patterns

            if self.hf_token:
                self.logger.debug("Using token to authenticate")
                params["token"] = self.hf_token

            local_path = snapshot_download(**params)
            self.logger.info(f"Repository {repo_name} successfully downloaded to: {local_path}")
        except Exception as e:
            raise HuggingfaceClientError(str(e))

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
            params = {
                "repo_id": repo_name,
                "filename": filename,
                "local_dir": self.download_dir,
                "etag_timeout": self.etag_timeout,
            }
            if self.hf_token:
                self.logger.debug("Using token to authenticate")
                params["token"] = self.hf_token

            file_path = hf_hub_download(**params)
            self.logger.info(f"File {filename} successfully downloaded to: {file_path}")
        except Exception as e:
            raise HuggingfaceClientError(
                f"Failed to download file '{filename}' from '{repo_name}'"
            ) from e
