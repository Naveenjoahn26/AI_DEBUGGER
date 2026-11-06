"""
tests/integration/test_end_to_end_api.py

End-to-end integration tests for the /debug endpoint.
Mocks out external APIs (HuggingFace, Groq, Chroma DB via temp directory) 
but runs the entire pipeline end-to-end (ingestion -> indexing -> agent).
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.ingestion.test_cloner import _make_local_bare_repo

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers & Mocks
# ---------------------------------------------------------------------------

class FakeGroqResponse:
    """Mocks the response from Groq client for our llm_adapter."""
    def __init__(self, content=None, tool_calls=None):
        self.choices = [MagicMock()]
        self.choices[0].message = MagicMock()
        self.choices[0].message.content = content
        self.choices[0].message.tool_calls = tool_calls
        
        self.usage = MagicMock()
        self.usage.prompt_tokens = 10
        self.usage.completion_tokens = 20
        self.model = "mock-groq-model"

class FakeToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = json.dumps(arguments)


@pytest.fixture
def mock_embedder():
    with patch("app.services.debug_service.CodeEmbedder") as MockEmbedder:
        instance = MockEmbedder.return_value
        instance.embed.return_value = [[0.1] * 384]
        yield instance

@pytest.fixture
def mock_chroma_dir():
    with tempfile.TemporaryDirectory(prefix="ai_debug_chroma_", ignore_cleanup_errors=True) as tmp_dir:
        # Patch the DebugService to use the temp directory for Chroma
        with patch("app.api.routes.debug._service._chroma_dir", tmp_dir):
            yield tmp_dir

@pytest.fixture
def mock_groq():
    with patch("repository.agent.llm_adapter.Groq") as MockGroq:
        client_instance = MockGroq.return_value
        
        # We need the Groq LLM Adapter to return something specific.
        # It's easier to mock the `GroqAgentLLM.invoke` directly for fine-grained control
        # over the iterations of the AgentRunner, but let's mock Groq client since 
        # the adapter wraps it.
        yield client_instance

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_successful_end_to_end_debug(mock_embedder, mock_chroma_dir, mock_groq):
    """
    Tests the full pipeline on a real local repository clone:
    - clones the repo
    - chunks/embeds/indexes it
    - agent searches the code
    - agent diagnoses the bug
    - cleanup occurs
    """
    tmp, bare_path = _make_local_bare_repo()
    try:
        # Mock LLM to first call the search_code tool, then answer.
        mock_tool_call = FakeToolCall(
            id="call_1", 
            name="search_code", 
            arguments={"query": "test"}
        )
        
        # First call: return a tool call
        resp1 = FakeGroqResponse(content=None, tool_calls=[mock_tool_call])
        # Second call: return the final diagnosis
        resp2 = FakeGroqResponse(content="The issue is in the README.")
        
        mock_groq.chat.completions.create.side_effect = [resp1, resp2]
        
        # Override the env var to prevent Groq API key missing errors
        with patch.dict(os.environ, {"GROQ_API_KEY": "mock_key"}):
            response = client.post(
                "/debug/",
                json={
                    "repo_url": bare_path.as_uri(),
                    "bug_description": "Find the issue in the code."
                }
            )
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["diagnosis"] == "The issue is in the README."
        assert data["metadata"]["iterations"] == 2
        # Since the test repo has 0 python files (just README.md)
        assert data["metadata"]["files_indexed"] == 0
        
    finally:
        tmp.cleanup()


def test_end_to_end_empty_repository(mock_embedder, mock_chroma_dir, mock_groq):
    """
    Tests the pipeline gracefully handles an empty repo (0 chunks).
    """
    tmp, bare_path = _make_local_bare_repo()
    try:
        resp = FakeGroqResponse(content="No python code found to debug.")
        mock_groq.chat.completions.create.side_effect = [resp]
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "mock_key"}):
            response = client.post(
                "/debug/",
                json={
                    "repo_url": bare_path.as_uri(),
                    "bug_description": "Find the issue."
                }
            )
            
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["metadata"]["chunks_indexed"] == 0
        
    finally:
        tmp.cleanup()


def test_end_to_end_agent_failure(mock_embedder, mock_chroma_dir, mock_groq):
    """
    If the agent hits max iterations without a final answer, it should fail gracefully.
    """
    tmp, bare_path = _make_local_bare_repo()
    try:
        # Constantly return tool calls to force max iterations (5 by default)
        mock_tool_call = FakeToolCall(id="call_x", name="search_code", arguments={"query": "loop"})
        resp = FakeGroqResponse(content=None, tool_calls=[mock_tool_call])
        
        # We need enough responses to exceed max_iterations (default 5 in debug_service)
        mock_groq.chat.completions.create.side_effect = [resp] * 10
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "mock_key"}):
            response = client.post(
                "/debug/",
                json={
                    "repo_url": bare_path.as_uri(),
                    "bug_description": "This will loop forever."
                }
            )
            
        assert response.status_code == 200 # HTTP is fine
        data = response.json()
        assert data["status"] == "failed"
        assert "could not produce a diagnosis" in data["diagnosis"]
        assert data["metadata"]["iterations"] == 5
        
    finally:
        tmp.cleanup()


def test_end_to_end_cleanup_on_success(mock_embedder, mock_chroma_dir, mock_groq):
    """
    Verifies that the temporary directory for the cloned repository is cleaned up.
    """
    tmp, bare_path = _make_local_bare_repo()
    captured_clone_dir = None
    
    # We'll hook into the IndexingPipeline.run to capture the temp dir path
    original_run = None
    
    def mock_run_capture(self, repo_path):
        nonlocal captured_clone_dir
        captured_clone_dir = repo_path
        return original_run(self, repo_path)
    
    try:
        resp = FakeGroqResponse(content="Done")
        mock_groq.chat.completions.create.side_effect = [resp]
        
        from repository.ingestion.indexer import IndexingPipeline
        original_run = IndexingPipeline.run
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "mock_key"}), \
             patch.object(IndexingPipeline, "run", mock_run_capture):
            
            client.post(
                "/debug/",
                json={
                    "repo_url": bare_path.as_uri(),
                    "bug_description": "Clean me up."
                }
            )
            
        assert captured_clone_dir is not None
        assert not captured_clone_dir.exists(), "Clone directory was not cleaned up after success."
        
    finally:
        tmp.cleanup()


def test_end_to_end_cleanup_on_failure(mock_embedder, mock_chroma_dir, mock_groq):
    """
    Verifies cleanup occurs even when the agent throws a hard exception.
    """
    tmp, bare_path = _make_local_bare_repo()
    captured_clone_dir = None
    original_run = None
    
    def mock_run_capture(self, repo_path):
        nonlocal captured_clone_dir
        captured_clone_dir = repo_path
        raise RuntimeError("Hard failure during indexing")
    
    try:
        from repository.ingestion.indexer import IndexingPipeline
        original_run = IndexingPipeline.run
        
        with patch.dict(os.environ, {"GROQ_API_KEY": "mock_key"}), \
             patch.object(IndexingPipeline, "run", mock_run_capture):
            
            response = client.post(
                "/debug/",
                json={
                    "repo_url": bare_path.as_uri(),
                    "bug_description": "Crash immediately."
                }
            )
            
        assert response.status_code == 500
        assert captured_clone_dir is not None
        assert not captured_clone_dir.exists(), "Clone directory was not cleaned up after exception."
        
    finally:
        tmp.cleanup()
