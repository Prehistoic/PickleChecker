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
    RAW_PICKLE_FILES_EXT, RAW_PICKLE_FILES_MAGIC, 
    NUMPY_FILES_EXT, NUMPY_FILES_MAGIC,
    PYTORCH_FILES_EXT, PYTORCH_FILES_MAGIC,
    ZIP_FILES_MAGIC
)
from picklechecker.utils.relaxed_zipfile import RelaxedZipFile
from picklechecker.utils.torch_helper import TorchHelper, InvalidMagicError
from picklechecker.utils.zip_helper import ZipHelper

class PickleExtractor:
    """
    Utility class for extracting pickled streams from different file formats
    """

    logger = logging.getLogger(__name__)
        
    @classmethod
    def extract_pickles_from_filepath(cls, filepath: str | Path) -> List[bytes]:
        cls.logger.debug(f"Extracting pickles from {filepath}")

        file_ext = os.path.splitext(filepath)[1]
        with open(filepath, "rb") as file:
            return cls.extract_pickles_from_bytes(file, filepath, file_ext)
    
    @classmethod
    def extract_pickles_from_bytes(cls, data: IO[bytes], filepath: str | Path, file_ext: Optional[str] = None) -> List[bytes]:
        cls.logger.debug(f"Extracting pickles from bytes coming from {filepath}")

        if file_ext is not None and file_ext in PYTORCH_FILES_EXT:
            try:
                return cls.extract_pickles_from_pytorch(data, filepath)
            except InvalidMagicError as e:
                cls.logger.warning(f"Invalid PyTorch magic number for file {e}. Trying to scan as non-PyTorch file.")
                data.seek(0)

        if file_ext is not None and file_ext in NUMPY_FILES_EXT:
            return cls.extract_pickles_from_numpy(data, filepath)
        
        is_zip = ZipHelper._is_zip_file(data)
        data.seek(0)
        if is_zip:
            return cls.extract_pickles_from_zip(data, filepath)
        elif ZipHelper._is_7z_file(data):
            return cls.extract_pickles_from_7z(data, filepath)
        else:
            stream = Path(filepath).read_bytes()
            return [stream]

    @classmethod
    def extract_pickles_from_7z(cls, data: IO[bytes], filepath: str | Path) -> List[bytes]:
        cls.logger.debug(f"Extracting pickles from 7z archive {filepath}")

        if not ZipHelper._is_7z_file(data):
            cls.logger.warning(f"Failed to extract pickles from {filepath}. Not a valid 7z archive.")
            return []
        
        extracted_pickles = []

        with py7zr.SevenZipFile(data, mode="r") as archive:
            filenames = archive.getnames()
            targets = [f for f in filenames if f.endswith(tuple(RAW_PICKLE_FILES_EXT))]
            cls.logger.debug(f"Target files in 7z archive {filepath}: {', '.join(targets)}")

            with tempfile.TemporaryDirectory() as tmpdir:
                archive.extract(path=tmpdir, targets=targets)
                for filename in targets:
                    tmp_filepath = os.path.join(tmpdir, filename)
                    cls.logger.debug(f"Found raw pickle {tmp_filepath} in 7z archive {filepath}")

                    if os.path.isfile(tmp_filepath):
                        extracted_pickles.extend(cls.extract_pickles_from_filepath(tmp_filepath))

        return extracted_pickles

    @classmethod
    def extract_pickles_from_zip(cls, data: IO[bytes], filepath: str | Path) -> List[bytes]:
        cls.logger.debug(f"Extracting pickles from ZIP archive {filepath}")

        if not zipfile.is_zipfile(data):
            cls.logger.warning(f"Failed to extract pickles from {filepath}. Not a valid ZIP archive.")
            return []

        extracted_pickles = []

        with RelaxedZipFile(data, "r") as zip:
            filenames = zip.namelist()
            cls.logger.debug(f"Found {len(filenames)} files in {filepath}")

            for filename in filenames:
                try:
                    with zip.open(filename, "r") as file:
                        magic_bytes = file.read(8)

                    file_ext = os.path.splitext(filename)[1]

                    if file_ext in RAW_PICKLE_FILES_EXT or any(magic_bytes.startswith(mn) for mn in RAW_PICKLE_FILES_MAGIC):
                        cls.logger.debug(f"Found raw pickle file {filename} in {filepath}")
                        with zip.open(filename, "r") as file:
                            extracted_pickles.append(file.read())

                    elif file_ext in NUMPY_FILES_EXT or magic_bytes.startswith(NUMPY_FILES_MAGIC):
                        cls.logger.debug(f"Found numpy file {filename} in {filepath}")
                        with zip.open(filename, "r") as file:
                            extracted_pickles.extend(cls.extract_pickles_from_numpy(data, filepath))

                except (zipfile.BadZipFile, RuntimeError) as e:
                    # Log decompression issues (password protected, corrupted, etc.)
                    cls.logger.warning(f"Invalid file {filename} in zip archive {filepath}: {str(e)}")

        return extracted_pickles

    @classmethod
    def extract_pickles_from_numpy(cls,  data: IO[bytes], filepath: str | Path) -> List[bytes]:
        cls.logger.debug(f"Extracting pickles from numpy file {filepath}")

        N = len(NUMPY_FILES_MAGIC)
        magic = data.read(N)

        # If the file size is less than N, we need to make sure not
        # to seek past the beginning of the file
        data.seek(-min(N, len(magic)), 1)  # back-up

        if magic.startswith(tuple(ZIP_FILES_MAGIC)):
            # .npz file
            cls.logger.warning(f".npz file not handled as zip file: {filepath}")

        elif magic == NUMPY_FILES_MAGIC:
            # .npy file
            version = np.lib.format.read_magic(data)
            np.lib.format._check_version(version)
            _, _, dtype = np.lib.format._read_array_header(data, version)

            if dtype.hasobject:
                return [Path(filepath).read_bytes()]
            
            else:
                cls.logger.info(f"{filepath} does not contain any pickled data")
                return []
        
        else:
            return [Path(filepath).read_bytes()]


    @classmethod
    def extract_pickles_from_pytorch(cls, data: IO[bytes], filepath: str | Path) -> List[bytes]:
        cls.logger.debug(f"Extracting pickles from pytorch file {filepath}")

        # New PyTorch format
        if TorchHelper._is_zipfile(data):
            return cls.extract_pickles_from_zip(data, filepath)
        elif ZipHelper._is_7z_file(data):
            return cls.extract_pickles_from_7z(data, filepath)
        
        # Old PyTorch format
        else:
            extracted_pickles = []

            should_read_directly = TorchHelper._should_read_directly(data)
            if should_read_directly and data.tell() == 0:
                try:
                    # TODO: implement loading from tar
                    cls.logger.error(f"Should read {filepath} directly and load it as a tar archive")
                    raise TarError()
                except TarError:
                    # File does not contain a valid tar
                    data.seek(0)
                    return []

            magic = TorchHelper.get_magic_number(data)
            if magic != PYTORCH_FILES_MAGIC:
                raise InvalidMagicError(magic, PYTORCH_FILES_MAGIC, filepath)
            
            for _ in range(5):
                extracted_pickles.extend(cls.extract_pickles_from_bytes(data, filepath))

            return extracted_pickles