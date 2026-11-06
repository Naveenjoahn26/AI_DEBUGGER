from repository.models.code_chunk import CodeChunk
from repository.embeddings.vector_store import CodeVectorStore


def make_chunk(
    content: str,
    name: str,
    start_line: int,
) -> CodeChunk:
    return CodeChunk(
        content=content,
        file_path="app/users.py",
        chunk_type="function",
        name=name,
        start_line=start_line,
        end_line=start_line + 2,
    )


def test_add_and_search(tmp_path):

    store = CodeVectorStore(
        collection_name="test_repository_code",
        persist_directory=str(tmp_path / "chroma"),
    )

    chunks = [
        make_chunk(
            content=(
                "def create_user(user):\n"
                "    save_user(user)\n"
                "    return user"
            ),
            name="create_user",
            start_line=1,
        ),
        make_chunk(
            content=(
                "def calculate_total(items):\n"
                "    return sum(items)"
            ),
            name="calculate_total",
            start_line=10,
        ),
    ]

    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]

    store.add(
        embeddings=embeddings,
        chunks=chunks,
    )

    results = store.search(
        query_embedding=[1.0, 0.0, 0.0],
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].name == "create_user"
