import pytest
import time
from pathlib import Path
from repository.reader.reader import CodeReader
from repository.language.detector import LanguageDetector

def test_reader_caching_behavior(tmp_path):
    detector = LanguageDetector()
    reader = CodeReader(language_detector=detector)
    
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")
    
    # 1. Cache Miss
    assert test_file not in reader._cache
    doc1 = reader.read(test_file)
    assert doc1.content == "print('hello')"
    assert test_file in reader._cache
    
    # 2. Cache Hit
    # Modify the _cache tuple manually to prove it's returning the cached object
    original_mtime, cached_doc = reader._cache[test_file]
    reader._cache[test_file] = (original_mtime, "FAKE_CACHED_DOC")
    doc2 = reader.read(test_file)
    assert doc2 == "FAKE_CACHED_DOC"
    
    # Restore the actual document
    reader._cache[test_file] = (original_mtime, cached_doc)
    
    # 3. Cache Invalidation via mtime change
    time.sleep(0.1) # Ensure mtime change is noticeable (some filesystems have coarse mtime)
    test_file.write_text("print('world')")
    
    doc3 = reader.read(test_file)
    assert doc3.content == "print('world')"
    # Mtime should be updated in cache
    new_mtime, new_cached_doc = reader._cache[test_file]
    assert new_mtime != original_mtime
    assert new_cached_doc.content == "print('world')"
