"""
tests/ingestion/test_indexer.py

Tests for IndexingPipeline.
All external calls (embedder, vector_store) are mocked so no real
Chroma or HuggingFace calls are made.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from repository.ingestion.indexer import IndexingPipeline, IndexingSummary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_pipeline(embedder=None, vector_store=None):
    """Build an IndexingPipeline with mocked external dependencies."""
    if embedder is None:
        embedder = MagicMock()
        embedder.embed.return_value = [[0.1] * 384]

    if vector_store is None:
        vector_store = MagicMock()
        vector_store.collection.name = "test_collection"

    return IndexingPipeline(embedder=embedder, vector_store=vector_store)


def _write_py_file(directory: Path, name: str, content: str) -> Path:
    path = directory / name
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_returns_indexing_summary():
    """run() must return an IndexingSummary regardless of content."""
    pipeline = _make_pipeline()
    with tempfile.TemporaryDirectory() as tmp:
        result = pipeline.run(Path(tmp))
    assert isinstance(result, IndexingSummary)


def test_empty_repository_produces_zero_counts():
    """An empty directory should yield 0 files and 0 chunks."""
    pipeline = _make_pipeline()
    with tempfile.TemporaryDirectory() as tmp:
        result = pipeline.run(Path(tmp))

    assert result.files_scanned == 0
    assert result.files_processed == 0
    assert result.chunks_created == 0
    assert result.chunks_indexed == 0


def test_scans_python_files():
    """files_scanned should equal the number of .py files found."""
    pipeline = _make_pipeline()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_py_file(tmp_path, "a.py", "x = 1\n")
        _write_py_file(tmp_path, "b.py", "y = 2\n")
        (tmp_path / "readme.txt").write_text("not python", encoding="utf-8")

        result = pipeline.run(tmp_path)

    assert result.files_scanned == 2


def test_unsupported_file_types_are_ignored():
    """Non-Python files must not affect files_scanned."""
    pipeline = _make_pipeline()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "index.js").write_text("const x = 1;", encoding="utf-8")
        (tmp_path / "data.json").write_text("{}", encoding="utf-8")
        result = pipeline.run(tmp_path)

    assert result.files_scanned == 0


def test_chunks_are_passed_to_embedder():
    """The embedder should be called if there are chunks to embed."""
    mock_embedder = MagicMock()
    # Return a fake embedding for every call
    mock_embedder.embed.return_value = [[0.0] * 384]

    mock_vector_store = MagicMock()
    mock_vector_store.collection.name = "col"

    pipeline = IndexingPipeline(embedder=mock_embedder, vector_store=mock_vector_store)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_py_file(tmp_path, "module.py", "def hello(): pass\n")
        pipeline.run(tmp_path)

    # Embedder must have been invoked
    mock_embedder.embed.assert_called()


def test_embeddings_are_passed_to_vector_store():
    """vector_store.add() should be called when chunks exist."""
    mock_embedder = MagicMock()
    mock_embedder.embed.return_value = [[0.1] * 384]

    mock_vector_store = MagicMock()
    mock_vector_store.collection.name = "col"

    pipeline = IndexingPipeline(embedder=mock_embedder, vector_store=mock_vector_store)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_py_file(tmp_path, "module.py", "def hello(): pass\n")
        pipeline.run(tmp_path)

    mock_vector_store.add.assert_called_once()


def test_individual_file_read_failure_does_not_abort_pipeline():
    """A file that fails to read should be skipped; others must still be processed."""
    pipeline = _make_pipeline()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        good_file = _write_py_file(tmp_path, "good.py", "def ok(): pass\n")

        # Create a bad file (empty — CodeReader will still try; we'll patch the reader)
        bad_file = _write_py_file(tmp_path, "bad.py", "def ok(): pass\n")

        # Patch the reader to raise only for bad_file
        original_read = pipeline._reader.read

        def selective_read(path):
            if path.name == "bad.py":
                raise ValueError("Simulated read failure")
            return original_read(path)

        pipeline._reader.read = selective_read

        result = pipeline.run(tmp_path)

    assert result.files_scanned == 2
    assert result.files_processed == 1        # only good.py succeeded
    assert len(result.errors) == 1


def test_summary_contains_collection_name():
    """The collection name from the vector store should appear in the summary."""
    mock_vs = MagicMock()
    mock_vs.collection.name = "my_repo_collection"

    pipeline = _make_pipeline(vector_store=mock_vs)
    with tempfile.TemporaryDirectory() as tmp:
        result = pipeline.run(Path(tmp))

    assert result.collection_name == "my_repo_collection"
