import pytest
from repository.models.code_chunk import CodeChunk
from repository.embeddings.vector_store import CodeVectorStore

def make_chunk():
    return CodeChunk(
        content="def hello():\n    pass",
        file_path="app/main.py",
        chunk_type="function",
        name="hello",
        start_line=1,
        end_line=2,
    )

def test_chunk_id_is_deterministic(tmp_path):
    store = CodeVectorStore(
        persist_directory=str(tmp_path / "chroma")
    )
    chunk = make_chunk()
    first = store._chunk_id(chunk)
    second = store._chunk_id(chunk)
    assert first == second

def test_different_chunks_have_different_ids(tmp_path):
    store = CodeVectorStore(
        persist_directory=str(tmp_path / "chroma")
    )
    first = make_chunk()
    second = CodeChunk(
        content="def goodbye():\n    pass",
        file_path="app/main.py",
        chunk_type="function",
        name="goodbye",
        start_line=4,
        end_line=5,
    )
    assert store._chunk_id(first) != store._chunk_id(second)

def test_embedding_chunk_count_must_match(tmp_path):
    store = CodeVectorStore(
        persist_directory=str(tmp_path / "chroma")
    )
    chunks = [
        make_chunk(),
        make_chunk(),
    ]
    embeddings = [
        [0.1, 0.2, 0.3],
    ]
    with pytest.raises(ValueError):
        store.add(
            embeddings=embeddings,
            chunks=chunks,
        )
