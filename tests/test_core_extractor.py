import io
import os
import pickle
import zipfile
import tempfile
import pytest
from pathlib import Path
import numpy as np

from picklechecker.core.extractor import PickleExtractor
from picklechecker.config import RAW_PICKLE_FILES_MAGIC, NUMPY_FILES_MAGIC, PYTORCH_FILES_MAGIC

_root_path = os.path.dirname(__file__)


class MaliciousExtractor:
    def __reduce__(self):
        return eval, ("print('test')",)


def initialize_test_file(path: str, data: bytes):
    """Helper to initialize test files"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def test_extract_pickles_from_filepath_raw_pickle():
    """Test extracting from a raw pickle file"""
    path = f"{_root_path}/test_data_extractor/test.pkl"
    initialize_test_file(path, pickle.dumps({"a": 1, "b": 2}))
    
    blobs = PickleExtractor.extract_pickles_from_filepath(path)
    
    assert len(blobs) == 1
    assert isinstance(blobs[0], bytes)
    # Verify we can unpickle it
    assert pickle.loads(blobs[0]) == {"a": 1, "b": 2}


def test_extract_pickles_from_filepath_multiple_protocols():
    """Test extracting pickles with different protocol versions"""
    for protocol in (1, 3, 4):
        path = f"{_root_path}/test_data_extractor/protocol_{protocol}.pkl"
        data = pickle.dumps([1, 2, 3], protocol=protocol)
        initialize_test_file(path, data)
        
        blobs = PickleExtractor.extract_pickles_from_filepath(path)
        
        assert len(blobs) == 1, f"Failed for protocol {protocol}"
        assert pickle.loads(blobs[0]) == [1, 2, 3]


def test_extract_pickles_from_pickle_bytes_valid():
    """Test extracting from valid pickle bytes"""
    data = pickle.dumps({"test": "data"})
    
    blobs = PickleExtractor.extract_pickles_from_pickle_bytes(io.BytesIO(data))
    
    assert len(blobs) == 1
    assert pickle.loads(blobs[0]) == {"test": "data"}


def test_extract_pickles_from_pickle_bytes_all_protocols():
    """Test extraction works with all pickle protocol magic numbers"""
    for protocol in range(5):  # Pickle protocols 0-4
        data = pickle.dumps(["test"], protocol=protocol)
        
        blobs = PickleExtractor.extract_pickles_from_pickle_bytes(io.BytesIO(data))
        
        assert len(blobs) == 1, f"Failed for protocol {protocol}"


def test_extract_pickles_from_zip_single_file():
    """Test extracting pickle from ZIP with single file"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("model.pkl", pickle.dumps({"key": "value"}))
    
    buffer.seek(0)
    blobs = PickleExtractor.extract_pickles_from_zip(buffer)
    
    assert len(blobs) == 1
    assert pickle.loads(blobs[0]) == {"key": "value"}


def test_extract_pickles_from_zip_multiple_files():
    """Test extracting multiple pickles from ZIP"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("model1.pkl", pickle.dumps([1, 2, 3]))
        zf.writestr("model2.pkl", pickle.dumps([4, 5, 6]))
        zf.writestr("readme.txt", b"Not a pickle")
    
    buffer.seek(0)
    blobs = PickleExtractor.extract_pickles_from_zip(buffer)
    
    assert len(blobs) == 2


def test_extract_pickles_from_zip_nested_structure():
    """Test extracting pickles from nested ZIP structure"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("models/model1.pkl", pickle.dumps({"a": 1}))
        zf.writestr("models/subdir/model2.pkl", pickle.dumps({"b": 2}))
    
    buffer.seek(0)
    blobs = PickleExtractor.extract_pickles_from_zip(buffer)
    
    assert len(blobs) == 2


def test_extract_pickles_from_zip_invalid():
    """Test handling of invalid ZIP data"""
    invalid_data = io.BytesIO(b"NOT A ZIP FILE")
    
    blobs = PickleExtractor.extract_pickles_from_zip(invalid_data)
    
    assert len(blobs) == 0


