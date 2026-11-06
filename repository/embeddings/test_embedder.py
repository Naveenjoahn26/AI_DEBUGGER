from repository.embeddings.formatter import CodeChunkFormatter
from repository.models.code_chunk import CodeChunk


def test_format_function_chunk():

    chunk = CodeChunk(
        content="def create_user(user):\n    return user",
        file_path="app/services/user_service.py",
        chunk_type="function",
        name="create_user",
        start_line=10,
        end_line=11,
    )

    formatter = CodeChunkFormatter()

    result = formatter.format(chunk)

    assert "File: app/services/user_service.py" in result
    assert "Type: function" in result
    assert "Name: create_user" in result
    assert "Lines: 10-11" in result
    assert "def create_user(user):" in result
def test_format_includes_parent():

    chunk = CodeChunk(
        content="def create_user(self):\n    pass",
        file_path="app/services/user_service.py",
        chunk_type="method",
        name="create_user",
        parent_name="UserService",
        start_line=20,
        end_line=21,
    )

    result = CodeChunkFormatter().format(chunk)

    assert "Parent: UserService" in result