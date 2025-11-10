"""
Utility functions for handling ZIP and 7z archives.
"""

from typing import IO
import zipfile
import logging

from picklechecker.config import _7Z_FILES_MAGIC


class ZipHelper:
    """
    Helper class for ZIP and 7z file detection and handling.
    """

    logger = logging.getLogger(__name__)

    @classmethod
    def _is_7z_file(cls, data: IO[bytes]) -> bool:
        """
        Check if the file starts with the 7z magic number.

        Args:
            data: bytes stream

        Returns:
            True if the file is a 7z archive, False otherwise.
        """
        try:
            # Save current position to reset later
            start_pos = data.tell()
            # Read the first 6 bytes for the 7z magic number
            header = data.read(6)
            # Reset to original position
            data.seek(start_pos)

            # Ensure we read enough bytes
            if len(header) < 6:
                return False

            # Compare with the expected 7z magic number
            return header == _7Z_FILES_MAGIC

        except (OSError, IOError) as e:
            cls.logger.debug(f"Error reading file header: {e}")
            return False

    @classmethod
    def _is_zip_file(cls, data: IO[bytes]) -> bool:
        """
        Check if the file is a ZIP archive.

        Args:
            data: bytes stream

        Returns:
            True if the file is a ZIP archive, False otherwise.
        """
        # Use zipfile.is_zipfile to check for ZIP magic number
        return zipfile.is_zipfile(data)
