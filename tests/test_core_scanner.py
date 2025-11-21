import io
import os
import pickle
import pytest
from pathlib import Path
from picklechecker.core.scanner import PickleScanner
from picklechecker.core.extractor import PickleExtractor
from picklechecker.core.results import AnalysisResult, AnalysisStatus, SafetyLevel

_root_path = os.path.dirname(__file__)


class Malicious1:
    def __reduce__(self):
        return eval, ("print('456')",)


class Malicious2:
    def __reduce__(self):
        return os.system, ("ls -la",)


class Malicious3:
    def __reduce__(self):
        import http.client
        return http.client.HTTPSConnection, ("github.com",)


def initialize_pickle_file(path: str, obj: any, version: int):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as file:
            pickle.dump(obj, file, protocol=version)


def initialize_data_file(path: str, data: bytes):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as file:
            file.write(data)


def test_scanner_scan_file_benign():
    """Test scanning a benign pickle file"""
    path = f"{_root_path}/test_data/benign.pkl"
    initialize_pickle_file(path, ["a", "b", "c"], 4)
    
    result = PickleScanner.scan_file(path)
    
    assert result.status == AnalysisStatus.COMPLETED
    assert result.safety == SafetyLevel.INNOCUOUS
    assert len(result.errors) == 0


def test_scanner_scan_file_malicious_eval():
    """Test scanning a pickle file with eval"""
    path = f"{_root_path}/test_data/malicious_eval.pkl"
    initialize_pickle_file(path, Malicious1(), 4)
    
    result = PickleScanner.scan_file(path)
    
    assert result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED_WITH_ERRORS]
    assert result.safety == SafetyLevel.DANGEROUS
    assert any("builtins" in g.module and "eval" in g.name for g in result.globals_found)


def test_scanner_scan_file_malicious_os_system():
    """Test scanning a pickle file with os.system"""
    path = f"{_root_path}/test_data/malicious_system.pkl"
    initialize_pickle_file(path, Malicious2(), 4)
    
    result = PickleScanner.scan_file(path)
    
    assert result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED_WITH_ERRORS]
    assert result.safety == SafetyLevel.DANGEROUS
    assert any("system" in g.name.lower() for g in result.globals_found)


def test_scanner_scan_file_multiple_protocols():
    """Test scanning pickle files with different protocol versions"""
    for version in (0, 3, 4):
        path = f"{_root_path}/test_data/benign_v{version}.pkl"
        initialize_pickle_file(path, {"a": 1, "b": 2}, version)
        
        result = PickleScanner.scan_file(path)
        
        assert result.status == AnalysisStatus.COMPLETED
        assert result.safety == SafetyLevel.INNOCUOUS


def test_scanner_scan_file_complex_malicious():
    """Test scanning a complex malicious pickle"""
    path = f"{_root_path}/test_data/malicious_complex.pkl"
    initialize_data_file(
        path,
        b'c__builtin__\nglobals\n(tRp100\n0c__builtin__\ncompile\n(S\'fl=open("/etc/passwd");'
        + b"picklesmashed=fl.read();'\nS''\nS'exec'\ntRp101\n0c__builtin__\neval\n(g101\ng100\n"
        + b"tRp102\n0c__builtin__\ngetattr\n(c__builtin__\ndict\nS'get'\ntRp103\n0c__builtin__\n"
        + b"apply\n(g103\n(g100\nS'picklesmashed'\nltRp104\n0g104\n.",
    )
    
    result = PickleScanner.scan_file(path)
    
    assert result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED_WITH_ERRORS]
    assert result.safety == SafetyLevel.DANGEROUS
    assert len(result.globals_found) > 0


def test_scanner_scan_file_stack_global():
    """Test scanning pickle with STACK_GLOBAL opcode"""
    path = f"{_root_path}/test_data/stack_global.pkl"
    initialize_data_file(
        path,
        b"".join([
            pickle.UNICODE + b"os\n",
            pickle.PUT + b"2\n",
            pickle.POP,
            pickle.UNICODE + b"system\n",
            pickle.PUT + b"3\n",
            pickle.POP,
            pickle.GET + b"2\n",
            pickle.GET + b"3\n",
            pickle.STACK_GLOBAL,
            pickle.MARK,
            pickle.UNICODE + b"ls\n",
            pickle.TUPLE,
            pickle.REDUCE,
            pickle.STOP,
        ])
    )
    
    result = PickleScanner.scan_file(path)
    
    assert result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED_WITH_ERRORS]
    assert any("os" in g.module and "system" in g.name for g in result.globals_found)


