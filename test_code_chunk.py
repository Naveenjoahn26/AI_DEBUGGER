import pytest
from repository.models.code_chunk import CodeChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chunk(**overrides) -> CodeChunk:
    """Return a minimal valid CodeChunk, with optional field overrides."""
    defaults = dict(
        content="def foo(): pass",
        file_path="src/foo.py",
        chunk_type="function",
        name="foo",
        start_line=1,
        end_line=1,
    )
    defaults.update(overrides)
    return CodeChunk(**defaults)


# ---------------------------------------------------------------------------
# Construction & required fields
# ---------------------------------------------------------------------------

class TestCodeChunkConstruction:
    def test_minimal_required_fields(self):
        chunk = make_chunk()
        assert chunk.content == "def foo(): pass"
        assert chunk.file_path == "src/foo.py"
        assert chunk.chunk_type == "function"
        assert chunk.name == "foo"
        assert chunk.start_line == 1
        assert chunk.end_line == 1

    def test_optional_fields_default_to_none(self):
        chunk = make_chunk()
        assert chunk.repository_id is None
        assert chunk.language is None
        assert chunk.parent_name is None
        assert chunk.file_hash is None

    def test_optional_fields_can_be_set(self):
        chunk = make_chunk(
            repository_id="repo-123",
            language="python",
            parent_name="MyClass",
            file_hash="abc123",
        )
        assert chunk.repository_id == "repo-123"
        assert chunk.language == "python"
        assert chunk.parent_name == "MyClass"
        assert chunk.file_hash == "abc123"

    def test_name_can_be_none(self):
        """Module-level or anonymous chunks may have no name."""
        chunk = make_chunk(name=None)
        assert chunk.name is None


# ---------------------------------------------------------------------------
# line_count property
# ---------------------------------------------------------------------------

class TestLineCount:
    def test_single_line_chunk(self):
        chunk = make_chunk(start_line=5, end_line=5)
        assert chunk.line_count == 1

    def test_multi_line_chunk(self):
        chunk = make_chunk(start_line=10, end_line=19)
        assert chunk.line_count == 10

    def test_two_line_chunk(self):
        chunk = make_chunk(start_line=3, end_line=4)
        assert chunk.line_count == 2

    def test_large_chunk(self):
        chunk = make_chunk(start_line=1, end_line=500)
        assert chunk.line_count == 500

    def test_line_count_equals_end_minus_start_plus_one(self):
        """Invariant: line_count == end_line - start_line + 1."""
        for start, end in [(1, 1), (1, 10), (42, 100), (7, 7)]:
            chunk = make_chunk(start_line=start, end_line=end)
            assert chunk.line_count == end - start + 1


# ---------------------------------------------------------------------------
# Dataclass equality & identity
# ---------------------------------------------------------------------------

class TestDataclassSemantics:
    def test_equal_chunks_are_equal(self):
        a = make_chunk()
        b = make_chunk()
        assert a == b

    def test_chunks_differing_in_content_are_not_equal(self):
        a = make_chunk(content="def foo(): pass")
        b = make_chunk(content="def bar(): pass")
        assert a != b

    def test_chunks_differing_in_file_path_are_not_equal(self):
        a = make_chunk(file_path="src/a.py")
        b = make_chunk(file_path="src/b.py")
        assert a != b

    def test_chunks_differing_in_lines_are_not_equal(self):
        a = make_chunk(start_line=1, end_line=5)
        b = make_chunk(start_line=2, end_line=6)
        assert a != b

    def test_chunks_differing_in_optional_fields_are_not_equal(self):
        a = make_chunk(language="python")
        b = make_chunk(language="javascript")
        assert a != b


# ---------------------------------------------------------------------------
# Chunk types (smoke-test common values)
# ---------------------------------------------------------------------------

class TestChunkTypes:
    @pytest.mark.parametrize("chunk_type", [
        "function", "class", "method", "module", "block"
    ])
    def test_various_chunk_types_are_accepted(self, chunk_type):
        chunk = make_chunk(chunk_type=chunk_type)
        assert chunk.chunk_type == chunk_type


# ---------------------------------------------------------------------------
# Repr / string representation (dataclass default)
# ---------------------------------------------------------------------------

class TestRepr:
    def test_repr_contains_class_name(self):
        chunk = make_chunk()
        assert "CodeChunk" in repr(chunk)

    def test_repr_contains_field_values(self):
        chunk = make_chunk(name="my_func", file_path="utils.py")
        r = repr(chunk)
        assert "my_func" in r
        assert "utils.py" in r
