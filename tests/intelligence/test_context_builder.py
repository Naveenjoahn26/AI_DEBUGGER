from repository.ai.context_builder import (
    RepositoryContextBuilder,
)
from repository.models.code_chunk import CodeChunk


def test_build_context():

    chunks = [
        CodeChunk(
            content="def login():\n    pass",
            file_path="auth.py",
            chunk_type="function",
            name="login",
            start_line=1,
            end_line=2,
        )
    ]

    builder = RepositoryContextBuilder()

    context = builder.build(chunks)

    assert len(context) == 1

    item = context[0]

    assert item.file_path == "auth.py"
    assert item.chunk_type == "function"
    assert item.name == "login"
    assert item.start_line == 1
    assert item.end_line == 2
    assert item.content == "def login():\n    pass"

def test_empty_chunks():

    builder = RepositoryContextBuilder()

    assert builder.build([]) == []

def test_duplicate_chunks_are_removed():

    chunk = CodeChunk(
        content="def login():\n    pass",
        file_path="auth.py",
        chunk_type="function",
        name="login",
        start_line=1,
        end_line=2,
    )

    builder = RepositoryContextBuilder()

    items = builder.build([
        chunk,
        chunk,
    ])

    assert len(items) == 1

def test_different_chunks_are_kept():

    first = CodeChunk(
        content="def login():\n    pass",
        file_path="auth.py",
        chunk_type="function",
        name="login",
        start_line=1,
        end_line=2,
    )

    second = CodeChunk(
        content="def logout():\n    pass",
        file_path="auth.py",
        chunk_type="function",
        name="logout",
        start_line=4,
        end_line=5,
    )

    builder = RepositoryContextBuilder()

    items = builder.build([
        first,
        second,
    ])

    assert len(items) == 2
    assert items[0].name == "login"
    assert items[1].name == "logout"

def test_retrieval_order_is_preserved():

    first = CodeChunk(
        content="def first():\n    pass",
        file_path="a.py",
        chunk_type="function",
        name="first",
        start_line=1,
        end_line=2,
    )

    second = CodeChunk(
        content="def second():\n    pass",
        file_path="b.py",
        chunk_type="function",
        name="second",
        start_line=1,
        end_line=2,
    )

    builder = RepositoryContextBuilder()

    items = builder.build([
        second,
        first,
    ])

    assert items[0].name == "second"
    assert items[1].name == "first"
