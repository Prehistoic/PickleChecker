"""
Utility functions for handling PyTorch model files and magic numbers.
"""

import io
import pickletools
from typing import IO, Optional, Any
import logging


class InvalidMagicError(Exception):
    """
    Exception raised when the magic number in a PyTorch file does not match the expected value.
    """

    def __init__(self, provided_magic: Optional[int], magic: int, file: str):
        """
        Initializes the exception with magic number details.

        Args:
            provided_magic (Optional[int]): The magic number found in the file.
            magic (int): The expected magic number.
            file (str): The file path or name.
        """
        self.provided_magic = provided_magic
        self.magic = magic
        self.file = file
        super().__init__()

    def __str__(self) -> str:
        """
        Returns a string representation of the error.

        Returns:
            str: Error message with file and magic numbers.
        """
        return f"{self.file}: {self.provided_magic} != {self.magic}"


class TorchHelper:
    """
    Helper class for PyTorch-specific file handling operations.
    """

    logger = logging.getLogger(__name__)

    # Copied from PyTorch code
    # https://github.com/pytorch/pytorch/blob/664058fa83f1d8eede5d66418abff6e20bd76ca8/torch/serialization.py#L272
    @classmethod
    def _is_compressed_file(cls, f: Any) -> bool:
        """
        Checks if the file object is compressed (e.g., gzip).

        Args:
            f: The file-like object to check.

        Returns:
            bool: True if the file is compressed, False otherwise.
        """
        compress_modules = ["gzip"]
        try:
            return f.__module__ in compress_modules
        except AttributeError:
            return False

    # Copied from PyTorch code
    # https://github.com/pytorch/pytorch/blob/664058fa83f1d8eede5d66418abff6e20bd76ca8/torch/serialization.py#L280
    @classmethod
    def _should_read_directly(cls, f: Any) -> bool:
        """
        Checks if the file should be read directly (not compressed and has a real file descriptor).

        Args:
            f: The file-like object to check.

        Returns:
            bool: True if the file should be read directly, False otherwise.
        """
        if cls._is_compressed_file(f):
            return False
        try:
            return f.fileno() >= 0
        except io.UnsupportedOperation:
            return False
        except AttributeError:
            return False

    # Copied from PyTorch code
    # https://github.com/pytorch/pytorch/blob/0b3316ad2c6ff61416597ef29e8865876dcb12f5/torch/serialization.py#L66
    @classmethod
    def _is_zipfile(cls, f: IO[bytes]) -> bool:
        """
        Checks if the file is a ZIP file by examining the magic number at the start.

        This is stricter than zipfile.is_zipfile() to avoid false positives.

        Args:
            f: The file-like object to check.

        Returns:
            bool: True if the file starts with the ZIP magic number, False otherwise.
        """
        # Read the first 4 bytes of the file
        read_bytes = []
        start = f.tell()

        byte = f.read(1)
        while byte != b"":
            read_bytes.append(byte)
            if len(read_bytes) == 4:
                break
            byte = f.read(1)
        f.seek(start)

        local_header_magic_number = [b"P", b"K", b"\x03", b"\x04"]
        return read_bytes == local_header_magic_number

    @classmethod
    def get_magic_number(cls, data: IO[bytes]) -> Optional[int]:
        """
        Extracts the magic number from the pickle stream in the data.

        Args:
            data (IO[bytes]): The binary data stream to parse.

        Returns:
            Optional[int]: The magic number if found, None otherwise.
        """
        try:
            # Iterate through pickle opcodes to find an INT or LONG opcode
            for opcode, args, pos in pickletools.genops(data):
                if "INT" in opcode.name or "LONG" in opcode.name:
                    data.seek(0)  # Reset position
                    return int(args)
        except ValueError:
            # Handle parsing errors gracefully
            return None

        return None
