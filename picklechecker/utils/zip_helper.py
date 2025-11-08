from typing import IO
import zipfile
import logging

from picklechecker.config import _7Z_FILES_MAGIC


class ZipHelper:
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
            start_pos = data.tell()
            header = data.read(6)
            data.seek(start_pos)  # Reset position

            if len(header) < 6:
                return False

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
        return zipfile.is_zipfile(data)