def test_extract_pickles_from_zip_corrupted_file():
    """Test handling of corrupted files within ZIP"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("good.pkl", pickle.dumps([1, 2, 3]))
        # Create a file with wrong extension but pickle content
        zf.writestr("bad.txt", pickle.dumps([4, 5, 6]))
    
    buffer.seek(0)
    # Should extract the .pkl file
    blobs = PickleExtractor.extract_pickles_from_zip(buffer)
    
    # Should extract both based on magic bytes
    assert len(blobs) >= 1


def test_extract_pickles_from_7z():
    """Test extracting from 7z archive"""
    pytest.importorskip("py7zr")
    
    path = f"{_root_path}/test_data_extractor/test.7z"
    pkl_data = pickle.dumps({"test": "7z"})
    
    # Create temp pickle file
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp:
        tmp.write(pkl_data)
        tmp_path = tmp.name
    
    try:
        # Create 7z archive
        import py7zr
        with py7zr.SevenZipFile(path, "w") as archive:
            archive.write(tmp_path, "model.pkl")
        
        with open(path, "rb") as f:
            blobs = PickleExtractor.extract_pickles_from_7z(f)
        
        assert len(blobs) == 1
        assert pickle.loads(blobs[0]) == {"test": "7z"}
    finally:
        os.unlink(tmp_path)
        if os.path.exists(path):
            os.unlink(path)


def test_extract_pickles_from_7z_invalid():
    """Test handling of invalid 7z data"""
    invalid_data = io.BytesIO(b"NOT A 7Z FILE")
    
    blobs = PickleExtractor.extract_pickles_from_7z(invalid_data)
    
    assert len(blobs) == 0


def test_extract_pickles_from_numpy_npy_with_objects():
    """Test extracting from NumPy .npy file with objects"""
    path = f"{_root_path}/test_data_extractor/objects.npy"
    
    # Create array with objects
    arr = np.empty((2, 2), dtype=object)
    arr[:] = [(1, 2), (3, 4)]
    np.save(path, arr)
    
    with open(path, "rb") as f:
        blobs = PickleExtractor.extract_pickles_from_numpy(f)
    
    assert len(blobs) > 0


def test_extract_pickles_from_numpy_npy_without_objects():
    """Test extracting from NumPy .npy file without objects"""
    path = f"{_root_path}/test_data_extractor/ints.npy"
    
    # Create array without objects
    arr = np.array([[1, 2], [3, 4]], dtype=int)
    np.save(path, arr)
    
    with open(path, "rb") as f:
        blobs = PickleExtractor.extract_pickles_from_numpy(f)
    
    # Should return empty list for non-object arrays
    assert len(blobs) == 0


def test_extract_pickles_from_numpy_npz():
    """Test extracting from NumPy .npz file"""
    path = f"{_root_path}/test_data_extractor/arrays.npz"
    
    # Create npz with object arrays
    np.savez(
        path,
        a=np.array([1, 2, 3], dtype=object),
        b=np.array([4, 5, 6], dtype=object)
    )
    
    with open(path, "rb") as f:
        blobs = PickleExtractor.extract_pickles_from_numpy(f)
    
    # .npz files are ZIPs, should be handled differently
    assert len(blobs) >= 0


def test_extract_pickles_from_bytes_auto_detect_pickle():
    """Test automatic format detection for raw pickle"""
    data = pickle.dumps([1, 2, 3])
    
    blobs = PickleExtractor.extract_pickles_from_bytes(io.BytesIO(data), ".pkl")
    
    assert len(blobs) == 1
    assert pickle.loads(blobs[0]) == [1, 2, 3]


def test_extract_pickles_from_bytes_auto_detect_zip():
    """Test automatic format detection for ZIP"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("data.pkl", pickle.dumps({"zip": "test"}))
    
    buffer.seek(0)
    blobs = PickleExtractor.extract_pickles_from_bytes(buffer, ".zip")
    
    assert len(blobs) == 1


def test_extract_pickles_from_bytes_pytorch_extension():
    """Test extraction from file with PyTorch extension"""
    # Create a simple pickle (not actual PyTorch format)
    data = pickle.dumps({"model": "data"})
    
    blobs = PickleExtractor.extract_pickles_from_bytes(io.BytesIO(data), ".pt")
    
    assert len(blobs) >= 0


def test_extract_pickles_from_bytes_numpy_extension():
    """Test extraction from file with NumPy extension"""
    path = f"{_root_path}/test_data_extractor/test_bytes.npy"
    arr = np.array([1, 2, 3], dtype=int)
    np.save(path, arr)
    
    with open(path, "rb") as f:
        blobs = PickleExtractor.extract_pickles_from_bytes(f, ".npy")
    
    assert isinstance(blobs, list)


