import sys
import hashlib
import logging
from pathlib import Path

# Add project root to sys.path to resolve 'repository' package when run directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from binaryornot.check import is_binary

from repository.models.code_document import CodeDocument
from repository.reader.constants import MAX_FILE_SIZE, SUPPORTED_ENCODINGS
from repository.reader.exception import FileDecodingError
from repository.language.detector import LanguageDetector

logger = logging.getLogger(__name__)


class CodeReader:

    def __init__(self, language_detector: LanguageDetector):
        self._language_detector = language_detector
        # 7.4 Caching: store path -> (mtime, CodeDocument)
        self._cache = {}

    def _decode_raw_bytes(self, raw_bytes: bytes) -> tuple[str, str]:
        for encoding in SUPPORTED_ENCODINGS:
            try:
                content = raw_bytes.decode(encoding)
                return content, encoding
            except UnicodeDecodeError:
                continue

        raise FileDecodingError("Unable to decode the file.")

    def _is_binary_file(self, path: Path) -> bool:
        return is_binary(path)

    def read_many(self, paths: list[Path]) -> list[CodeDocument]:
        documents = []

        for path in paths:
            try:
                documents.append(self.read(path))
            except Exception as e:
                logger.warning("Failed to read %s: %s", path, e)

        return documents

    def read(self, path: Path) -> CodeDocument:

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise FileNotFoundError(f"No file found at: {path}")

        # Check cache
        current_mtime = path.stat().st_mtime
        if path in self._cache:
            cached_mtime, cached_doc = self._cache[path]
            if current_mtime == cached_mtime:
                return cached_doc

        if self._is_binary_file(path):
            raise ValueError(f"Binary file detected: {path}")

        size = path.stat().st_size

        if size > MAX_FILE_SIZE:
            raise ValueError(
                f"{path} exceeds maximum supported size ({MAX_FILE_SIZE} bytes)."
            )

        raw_bytes = path.read_bytes()

        content, encoding = self._decode_raw_bytes(raw_bytes)

        file_hash = hashlib.sha256(raw_bytes).hexdigest()
        language = self._language_detector.detect(path)
        doc = CodeDocument(
            path=path,
            content=content,
            encoding=encoding,
            size=size,
            file_hash=file_hash,
            language=language,
        )
        
        # Update cache
        self._cache[path] = (current_mtime, doc)
        
        return doc
