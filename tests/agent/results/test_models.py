import pytest
from pydantic import ValidationError
from repository.agent.results.models import ToolResult


def test_success_tool_result():
    # Test 1 - success
    result = ToolResult(
        tool_call_id="call_123",
        success=True,
        content="Found authenticate_user in auth/service.py"
    )
    assert result.tool_call_id == "call_123"
    assert result.success is True
    assert result.content == "Found authenticate_user in auth/service.py"
    assert result.error is None


def test_failure_tool_result():
    # Test 2 - failure
    result = ToolResult(
        tool_call_id="call_123",
        success=False,
        error="File could not be read"
    )
    assert result.tool_call_id == "call_123"
    assert result.success is False
    assert result.content == ""
    assert result.error == "File could not be read"


def test_validation_missing_tool_call_id():
    # Test 3 - validation missing tool_call_id
    with pytest.raises(ValidationError) as exc:
        ToolResult(
            success=True,
            content="Some content"
        )
    assert "tool_call_id" in str(exc.value)


def test_empty_content_allowed():
    # Test 4 - empty content allowed
    result = ToolResult(
        tool_call_id="call_999",
        success=True,
        content=""
    )
    assert result.success is True
    assert result.content == ""
