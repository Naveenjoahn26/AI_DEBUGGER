from repository.agent.loop.runner import AgentRunner
from repository.agent.tools.registry import ToolRegistry
from repository.agent.memory.store import MemoryStore
from repository.agent.memory.models import Memory
from repository.agent.state.models import IterationStatus


class SpyLLM:
    """An LLM double that records the messages it receives."""
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.received_messages = []

    def invoke(self, messages):
        self.received_messages.append(messages)
        return self.response_text


def test_memory_end_to_end_flow():
    # 1. Setup agent with memory store
    memory_store = MemoryStore()
    registry = ToolRegistry()
    
    # Pre-populate memory (as if it was learned in a previous run)
    memory_store.save(Memory(
        key="auth", 
        content="JWT authentication is handled in auth/service.py"
    ))
    # Add an irrelevant memory to prove it isn't injected
    memory_store.save(Memory(
        key="db", 
        content="Database uses PostgreSQL"
    ))
    
    llm = SpyLLM(response_text="The authentication is in auth/service.py")
    
    runner = AgentRunner(
        llm=llm,
        tool_registry=registry,
        memory_store=memory_store
    )
    
    # 2. Run the agent with a goal that should trigger memory retrieval
    goal = "Where is authentication implemented?"
    state = runner.run(goal)
    
    # 3. Assertions
    assert state.status == IterationStatus.COMPLETED
    assert len(llm.received_messages) == 1
    
    # Extract the messages sent to the LLM in the first iteration
    messages_sent = llm.received_messages[0]
    
    # First message should be the dynamically constructed system prompt
    system_msg = messages_sent[0]
    assert system_msg.role == "system"
    system_prompt = system_msg.content
    
    # Verify the relevant memory was retrieved and injected
    assert "# Project Memory" in system_prompt
    assert "JWT authentication is handled in auth/service.py" in system_prompt
    
    # Verify irrelevant memory wasn't injected
    assert "Database uses PostgreSQL" not in system_prompt
    
    # Verify agent successfully finished the run
    assert state.messages[-1].role == "assistant"
    assert "auth/service.py" in state.messages[-1].content
