from repository.agent.prompts.builder import PromptBuilder
from repository.agent.state.models import ChatMessage, MessageRole
from repository.agent.tools.search_code import SearchCodeTool
from repository.agent.planning.models import Plan, PlanStep, PlanStepStatus


class DummyInspectFileTool:
    name = "inspect_file"
    description = "Use this tool to inspect the contents of a specific file."
    args_schema = None


def test_goal_appears():
    # Test 1 — goal appears
    goal = "Find authentication bug"
    prompt = PromptBuilder.build(goal=goal, tools=[])
    
    assert goal in prompt
    assert "# Goal" in prompt


def test_tool_appears():
    # Test 2 — tool appears (register search_code and verify name/description)
    search_tool = SearchCodeTool(retriever=None, context_builder=None)
    
    prompt = PromptBuilder.build(goal="test", tools=[search_tool])
    
    assert search_tool.name in prompt
    assert "search the codebase" in prompt


def test_conversation_appears():
    # Test 3 — conversation appears (Given a previous user/assistant message)
    conversation = [
        ChatMessage(role=MessageRole.USER, content="Hello AI"),
        ChatMessage(role=MessageRole.ASSISTANT, content="How can I help?")
    ]
    
    prompt = PromptBuilder.build(goal="test", tools=[], conversation=conversation)
    
    assert "Hello AI" in prompt
    assert "How can I help?" in prompt
    assert "USER" in prompt
    assert "ASSISTANT" in prompt


def test_multiple_tools():
    # Test 4 — multiple tools (search_code and inspect_file)
    search_tool = SearchCodeTool(retriever=None, context_builder=None)
    inspect_tool = DummyInspectFileTool()
    
    prompt = PromptBuilder.build(goal="test", tools=[search_tool, inspect_tool])
    
    assert search_tool.name in prompt
    assert inspect_tool.name in prompt
    assert inspect_tool.description in prompt


def test_no_hardcoded_tools():
    # Test 5 — no hardcoded tools
    # If a tool is removed from the list, it should NOT appear in the prompt
    search_tool = SearchCodeTool(retriever=None, context_builder=None)
    inspect_tool = DummyInspectFileTool()
    
    # Pass ONLY inspect_tool
    prompt = PromptBuilder.build(goal="test", tools=[inspect_tool])
    
    assert inspect_tool.name in prompt
    assert search_tool.name not in prompt  # Proves the prompt is dynamic!


def test_plan_appears():
    # Test 6 — plan appears
    plan = Plan(
        steps=[
            PlanStep(description="Step A", status=PlanStepStatus.COMPLETED),
            PlanStep(description="Step B", status=PlanStepStatus.IN_PROGRESS),
        ],
        current_step=1
    )
    
    prompt = PromptBuilder.build(goal="test", plan=plan)
    
    assert "# Current Plan" in prompt
    assert "[completed] Step A" in prompt
    assert "[in_progress] Step B" in prompt
    assert "# Current Step\nStep B" in prompt


def test_memory_appears():
    # Test 7 — memory appears
    from repository.agent.memory.models import Memory
    
    memories = [
        Memory(key="auth", content="JWT authentication is handled in auth/service.py"),
        Memory(key="db", content="PostgreSQL is used for persistence")
    ]
    
    prompt = PromptBuilder.build(goal="test", memories=memories)
    
    assert "# Project Memory" in prompt
    assert "- JWT authentication is handled in auth/service.py" in prompt
    assert "- PostgreSQL is used for persistence" in prompt
