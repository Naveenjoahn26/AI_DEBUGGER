import pytest
from pydantic import BaseModel, Field, ValidationError

from repository.agent.tools.registry import ToolRegistry
from repository.agent.tools.search_code import SearchCodeTool, SearchCodeInput


class FakeRetriever:
    def retrieve(self, query: str, top_k: int = 5):
        if query == "find nothing":
            return []
        return ["fake_chunk"]


class FakeContextBuilder:
    def build(self, chunks):
        return chunks

    def format(self, items):
        return "\n".join(items)


class DummyToolInput(BaseModel):
    name: str


class DummyTool:
    name = "dummy_tool"
    description = "A fake second tool to prove architecture works."
    args_schema = DummyToolInput

    def execute(self, name: str) -> str:
        return f"Hello, {name}!"


def setup_search_tool():
    return SearchCodeTool(
        retriever=FakeRetriever(),
        context_builder=FakeContextBuilder()
    )


# Test 1: SearchCodeTool.name -> "search_code"
def test_search_code_tool_name():
    tool = setup_search_tool()
    assert tool.name == "search_code"


# Test 2: SearchCodeTool.description -> useful description
def test_search_code_tool_description():
    tool = setup_search_tool()
    assert tool.description
    assert "search the codebase" in tool.description.lower()


# Test 3: valid arguments -> search executes
def test_valid_arguments_executes_search():
    tool = setup_search_tool()
    # Directly validate with the Pydantic schema
    args = tool.args_schema(query="login function")
    result = tool.execute(**args.model_dump())
    assert result == "fake_chunk"


# Test 4: invalid arguments -> validation error
def test_invalid_arguments_raises_validation_error():
    tool = setup_search_tool()
    with pytest.raises(ValidationError):
        # Query is required but missing, or wrong type
        tool.args_schema(wrong_field="some value")


# Test 5: registry.execute("search_code", ...) -> correct tool executes
def test_registry_executes_correct_tool():
    registry = ToolRegistry()
    tool = setup_search_tool()
    registry.register(tool)
    
    result = registry.execute("call_1", "search_code", query="my search query")
    assert result.success is True
    assert result.content == "fake_chunk"
    assert result.tool_call_id == "call_1"


# Test 6: registry.execute("unknown_tool", ...) -> controlled error
def test_registry_unknown_tool_raises_error():
    registry = ToolRegistry()
    result = registry.execute("call_2", "unknown_tool", query="something")
    assert result.success is False
    assert "Unknown tool: 'unknown_tool'" in result.error
    assert result.tool_call_id == "call_2"


# Test 7: Add a fake second tool just to prove the architecture works
def test_registry_handles_multiple_tools():
    registry = ToolRegistry()
    search_tool = setup_search_tool()
    dummy_tool = DummyTool()
    
    registry.register(search_tool)
    registry.register(dummy_tool)
    
    # Both tools should execute successfully without registry modifying its internal logic
    search_result = registry.execute("call_3", "search_code", query="test query")
    dummy_result = registry.execute("call_4", "dummy_tool", name="Alice")
    
    assert search_result.success is True
    assert search_result.content == "fake_chunk"
    
    assert dummy_result.success is True
    assert dummy_result.content == "Hello, Alice!"
