import logging

from huggingface_hub import snapshot_download, hf_hub_download

from picklechecker.config import HF_TOKEN, HF_ETAG_TIMEOUT

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
        self.download_dir = download_dir

        if not self.hf_token:
            self.logger.error("Required environment variable HF_TOKEN is not set !")
            raise

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
                token=self.hf_token,
                local_dir=self.download_dir,
                etag_timeout=self.etag_timeout,
                allow_patterns=allow_patterns
            )
            self.logger.info(f"Repository {repo_name} successfully downloaded to: {local_path}")
        except Exception as e:
            self.logger.error(f"Failed to download Huggingface repo {repo_name}: {str(e)}")
            raise

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
                token=self.hf_token,
                local_dir=self.download_dir,
                etag_timeout=self.etag_timeout
            )
            self.logger.info(f"File {filename} successfully downloaded to: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to download {filename} from Huggingface repo {repo_name}: {str(e)}")
            raise