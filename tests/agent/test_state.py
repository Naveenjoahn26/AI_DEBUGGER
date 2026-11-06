import pytest
from pydantic import ValidationError

from repository.agent.state.models import (
    AgentState, 
    IterationStatus, 
    ChatMessage, 
    MessageRole, 
    ToolCall, 
    Observation
)

def test_minimal_state():
    # Test 1: Minimal state AgentState(goal="Find authentication bug") works
    state = AgentState(goal="Find authentication bug")
    assert state.goal == "Find authentication bug"


def test_defaults():
    # Test 2: Defaults (iteration=0, messages=[], tool_calls=[], observations=[], status=pending)
    state = AgentState(goal="Test defaults")
    assert state.iteration == 0
    assert state.messages == []
    assert state.tool_calls == []
    assert state.observations == []
    assert state.status == IterationStatus.PENDING


def test_mutation():
    # Test 3: Mutation (add message, tool call, observation, and state reflects them)
    state = AgentState(goal="Test mutation")
    
    msg = ChatMessage(role=MessageRole.USER, content="Hello")
    state.add_message(msg)
    
    tc = ToolCall(id="tc_1", name="search_code", arguments={"query": "auth"})
    state.add_tool_call(tc)
    
    obs = Observation(tool_call_id="tc_1", content="found code")
    state.add_observation(obs)
    
    assert len(state.messages) == 1
    assert state.messages[0].content == "Hello"
    
    assert len(state.tool_calls) == 1
    assert state.tool_calls[0].name == "search_code"
    
    assert len(state.observations) == 1
    assert state.observations[0].content == "found code"


def test_iteration():
    # Test 4: Iteration (iteration=0, then increment it)
    state = AgentState(goal="Test iteration")
    assert state.iteration == 0
    state.increment_iteration()
    assert state.iteration == 1


def test_validation():
    # Test 5: Validation (Invalid status should be rejected)
    with pytest.raises(ValidationError):
        AgentState(goal="Test validation", status="invalid_status_string")
