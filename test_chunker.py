from pathlib import Path

from repository.indexing.chunker import CodeChunker
from repository.language.language import Language
from repository.models.code_document import CodeDocument


def make_document(content: str, language: Language = Language.PYTHON) -> CodeDocument:
    return CodeDocument(
        path=Path("test.py"),
        content=content,
        encoding="utf-8",
        size=len(content),
        file_hash="test-hash",
        language=language,
    )


def test_chunks_top_level_function():
    document = make_document(
        "def hello():\n"
        "    return 'hello'\n"
    )

    chunks = CodeChunker().chunk(document)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.chunk_type == "function"
    assert chunk.name == "hello"
    assert chunk.parent_name is None
    assert chunk.start_line == 1
    assert chunk.end_line == 2


def test_chunks_class_and_methods():
    document = make_document(
        "class UserService:\n"
        "\n"
        "    def create_user(self):\n"
        "        pass\n"
        "\n"
        "    async def delete_user(self):\n"
        "        pass\n"
    )

    chunks = CodeChunker().chunk(document)

    assert len(chunks) == 3

    class_chunk = chunks[0]
    create_chunk = chunks[1]
    delete_chunk = chunks[2]

    assert class_chunk.chunk_type == "class"
    assert class_chunk.name == "UserService"
    assert class_chunk.parent_name is None

    assert create_chunk.chunk_type == "method"
    assert create_chunk.name == "create_user"
    assert create_chunk.parent_name == "UserService"

    assert delete_chunk.chunk_type == "method"
    assert delete_chunk.name == "delete_user"
    assert delete_chunk.parent_name == "UserService"


def test_invalid_python_returns_no_chunks():
    document = make_document(
        "def broken(:\n"
    )

    chunks = CodeChunker().chunk(document)

    assert chunks == []


def test_non_python_returns_no_chunks():
    document = make_document(content="<h1>Hello</h1>", language=Language.UNKNOWN)

    chunks = CodeChunker().chunk(document)

    assert chunks == []


def test_class_method_has_parent():
    document = make_document(
        "class UserService:\n"
        "    def create_user(self):\n"
        "        pass\n"
    )

    chunks = CodeChunker().chunk(document)

    method = chunks[1]

    assert method.chunk_type == "method"
    assert method.name == "create_user"
    assert method.parent_name == "UserService"


def test_top_level_function_has_no_parent():
    document = make_document(
        "def calculate_total():\n"
        "    return 100\n"
    )

    chunks = CodeChunker().chunk(document)

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "function"
    assert chunks[0].parent_name is None


def test_async_method_is_method():
    document = make_document(
        "class Service:\n"
        "    async def process(self):\n"
        "        pass\n"
    )

    chunks = CodeChunker().chunk(document)

    method = chunks[1]

    assert method.chunk_type == "method"
    assert method.name == "process"
    assert method.parent_name == "Service"


def test_function_metadata():
    document = make_document(
        "@router.post('/users')\n"
        "def create_user():\n"
        "    \"\"\"Create a new user.\"\"\"\n"
        "    pass\n"
    )

    chunks = CodeChunker().chunk(document)

    chunk = chunks[0]

    assert chunk.name == "create_user"
    assert chunk.decorators == ["router.post('/users')"]
    assert chunk.docstring == "Create a new user."


def test_class_metadata():
    document = make_document(
        "@dataclass\n"
        "class User:\n"
        "    \"\"\"Represents a user.\"\"\"\n"
        "    name: str\n"
    )

    chunks = CodeChunker().chunk(document)

    chunk = chunks[0]

    assert chunk.name == "User"
    assert chunk.chunk_type == "class"
    assert chunk.decorators == ["dataclass"]
    assert chunk.docstring == "Represents a user."


def test_imports_are_attached_to_chunks():
    document = make_document(
        "import os\n"
        "from fastapi import FastAPI\n"
        "from app.database import get_db\n"
        "\n"
        "def create_user():\n"
        "    return get_db()\n"
    )

    chunks = CodeChunker().chunk(document)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.imports == [
        "import os",
        "from fastapi import FastAPI",
        "from app.database import get_db",
    ]


def test_no_imports_returns_empty_list():
    document = make_document(
        "def hello():\n"
        "    return 'hello'\n"
    )

    chunks = CodeChunker().chunk(document)

    assert chunks[0].imports == []


def test_nested_function_is_part_of_parent_function():
    document = make_document(
        "def create_user(user):\n"
        "    def validate():\n"
        "        return True\n"
        "    return validate()\n"
    )

    chunks = CodeChunker().chunk(document)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.chunk_type == "function"
    assert chunk.name == "create_user"
    assert chunk.parent_name is None
    assert "def validate():" in chunk.content


def test_nested_class_has_parent():
    document = make_document(
        "class Outer:\n"
        "    class Inner:\n"
        "        def process(self):\n"
        "            pass\n"
    )

    chunks = CodeChunker().chunk(document)

    assert len(chunks) == 3

    outer = chunks[0]
    inner = chunks[1]
    process = chunks[2]

    assert outer.chunk_type == "class"
    assert outer.name == "Outer"
    assert outer.parent_name is None

    assert inner.chunk_type == "class"
    assert inner.name == "Inner"
    assert inner.parent_name == "Outer"

    assert process.chunk_type == "method"
    assert process.name == "process"
    assert process.parent_name == "Inner"


def test_empty_module_returns_no_chunks():
    document = make_document("")

    chunks = CodeChunker().chunk(document)

    assert chunks == []


def test_syntax_error_returns_no_chunks():
    document = make_document(
        "def broken(:\n"
        "    pass\n"
    )

    chunks = CodeChunker().chunk(document)

    assert chunks == []
