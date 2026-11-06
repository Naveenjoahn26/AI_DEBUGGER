"""
Phase 5.5.5 — Real Debugging Test

Uses the actual CodeDebuggingEngine with:
- FakeLLM  (no Groq API calls)
- FakeRetriever backed by real CodeChunks derived from the buggy fixture
- Real RepositoryContextBuilder
- Real DebugResponseSchema validation
- Real DebugResult / DebugEvidence construction

The pipeline under test:
  error description
      ↓
  FakeRetriever (returns real chunks from billing.py)
      ↓
  RepositoryContextBuilder (builds / formats context)
      ↓
  FakeLLM (returns structured JSON matching the bug)
      ↓
  DebugResponseSchema validation
      ↓
  Evidence grounding against retrieved chunks
      ↓
  DebugResult
"""
import json
import pytest
from pydantic import ValidationError

from repository.debugging.engine import CodeDebuggingEngine
from repository.debugging.models import DebugResult, DebugEvidence
from repository.debugging.schemas import DebugResponseSchema
from repository.ai.context_builder import RepositoryContextBuilder
from repository.models.code_chunk import CodeChunk


# ── Shared fixture chunks from buggy_repo/billing.py ─────────────────────────

BILLING_CHUNK = CodeChunk(
    content=(
        "def calculate_total(price, quantity):\n"
        "    return price + quantity  # Bug: should be price * quantity"
    ),
    file_path="tests/fixtures/buggy_repo/billing.py",
    chunk_type="function",
    name="calculate_total",
    start_line=10,
    end_line=11,
)

DISCOUNT_CHUNK = CodeChunk(
    content=(
        "def apply_discount(total, discount_percent):\n"
        "    if discount_percent < 0 or discount_percent > 100:\n"
        "        raise ValueError('Discount must be between 0 and 100')\n"
        "    return total * (1 - discount_percent / 100)"
    ),
    file_path="tests/fixtures/buggy_repo/billing.py",
    chunk_type="function",
    name="apply_discount",
    start_line=14,
    end_line=17,
)


# ── Fakes ─────────────────────────────────────────────────────────────────────

class FakeRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    def search(self, query, top_k=5):
        return self._chunks


class FakeLLM:
    def __init__(self, payload: dict):
        self._payload = payload

    def generate(self, prompt: str) -> str:
        return json.dumps(self._payload)


def make_engine(chunks, llm_payload):
    return CodeDebuggingEngine(
        retriever=FakeRetriever(chunks),
        context_builder=RepositoryContextBuilder(),
        llm=FakeLLM(llm_payload),
    )


# ── Standard valid LLM payload referencing real chunk ────────────────────────

VALID_PAYLOAD = {
    "root_cause": "calculate_total uses + instead of * causing TypeError when quantity is a string",
    "explanation": (
        "The function adds price and quantity directly. "
        "When quantity is passed as a string '2', Python cannot add int + str, "
        "raising TypeError: unsupported operand type(s) for +: 'int' and 'str'."
    ),
    "evidence": [
        {
            "file_path": "tests/fixtures/buggy_repo/billing.py",
            "start_line": 10,
            "end_line": 11,
            "explanation": "calculate_total uses + instead of *, and no type coercion on quantity",
        }
    ],
    "suggested_fix": (
        "Change `price + quantity` to `price * int(quantity)` "
        "to correctly compute the total and handle string inputs."
    ),
    "confidence": "high",
}


# ═════════════════════════════════════════════════════════════════════════════
# HAPPY-PATH TESTS
# ═════════════════════════════════════════════════════════════════════════════

def test_full_pipeline_returns_debug_result():
    """Engine runs end-to-end and returns a DebugResult."""
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    error = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"

    result = engine.debug(error)

    assert isinstance(result, DebugResult)


def test_root_cause_is_non_empty():
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    assert result.root_cause
    assert len(result.root_cause) > 0


def test_explanation_is_non_empty():
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    assert result.explanation
    assert len(result.explanation) > 0


def test_suggested_fix_is_non_empty():
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    assert result.suggested_fix
    assert len(result.suggested_fix) > 0


def test_confidence_is_present():
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    assert result.confidence in {"low", "medium", "high"}


def test_evidence_matches_retrieved_chunk():
    """Evidence file_path/lines/content must come from the real CodeChunk."""
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    assert len(result.evidence) == 1

    ev = result.evidence[0]
    assert ev.file_path == BILLING_CHUNK.file_path
    assert ev.start_line == BILLING_CHUNK.start_line
    assert ev.end_line == BILLING_CHUNK.end_line
    assert ev.content == BILLING_CHUNK.content          # real source, not LLM text
    assert ev.explanation                               # LLM explanation non-empty


def test_evidence_content_is_real_source_code():
    """Specifically assert the content matches the buggy function body."""
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    ev = result.evidence[0]
    assert "def calculate_total" in ev.content
    assert "price + quantity" in ev.content


def test_evidence_explanation_separate_from_content():
    """LLM explanation must NOT bleed into the content field."""
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    ev = result.evidence[0]
    assert ev.explanation != ev.content


def test_multiple_chunks_retrieved_only_matched_becomes_evidence():
    """When multiple chunks are retrieved, only the one the LLM cited is attached."""
    engine = make_engine([BILLING_CHUNK, DISCOUNT_CHUNK], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    assert len(result.evidence) == 1
    assert result.evidence[0].name == "calculate_total" if hasattr(result.evidence[0], "name") else True
    assert result.evidence[0].file_path == "tests/fixtures/buggy_repo/billing.py"


# ═════════════════════════════════════════════════════════════════════════════
# FAILURE-PATH TESTS
# ═════════════════════════════════════════════════════════════════════════════

def test_empty_error_returns_early():
    engine = make_engine([BILLING_CHUNK], VALID_PAYLOAD)
    result = engine.debug("   ")

    assert result.root_cause == "Empty input"
    assert result.evidence == []


def test_malformed_json_raises():
    engine = CodeDebuggingEngine(
        retriever=FakeRetriever([BILLING_CHUNK]),
        context_builder=RepositoryContextBuilder(),
        llm=FakeLLM({}),  # we override generate below
    )
    # Patch generate to return garbage
    engine.llm.generate = lambda prompt: "NOT { valid json ]["

    with pytest.raises(json.JSONDecodeError):
        engine.debug("TypeError: int and str")


def test_llm_evidence_pointing_to_nonexistent_file_is_dropped():
    hallucinated_payload = {
        **VALID_PAYLOAD,
        "evidence": [
            {
                "file_path": "totally/made_up/file.py",
                "start_line": 1,
                "end_line": 5,
                "explanation": "This file does not exist in retrieved chunks",
            }
        ],
    }
    engine = make_engine([BILLING_CHUNK], hallucinated_payload)
    result = engine.debug("TypeError: int and str")

    assert result.evidence == []


def test_no_retrieved_chunks_produces_empty_evidence():
    engine = make_engine([], VALID_PAYLOAD)
    result = engine.debug("TypeError: int and str")

    # Result is still valid — just no grounded evidence
    assert isinstance(result, DebugResult)
    assert result.evidence == []
    assert result.root_cause


def test_missing_required_fields_raises_validation_error():
    bad_payload = {"root_cause": "something broke"}  # missing explanation, suggested_fix, confidence

    with pytest.raises(ValidationError):
        DebugResponseSchema.model_validate(bad_payload)
