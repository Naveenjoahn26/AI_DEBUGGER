from repository.models.code_chunk import CodeChunk
from repository.retrieval.lexical import BM25Retriever


def test_bm25_finds_exact_symbol():

    chunks = [
        CodeChunk(
            content="def calculate_total(items):\n    return sum(items)",
            file_path="billing.py",
            chunk_type="function",
            name="calculate_total",
            start_line=1,
            end_line=2,
        ),
        CodeChunk(
            content="def create_user(user):\n    return user",
            file_path="users.py",
            chunk_type="function",
            name="create_user",
            start_line=1,
            end_line=2,
        ),
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "calculate_total",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].name == "calculate_total"


def test_bm25_finds_file_path():

    chunks = [
        CodeChunk(
            content="def login():\n    pass",
            file_path="auth/login.py",
            chunk_type="function",
            name="login",
            start_line=1,
            end_line=2,
        ),
        CodeChunk(
            content="def calculate():\n    pass",
            file_path="billing/service.py",
            chunk_type="function",
            name="calculate",
            start_line=1,
            end_line=2,
        ),
    ]

    retriever = BM25Retriever(chunks)

    results = retriever.search(
        "auth login",
        top_k=1,
    )

    assert results[0].name == "login"


def test_empty_query():

    retriever = BM25Retriever([])

    assert retriever.search("anything") == []