def test_scanner_scan_directory():
    """Test scanning a directory of pickle files"""
    dir_path = f"{_root_path}/test_data/scan_dir"
    os.makedirs(dir_path, exist_ok=True)
    
    # Create multiple files
    initialize_pickle_file(f"{dir_path}/benign1.pkl", ["a", "b"], 4)
    initialize_pickle_file(f"{dir_path}/benign2.pkl", {"x": 1}, 4)
    initialize_pickle_file(f"{dir_path}/malicious1.pkl", Malicious1(), 4)
    
    results = PickleScanner.scan_directory(dir_path)
    
    assert len(results) >= 3
    assert any(r.safety == SafetyLevel.DANGEROUS for r in results)
    assert any(r.safety == SafetyLevel.INNOCUOUS for r in results)

def test_scanner_opcode_counts():
    """Test that opcode counts are tracked"""
    path = f"{_root_path}/test_data/opcode_test.pkl"
    initialize_pickle_file(path, {"a": 1, "b": 2, "c": 3}, 4)
    
    result = PickleScanner.scan_file(path)
    
    assert len(result.opcode_counts) > 0
    assert "STOP" in result.opcode_counts


def test_scanner_disassembly():
    """Test that pickle disassembly is generated"""
    path = f"{_root_path}/test_data/disassembly_test.pkl"
    initialize_pickle_file(path, ["test"], 4)
    
    result = PickleScanner.scan_file(path)
    
    assert len(result.disassembly) > 0
    assert "STOP" in result.disassembly


def test_scanner_file_not_found():
    """Test scanning non-existent file"""
    result = PickleScanner.scan_file("/nonexistent/path/file.pkl")
    
    assert result.status == AnalysisStatus.FAILED
    assert len(result.errors) > 0


def test_scanner_relative_path():
    """Test that relative paths are correctly computed"""
    dir_path = f"{_root_path}/test_data/relative_test"
    os.makedirs(dir_path, exist_ok=True)
    
    file_path = f"{dir_path}/test.pkl"
    initialize_pickle_file(file_path, ["a"], 4)
    
    result = PickleScanner.scan_file(file_path, scandir=dir_path)
    
    assert result.source_path == Path("test.pkl")


def test_extractor_extract_pickle():
    """Test extracting pickle from file"""
    path = f"{_root_path}/test_data/extract_test.pkl"
    initialize_pickle_file(path, ["a", "b", "c"], 4)
    
    blobs = PickleExtractor.extract_pickles_from_filepath(path)
    
    assert len(blobs) > 0
    assert isinstance(blobs[0], bytes)


def test_scanner_inst_opcode():
    """Test scanning pickle with INST opcode"""
    path = f"{_root_path}/test_data/inst_opcode.pkl"
    initialize_data_file(
        path,
        b"(S'raise RuntimeError(\"Injection running\")'\ni__builtin__\nexec\n."
    )
    
    result = PickleScanner.scan_file(path)
    
    assert result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED_WITH_ERRORS]
    assert any("exec" in g.name.lower() for g in result.globals_found)


def test_scanner_memo_handling():
    """Test that memo operations are handled correctly"""
    path = f"{_root_path}/test_data/memo_test.pkl"
    initialize_data_file(
        path,
        b"".join([
            pickle.PROTO, b"\x04",
            pickle.SHORT_BINUNICODE, b"\x02os",
            pickle.MEMOIZE,
            pickle.SHORT_BINUNICODE, b"\x06system",
            pickle.MEMOIZE,
            pickle.BINGET, b"\x00",
            pickle.BINGET, b"\x01",
            pickle.STACK_GLOBAL,
            pickle.UNICODE, b"ls\n",
            pickle.TUPLE1,
            pickle.REDUCE,
            pickle.STOP,
        ])
    )
    
    result = PickleScanner.scan_file(path)
    
    assert result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED_WITH_ERRORS]
    assert any("os" in g.module and "system" in g.name for g in result.globals_found)


def test_scanner_invalid_pickle_data():
    """Test scanning corrupted pickle data"""
    path = f"{_root_path}/test_data/invalid.pkl"
    initialize_data_file(path, b"invalid pickle data \x00\x01\x02")
    
    result = PickleScanner.scan_file(path)
    
    # Should handle gracefully
    assert result.status in [AnalysisStatus.FAILED, AnalysisStatus.COMPLETED_WITH_ERRORS]


def test_scanner_multiple_pickles():
    """Test scanning file with multiple pickle streams"""
    path = f"{_root_path}/test_data/multiple_pickles.pkl"
    data = pickle.dumps(["a", "b", "c"]) + pickle.dumps(Malicious1())
    initialize_data_file(path, data)
    
    result = PickleScanner.scan_file(path)
    
    assert result.status in [AnalysisStatus.COMPLETED, AnalysisStatus.COMPLETED_WITH_ERRORS]
    # Should detect the malicious pickle
    assert any("eval" in g.name.lower() for g in result.globals_found)