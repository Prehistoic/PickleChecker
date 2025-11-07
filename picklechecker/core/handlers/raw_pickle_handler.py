from pathlib import Path

from picklechecker.core.handlers import FileFormatHandler

class RawPickleHandler(FileFormatHandler):
    format_name = "raw-pickle"
    _exts = {".pkl", ".pickle"}

    # Known pickle protocol magic bytes (first 2 bytes: PROTO opcode)
    _magic_bytes = {
        b'\x80\x02',  # Protocol 0, 1, 2
        b'\x80\x03',  # Protocol 3
        b'\x80\x04',  # Protocol 4
        b'\x80\x05',  # Protocol 5
    }

    def supports(self, path: Path) -> bool:
        # First check extension
        if path.suffix.lower() in self._exts:
            return True
        
        # Then check magic bytes
        try:
            with path.open('rb') as f:
                header = f.read(2)
                if header in self._magic_bytes:
                    return True
        except (OSError, IOError):
            # Can't read file, fall back to extension check only
            pass
        
        return False

    def extract_pickles(self, path: Path):
        data = path.read_bytes()
        yield (data, "top-level")