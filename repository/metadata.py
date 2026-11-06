from pathlib import Path

from models import FileMetadata

class MetadataCollector:
    @staticmethod
    def binary_file(path: Path) -> bool:
        try:
            with path.open("rb") as f:
                chunk = f.read(1024)
            return b"\x00" in chunk
        except Exception:
            return False

    @staticmethod
    def encoding(path: Path) -> str | None:
        try:
            path.read_text(encoding="utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            return "unknown"
        except Exception:
            return None

    @staticmethod
    def collect(file_path: Path, repository_root: Path) -> FileMetadata:
        start = file_path.stat()
        is_binary = MetadataCollector.binary_file(file_path)
        
        enc = None
        lines = 0
        if not is_binary:
            enc = MetadataCollector.encoding(file_path)
            try:
                # We can try to open it with the detected encoding or utf-8
                with file_path.open("r", encoding=enc if enc != "unknown" else "utf-8", errors="ignore") as f:
                    lines = sum(1 for _ in f)
            except Exception:
                lines = 0

        return FileMetadata(
            absolute_path=file_path.resolve(),
            relative_path=file_path.relative_to(repository_root),
            file_name=file_path.name,
            extension=file_path.suffix.lower() or "no extension",
            size_bytes=start.st_size,
            is_binary=is_binary,
            encoding=enc,
            line_count=lines,
        )