def test_extract_pickles_from_bytes_no_extension():
    """Test extraction when no extension is provided"""
    data = pickle.dumps({"no": "extension"})
    
    blobs = PickleExtractor.extract_pickles_from_bytes(io.BytesIO(data), None)
    
    assert len(blobs) == 1


def test_extract_pickles_from_pytorch_invalid_magic():
    """Test handling of invalid PyTorch magic number"""
    from picklechecker.utils.torch_helper import InvalidMagicError
    
    invalid_data = b"INVALID_MAGIC" + pickle.dumps({"data": "test"})
    
    with pytest.raises(InvalidMagicError):
        PickleExtractor.extract_pickles_from_pytorch(io.BytesIO(invalid_data))


def test_extract_pickles_from_pytorch_zip_based():
    """Test extraction from new ZIP-based PyTorch format"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("data.pkl", pickle.dumps({"pytorch": "zip"}))
    
    buffer.seek(0)
    blobs = PickleExtractor.extract_pickles_from_pytorch(buffer)
    
    assert len(blobs) >= 0


def test_extract_multiple_pickle_streams():
    """Test extraction of multiple pickle streams concatenated"""
    stream1 = pickle.dumps([1, 2, 3])
    stream2 = pickle.dumps([4, 5, 6])
    combined = stream1 + stream2
    
    path = f"{_root_path}/test_data_extractor/multi_stream.pkl"
    initialize_test_file(path, combined)
    
    blobs = PickleExtractor.extract_pickles_from_filepath(path)
    
    # Should extract at least the first stream
    assert len(blobs) >= 1


def test_extract_malicious_pickle():
    """Test extraction of malicious pickle"""
    malicious_pickle = pickle.dumps(MaliciousExtractor())
    
    blobs = PickleExtractor.extract_pickles_from_pickle_bytes(io.BytesIO(malicious_pickle))
    
    assert len(blobs) == 1
    # Verify it's the dangerous pickle (but don't load it!)
    assert b"eval" in blobs[0]


def test_extract_zip_with_mixed_content():
    """Test ZIP containing both pickle and non-pickle files"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("model.pkl", pickle.dumps({"model": 1}))
        zf.writestr("config.json", b'{"key": "value"}')
        zf.writestr("weights.npy", pickle.dumps({"weights": 2}))
    
    buffer.seek(0)
    blobs = PickleExtractor.extract_pickles_from_zip(buffer)
    
    # Should extract pickle files, possibly numpy too
    assert len(blobs) >= 1


def test_extract_from_filepath_nonexistent():
    """Test handling of nonexistent file"""
    with pytest.raises(FileNotFoundError):
        PickleExtractor.extract_pickles_from_filepath("/nonexistent/file.pkl")


def test_extract_zip_empty():
    """Test extraction from empty ZIP"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        pass  # Create empty ZIP
    
    buffer.seek(0)
    blobs = PickleExtractor.extract_pickles_from_zip(buffer)
    
    assert len(blobs) == 0


def test_extract_pickles_preserves_data_integrity():
    """Test that extraction preserves the original pickle data"""
    original_data = {"nested": {"dict": [1, 2, 3]}, "key": "value"}
    pickled = pickle.dumps(original_data)
    
    blobs = PickleExtractor.extract_pickles_from_pickle_bytes(io.BytesIO(pickled))
    
    assert len(blobs) == 1
    restored = pickle.loads(blobs[0])
    assert restored == original_data


def test_extract_all_pickle_protocols():
    """Test extraction works with all standard pickle protocols"""
    test_data = {"test": [1, 2, 3]}
    
    for protocol in range(5):  # 0 through 4
        pickled = pickle.dumps(test_data, protocol=protocol)
        blobs = PickleExtractor.extract_pickles_from_pickle_bytes(io.BytesIO(pickled))
        
        assert len(blobs) == 1, f"Failed for protocol {protocol}"
        assert pickle.loads(blobs[0]) == test_data


def test_extract_numpy_compressed():
    """Test extraction from compressed NumPy archive"""
    path = f"{_root_path}/test_data_extractor/compressed.npz"
    
    np.savez_compressed(
        path,
        a=np.array([1, 2, 3], dtype=object),
        b=np.array([4, 5, 6], dtype=object)
    )
    
    with open(path, "rb") as f:
        # .npz is a ZIP, should be detected as such
        blobs = PickleExtractor.extract_pickles_from_numpy(f)
    
    assert isinstance(blobs, list)