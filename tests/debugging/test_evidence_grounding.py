import json
import pytest
from pydantic import ValidationError

from repository.debugging.engine import CodeDebuggingEngine
from repository.debugging.models import DebugResult, DebugEvidence
from repository.models.code_chunk import CodeChunk


# ── Fakes ────────────────────────────────────────────────────────────────────

def make_chunk(
    file_path="auth.py",
    start_line=10,
    end_line=15,
    content="def authenticate_user(username, password):\n    return True",
    name="authenticate_user",
    chunk_type="function",
):
    return CodeChunk(
        content=content,
        file_path=file_path,
        chunk_type=chunk_type,
        name=name,
        start_line=start_line,
        end_line=end_line,
    )


class FakeRetriever:
    def __init__(self, chunks):
        self.chunks = chunks

    def search(self, query, top_k=5):
        return self.chunks


class FakeContextBuilder:
    def build(self, chunks):
        return []

    def format(self, items):
        return ""


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def generate(self, prompt):
        return self.response


def make_engine(chunks, llm_response):
    return CodeDebuggingEngine(
        retriever=FakeRetriever(chunks),
        context_builder=FakeContextBuilder(),
        llm=FakeLLM(llm_response),
    )


def valid_response(**overrides):
    base = {
        "root_cause": "Bug in auth",
        "explanation": "The user check fails",
        "evidence": [
            {
                "file_path": "auth.py",
                "start_line": 10,
                "end_line": 15,
                "explanation": "This function has the bug",
            }
        ],
        "suggested_fix": "Fix the condition",
        "confidence": "high",
    }
    base.update(overrides)
    return json.dumps(base)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_valid_matching_evidence():
    chunk = make_chunk()
    engine = make_engine([chunk], valid_response())

    result = engine.debug("Why does login fail?")

    assert isinstance(result, DebugResult)
    assert len(result.evidence) == 1

    ev = result.evidence[0]
    assert ev.file_path == "auth.py"
    assert ev.content == chunk.content          # real source code, not LLM fabrication
    assert ev.explanation == "This function has the bug"  # LLM explanation kept separate
    assert ev.start_line == 10
    assert ev.end_line == 15


def test_nonexistent_file_evidence_is_dropped():
    """LLM references a file that was never retrieved — must be silently dropped."""
    chunk = make_chunk(file_path="auth.py")
    hallucinated = valid_response()

    # Override to reference a completely different file
    data = json.loads(hallucinated)
    data["evidence"][0]["file_path"] = "totally_made_up.py"

    engine = make_engine([chunk], json.dumps(data))
    result = engine.debug("Some problem")

    assert result.evidence == []


def test_invalid_line_range_evidence_is_dropped():
    """LLM cites lines 100-200 but chunk is only at 10-15 — no overlap, must drop."""
    chunk = make_chunk(start_line=10, end_line=15)
    data = json.loads(valid_response())
    data["evidence"][0]["start_line"] = 100
    data["evidence"][0]["end_line"] = 200

    engine = make_engine([chunk], json.dumps(data))
    result = engine.debug("Some problem")

    assert result.evidence == []


def test_overlapping_line_range_is_accepted():
    """LLM cites 12-14 inside a chunk 10-15 — overlap is valid."""
    chunk = make_chunk(start_line=10, end_line=15)
    data = json.loads(valid_response())
    data["evidence"][0]["start_line"] = 12
    data["evidence"][0]["end_line"] = 14

    engine = make_engine([chunk], json.dumps(data))
    result = engine.debug("Some problem")

    assert len(result.evidence) == 1
    assert result.evidence[0].content == chunk.content


def test_multiple_evidence_chunks():
    chunk_auth = make_chunk(file_path="auth.py", start_line=10, end_line=15, name="authenticate_user")
    chunk_db = make_chunk(
        file_path="database.py", start_line=5, end_line=10,
        content="def connect():\n    pass", name="connect", chunk_type="function"
    )

    data = json.loads(valid_response())
    data["evidence"] = [
        {"file_path": "auth.py", "start_line": 10, "end_line": 15, "explanation": "Auth issue"},
        {"file_path": "database.py", "start_line": 5, "end_line": 10, "explanation": "DB issue"},
    ]

    engine = make_engine([chunk_auth, chunk_db], json.dumps(data))
    result = engine.debug("Login fails with DB error")

    assert len(result.evidence) == 2
    files = {ev.file_path for ev in result.evidence}
    assert "auth.py" in files
    assert "database.py" in files


def test_empty_evidence():
    chunk = make_chunk()
    data = json.loads(valid_response())
    data["evidence"] = []

    engine = make_engine([chunk], json.dumps(data))
    result = engine.debug("Some problem")

    assert result.evidence == []


def test_chunk_content_is_real_source_not_llm_text():
    """The content field must be the actual CodeChunk source, not the LLM explanation."""
    real_source = "def real_code():\n    return 42"
    chunk = make_chunk(content=real_source)

    engine = make_engine([chunk], valid_response())
    result = engine.debug("Why does login fail?")

    assert result.evidence[0].content == real_source
    assert result.evidence[0].content != "This function has the bug"  # not the LLM text


def test_explanation_stored_separately():
    """LLM explanation must be stored in evidence.explanation, not content."""
    chunk = make_chunk()
    engine = make_engine([chunk], valid_response())
    result = engine.debug("Some problem")

    ev = result.evidence[0]
    assert ev.explanation == "This function has the bug"
    assert ev.content != ev.explanation


def test_empty_problem_returns_early():
    engine = make_engine([], valid_response())
    result = engine.debug("   ")
    assert result.root_cause == "Empty input"
    assert result.evidence == []
