import pytest
from typing import Any
from repository.agent.loop.runner import AgentRunner
from repository.agent.tools.registry import ToolRegistry
from repository.agent.state.models import IterationStatus


class FlakyTool:
    name = "flaky_tool"
    description = "A tool that fails."
    args_schema = None
    
    def execute(self, **kwargs) -> str:
        raise ValueError("Simulated tool failure!")


class SuccessTool:
    name = "success_tool"
    description = "A tool that works."
    args_schema = None
    
    def execute(self, **kwargs) -> str:
        return "It worked!"


class RecoveryLLM:
    """An LLM that tries flaky_tool first, then recovers by using success_tool."""
    def __init__(self):
        self.invocations = 0

    def invoke(self, messages: list[Any]) -> Any:
        self.invocations += 1
        
        class FakeResponse:
            def __init__(self, tool_calls, content=""):
                self.tool_calls = tool_calls
                self.content = content
                
        class FakeToolCall:
            def __init__(self, id, name):
                self.id = id
                self.name = name
                self.arguments = {}

        if self.invocations == 1:
            # First attempt: Try the tool that will fail
            return FakeResponse([FakeToolCall("call_1", "flaky_tool")])
        elif self.invocations == 2:
            # Second attempt: Recover by calling the tool that works
            return FakeResponse([FakeToolCall("call_2", "success_tool")])
        else:
            # Third attempt: Conclude
            return FakeResponse([], content="I have recovered and succeeded.")


class StubbornLLM:
    """An LLM that keeps trying the same failing tool indefinitely."""
    def invoke(self, messages: list[Any]) -> Any:
        class FakeResponse:
            def __init__(self, tool_calls, content=""):
                self.tool_calls = tool_calls
                self.content = content
                
        class FakeToolCall:
            def __init__(self, id, name):
                self.id = id
                self.name = name
                self.arguments = {}

        return FakeResponse([FakeToolCall("call_X", "flaky_tool")])


def test_tool_exception_creates_error_observation():
    registry = ToolRegistry()
    registry.register(FlakyTool())
    
    llm = StubbornLLM()
    runner = AgentRunner(llm=llm, tool_registry=registry, max_iterations=2)
    
    state = runner.run("test")
    
    # Verify the observation was created with the error
    assert len(state.observations) > 0
    first_obs = state.observations[0]
    assert first_obs.is_error is True
    assert "Simulated tool failure!" in first_obs.content


def test_agent_recovers_from_failure():
    registry = ToolRegistry()
    registry.register(FlakyTool())
    registry.register(SuccessTool())
    
    llm = RecoveryLLM()
    runner = AgentRunner(llm=llm, tool_registry=registry, max_iterations=5)
    
    state = runner.run("Find the issue")
    
    assert state.status == IterationStatus.COMPLETED
    assert state.iteration == 3
    
    # Verify first observation was an error
    assert state.observations[0].is_error is True
    assert state.observations[0].tool_call_id == "call_1"
    
    # Verify second observation was a success
    assert state.observations[1].is_error is False
    assert state.observations[1].tool_call_id == "call_2"
    assert "It worked!" in state.observations[1].content


def test_agent_stops_at_iteration_limit():
    registry = ToolRegistry()
    registry.register(FlakyTool())
    
    llm = StubbornLLM()
    MAX_ITER = 3
    runner = AgentRunner(llm=llm, tool_registry=registry, max_iterations=MAX_ITER)
    
    state = runner.run("test")
    
    assert state.status == IterationStatus.FAILED
    assert state.iteration == MAX_ITER
    
    # The last observation should be the max_iterations error
    assert state.observations[-1].is_error is True
    assert "maximum of 3 iterations" in state.observations[-1].content
