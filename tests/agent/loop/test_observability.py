import logging
from repository.agent.loop.runner import AgentRunner
from repository.agent.tools.registry import ToolRegistry


class FakeLLM:
    def invoke(self, messages):
        class FakeResponse:
            def __init__(self, tool_calls, content=""):
                self.tool_calls = tool_calls
                self.content = content
                
        class FakeToolCall:
            def __init__(self, id, name):
                self.id = id
                self.name = name
                self.arguments = {}

        return FakeResponse([FakeToolCall("call_123", "success_tool")])


class FakeLLMComplete:
    def invoke(self, messages):
        class FakeResponse:
            def __init__(self, tool_calls, content):
                self.tool_calls = tool_calls
                self.content = content
        return FakeResponse(None, "I am done.")


class SuccessTool:
    name = "success_tool"
    description = "Works perfectly."
    args_schema = None
    
    def execute(self, **kwargs):
        return "Success data"


class FlakyTool:
    name = "flaky_tool"
    description = "Fails perfectly."
    args_schema = None
    
    def execute(self, **kwargs):
        raise ValueError("Fail data")


def test_agent_observability_success_flow(caplog):
    caplog.set_level(logging.INFO)
    
    registry = ToolRegistry()
    registry.register(SuccessTool())
    
    runner = AgentRunner(llm=FakeLLM(), tool_registry=registry, max_iterations=1)
    
    runner.run("Find the bug")
    
    logs = [record.message for record in caplog.records]
    
    assert any("agent_started" in msg for msg in logs)
    assert any("llm_response" in msg for msg in logs)
    assert any("tool_called" in msg for msg in logs)
    assert any("tool_completed" in msg for msg in logs)
    assert any("agent_completed: Stopped due to max iterations" in msg for msg in logs)


def test_agent_observability_completion(caplog):
    caplog.set_level(logging.INFO)
    
    registry = ToolRegistry()
    runner = AgentRunner(llm=FakeLLMComplete(), tool_registry=registry)
    
    runner.run("Find the bug")
    
    logs = [record.message for record in caplog.records]
    
    assert any("agent_started" in msg for msg in logs)
    assert any("llm_response" in msg for msg in logs)
    assert any("agent_completed: Final answer generated" in msg for msg in logs)


def test_agent_observability_tool_failure(caplog):
    caplog.set_level(logging.INFO)
    
    class FakeLLMFlaky:
        def invoke(self, messages):
            class FakeResponse:
                def __init__(self, tool_calls, content=""):
                    self.tool_calls = tool_calls
                    self.content = content
                    
            class FakeToolCall:
                def __init__(self, id, name):
                    self.id = id
                    self.name = name
                    self.arguments = {}

            return FakeResponse([FakeToolCall("call_123", "flaky_tool")])

    registry = ToolRegistry()
    registry.register(FlakyTool())
    
    runner = AgentRunner(llm=FakeLLMFlaky(), tool_registry=registry, max_iterations=1)
    
    runner.run("Find the bug")
    
    logs = [record.message for record in caplog.records]
    
    assert any("agent_started" in msg for msg in logs)
    assert any("llm_response" in msg for msg in logs)
    assert any("tool_called" in msg for msg in logs)
    assert any("tool_failed" in msg for msg in logs)
