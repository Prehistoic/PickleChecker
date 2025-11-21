"""
Utility class for extracting pickled streams from various file formats.
"""

from typing import IO, List, Optional
from pathlib import Path
import numpy as np
from tarfile import TarError
import zipfile
import tempfile
import py7zr
import logging
import os

from picklechecker.config import (
    RAW_PICKLE_FILES_EXT,
    RAW_PICKLE_FILES_MAGIC,
    NUMPY_FILES_EXT,
    NUMPY_FILES_MAGIC,
    PYTORCH_FILES_EXT,
    PYTORCH_FILES_MAGIC,
    ZIP_FILES_MAGIC,
)
from picklechecker.utils.relaxed_zipfile import RelaxedZipFile
from picklechecker.utils.torch_helper import TorchHelper, InvalidMagicError
from picklechecker.utils.zip_helper import ZipHelper


class PickleExtractor:
    """
    Utility class for extracting pickled streams from different file formats.
    """

    logger = logging.getLogger(__name__)

    @classmethod
    def extract_pickles_from_filepath(cls, filepath: str | Path) -> List[bytes]:
        """
        Extracts pickle streams from a file by opening it and delegating to byte extraction.

        Args:
            filepath (str | Path): Path to the file to extract from.

        Returns:
            List[bytes]: List of extracted pickle byte streams.
        """
        cls.logger.debug(f"Extracting pickles from {filepath}")

        file_ext = os.path.splitext(filepath)[1]
        with open(filepath, "rb") as file:
            return cls.extract_pickles_from_bytes(file, file_ext)

    @classmethod
    def extract_pickles_from_pickle_bytes(cls, data: IO[bytes]) -> List[bytes]:
        """
        Verifies and extract pickle streams from pickle byte raw data

        Args:
            data (IO[bytes]): Binary file-like object containing the data.

        Returns:
            List[bytes]: List of extracted pickle byte streams.
        """
        cls.logger.debug("Extracting pickles from pickle bytes")
        return [data.read()]
    
    @classmethod
    def extract_pickles_from_bytes(
        cls, data: IO[bytes], file_ext: Optional[str] = None
    ) -> List[bytes]:
        """
        Extracts pickle streams from byte data, handling different file formats.

        Args:
            data (IO[bytes]): Binary file-like object containing the data.
            file_ext (Optional[str]): File extension to aid format detection.

        Returns:
            List[bytes]: List of extracted pickle byte streams.
        """
        cls.logger.debug("Extracting pickles from bytes")

        # Check for PyTorch files first
        if file_ext is not None and file_ext in PYTORCH_FILES_EXT:
            try:
                return cls.extract_pickles_from_pytorch(data)
            except InvalidMagicError as e:
                cls.logger.warning(
                    f"Invalid PyTorch magic number for file {e}. Trying to scan as non-PyTorch file."
                )
                data.seek(0)

        # Check for NumPy files
        if file_ext is not None and file_ext in NUMPY_FILES_EXT:
            return cls.extract_pickles_from_numpy(data)

        # Check for ZIP archives
        is_zip = ZipHelper._is_zip_file(data)
        data.seek(0)
        if is_zip:
            return cls.extract_pickles_from_zip(data)
        elif ZipHelper._is_7z_file(data):
            return cls.extract_pickles_from_7z(data)
        else:
            # Assume raw pickle file
            return cls.extract_pickles_from_pickle_bytes(data)

    @classmethod
    def extract_pickles_from_7z(cls, data: IO[bytes]) -> List[bytes]:
        """
        Extracts pickle streams from a 7z archive.

        Args:
            data (IO[bytes]): Binary file-like object containing the 7z data.

        Returns:
            List[bytes]: List of extracted pickle byte streams.
        """
        cls.logger.debug("Extracting pickles from 7z archive")

        if not ZipHelper._is_7z_file(data):
            cls.logger.warning(f"Failed to extract pickles. Not a valid 7z archive.")
            return []

        extracted_pickles = []

        with py7zr.SevenZipFile(data, mode="r") as archive:
            filenames = archive.getnames()
            # Filter for files with pickle extensions
            targets = [f for f in filenames if f.endswith(tuple(RAW_PICKLE_FILES_EXT))]
            cls.logger.debug(f"Target files in 7z archive : {', '.join(targets)}")

            # Extract to temp directory and process
            with tempfile.TemporaryDirectory() as tmpdir:
                archive.extract(path=tmpdir, targets=targets)
                for filename in targets:
                    tmp_filepath = os.path.join(tmpdir, filename)
                    cls.logger.debug(f"Found raw pickle {tmp_filepath} in 7z archive")

                    if os.path.isfile(tmp_filepath):
                        extracted_pickles.extend(cls.extract_pickles_from_filepath(tmp_filepath))

        return extracted_pickles

    @classmethod
    def extract_pickles_from_zip(cls, data: IO[bytes]) -> List[bytes]:
        """
        Extracts pickle streams from a ZIP archive.

        Args:
            data (IO[bytes]): Binary file-like object containing the ZIP data.

        Returns:
            List[bytes]: List of extracted pickle byte streams.
        """
        cls.logger.debug(f"Extracting pickles from ZIP archive")

        if not zipfile.is_zipfile(data):
            cls.logger.warning(f"Failed to extract pickles. Not a valid ZIP archive.")
            return []

        extracted_pickles = []

        with RelaxedZipFile(data, "r") as zip:
            filenames = zip.namelist()
            cls.logger.debug(f"Found {len(filenames)} files")

            for filename in filenames:
                try:
                    # Read magic bytes to check file type
                    with zip.open(filename, "r") as file:
                        magic_bytes = file.read(max(len(magic) for magic in RAW_PICKLE_FILES_MAGIC))

                    file_ext = os.path.splitext(filename)[1]

                    # Check if it's a raw pickle or NumPy file
                    if file_ext in RAW_PICKLE_FILES_EXT or any(
                        magic_bytes.startswith(mn) for mn in RAW_PICKLE_FILES_MAGIC
                    ):
                        cls.logger.debug(f"Found raw pickle file {filename}")
                        with zip.open(filename, "r") as file:
                            extracted_pickles.extend(cls.extract_pickles_from_pickle_bytes(file))

                    elif file_ext in NUMPY_FILES_EXT or magic_bytes.startswith(NUMPY_FILES_MAGIC):
                        cls.logger.debug(f"Found numpy file {filename}")
                        with zip.open(filename, "r") as file:
                            extracted_pickles.extend(cls.extract_pickles_from_numpy(file))

                except (zipfile.BadZipFile, RuntimeError) as e:
                    # Handle corrupted or password-protected files
                    cls.logger.warning(f"Invalid file {filename} in zip archive: {str(e)}")

        return extracted_pickles

    @classmethod
    def extract_pickles_from_numpy(cls, data: IO[bytes]) -> List[bytes]:
        """
        Extracts pickle streams from a NumPy .npy or .npz file.

        Args:
            data (IO[bytes]): Binary file-like object containing the NumPy data.

        Returns:
            List[bytes]: List of extracted pickle byte streams.
        """
        cls.logger.debug(f"Extracting pickles from numpy file")

        N = len(NUMPY_FILES_MAGIC)
        magic = data.read(N)

        # Seek back to avoid reading past the start
        data.seek(-min(N, len(magic)), 1)

        if magic.startswith(tuple(ZIP_FILES_MAGIC)):
            # .npz files are ZIP archives, but not handled here
            cls.logger.warning(f".npz file not handled as zip file")
            return []

        elif magic == NUMPY_FILES_MAGIC:
            # Read NumPy file header
            version = np.lib.format.read_magic(data)
            np.lib.format._check_version(version)
            _, _, dtype = np.lib.format._read_array_header(data, version)

            if dtype.hasobject:
                # Contains pickled objects
                return cls.extract_pickles_from_pickle_bytes(data)
            else:
                cls.logger.info("File does not contain any pickled data")
                return []

        else:
            # Fallback: treat as raw pickle
            return cls.extract_pickles_from_pickle_bytes(data)

    @classmethod
    def extract_pickles_from_pytorch(cls, data: IO[bytes]) -> List[bytes]:
        """
        Extracts pickle streams from a PyTorch model file.

        Args:
            data (IO[bytes]): Binary file-like object containing the PyTorch data.

        Returns:
            List[bytes]: List of extracted pickle byte streams.
        """
        cls.logger.debug(f"Extracting pickles from pytorch file")

        # New PyTorch format (ZIP-based)
        if TorchHelper._is_zipfile(data):
            return cls.extract_pickles_from_zip(data)
        elif ZipHelper._is_7z_file(data):
            return cls.extract_pickles_from_7z(data)

        # Old PyTorch format (TAR-based)
        else:
            should_read_directly = TorchHelper._should_read_directly(data)
            if should_read_directly and data.tell() == 0:
                try:
                    # TODO: Implement TAR extraction for legacy PyTorch format
                    raise TarError()
                except TarError:
                    # Not a valid TAR, reset and continue
                    data.seek(0)

            # Validate PyTorch magic number
            magic = TorchHelper.get_magic_number(data)
            if magic != PYTORCH_FILES_MAGIC:
                raise InvalidMagicError(magic, PYTORCH_FILES_MAGIC)

            # Legacy Pytorch models are actually one raw pickle byte stream. Thus we simply return the raw data
            return cls.extract_pickles_from_pickle_bytes(data)
