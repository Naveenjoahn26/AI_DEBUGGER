from repository.agent.loop.runner import AgentRunner
from repository.agent.state.models import IterationStatus
from repository.agent.tools.registry import ToolRegistry


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def invoke(self, messages):
        return self.response


def test_agent_completes_with_final_answer():
    llm = FakeLLM(
        response="The authentication function is failing."
    )
    registry = ToolRegistry()

    runner = AgentRunner(
        llm=llm,
        tool_registry=registry,
    )

    state = runner.run("Find the authentication bug.")

    assert state.status == IterationStatus.COMPLETED
    assert state.iteration == 1
    
    # We can also verify that the final message was captured in conversation history
    assert state.messages[-1].role == "assistant"
    assert state.messages[-1].content == "The authentication function is failing."
