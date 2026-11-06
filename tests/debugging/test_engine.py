import json
import pytest
from pydantic import ValidationError

from repository.debugging.engine import CodeDebuggingEngine
from repository.debugging.models import DebugResult
from repository.models.code_chunk import CodeChunk


class FakeRetriever:
    def search(self, query, top_k=5):
        return []


class FakeContextBuilder:
    def build(self, chunks):
        return []
        
    def format(self, items):
        return ""


class FakeLLM:
    def __init__(self):
        self.response_to_return = ""
        
    def generate(self, prompt):
        return self.response_to_return


def test_engine_valid_json():
    # Supply a matching chunk so grounding logic can attach real source code
    matching_chunk = CodeChunk(
        content="def test_func():\n    pass",
        file_path="test.py",
        chunk_type="function",
        name="test_func",
        start_line=1,
        end_line=2,
    )

    class FakeRetrieverWithChunk:
        def search(self, query, top_k=5):
            return [matching_chunk]

    builder = FakeContextBuilder()
    llm = FakeLLM()

    llm.response_to_return = json.dumps({
        "root_cause": "Test cause",
        "explanation": "Test explanation",
        "evidence": [
            {
                "file_path": "test.py",
                "start_line": 1,
                "end_line": 2,
                "explanation": "Test evidence"
            }
        ],
        "suggested_fix": "Test fix",
        "confidence": "high"
    })

    engine = CodeDebuggingEngine(
        retriever=FakeRetrieverWithChunk(),
        context_builder=builder,
        llm=llm
    )

    result = engine.debug("I have a bug")
    assert isinstance(result, DebugResult)
    assert result.root_cause == "Test cause"
    assert len(result.evidence) == 1
    assert result.evidence[0].file_path == "test.py"
    assert result.evidence[0].content == matching_chunk.content


def test_engine_malformed_json():
    retriever = FakeRetriever()
    builder = FakeContextBuilder()
    llm = FakeLLM()
    
    llm.response_to_return = "Not a json { this is invalid"
    
    engine = CodeDebuggingEngine(
        retriever=retriever,
        context_builder=builder,
        llm=llm
    )
    
    with pytest.raises(json.JSONDecodeError):
        engine.debug("I have a bug")


def test_engine_missing_fields_json():
    retriever = FakeRetriever()
    builder = FakeContextBuilder()
    llm = FakeLLM()
    
    llm.response_to_return = json.dumps({
        "root_cause": "Test cause"
        # missing explanation, suggested_fix, etc.
    })
    
    engine = CodeDebuggingEngine(
        retriever=retriever,
        context_builder=builder,
        llm=llm
    )
    
    with pytest.raises(ValidationError):
        engine.debug("I have a bug")


def test_engine_markdown_wrapped_json():
    retriever = FakeRetriever()
    builder = FakeContextBuilder()
    llm = FakeLLM()
    
    llm.response_to_return = "```json\n" + json.dumps({
        "root_cause": "Test cause",
        "explanation": "Test explanation",
        "evidence": [],
        "suggested_fix": "Test fix",
        "confidence": "high"
    }) + "\n```"
    
    engine = CodeDebuggingEngine(
        retriever=retriever,
        context_builder=builder,
        llm=llm
    )
    
    result = engine.debug("I have a bug")
    assert result.root_cause == "Test cause"
