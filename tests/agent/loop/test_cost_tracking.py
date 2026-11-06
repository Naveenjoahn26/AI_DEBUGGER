from repository.agent.loop.runner import AgentRunner
from repository.agent.tools.registry import ToolRegistry
from repository.agent.cost import calculate_cost

class FakeUsage:
    def __init__(self, prompt, completion):
        self.prompt_tokens = prompt
        self.completion_tokens = completion

class FakeLLMResponse:
    def __init__(self, usage, model, tool_calls=None, content=""):
        self.usage = usage
        self.model = model
        self.tool_calls = tool_calls
        self.content = content

class FakeLLM:
    def invoke(self, messages):
        # Return 100 input tokens, 50 output tokens
        return FakeLLMResponse(
            usage=FakeUsage(100, 50),
            model="gpt-4-turbo",
            content="Final answer."
        )

def test_cost_calculation():
    # gpt-4-turbo: 0.01 per 1k input, 0.03 per 1k output
    cost = calculate_cost("gpt-4-turbo", 1000, 1000)
    assert cost == 0.04
    
    # Unknown model defaults to 0
    cost2 = calculate_cost("unknown-model", 1000, 1000)
    assert cost2 == 0.0

def test_agent_state_accumulates_tokens():
    llm = FakeLLM()
    runner = AgentRunner(llm=llm, tool_registry=ToolRegistry())
    state = runner.run("Do something")
    
    # Since iteration=1, it made one call to the LLM
    assert state.input_tokens == 100
    assert state.output_tokens == 50
    assert state.total_tokens == 150
    
    # Cost for gpt-4-turbo: 100 * 0.01/1000 + 50 * 0.03/1000 = 0.001 + 0.0015 = 0.0025
    assert state.estimated_cost == 0.0025
