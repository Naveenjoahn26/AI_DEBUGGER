from repository.agent.state.models import AgentState, ToolCall
from repository.evaluation.models import EvaluationCase
from repository.evaluation.tool_selection import ToolSelectionEvaluator


def test_correct_tool_selection():

    case = EvaluationCase(
        case_id="BUG-001",
        bug_description="Discount calculation is wrong.",
        expected_files=["pricing.py"],
        expected_tools=["search_code"],
        expected_diagnosis="Discount is calculated incorrectly.",
    )

    state = AgentState(
        goal=case.bug_description,
        tool_calls=[
            ToolCall(
                id="call-1",
                name="search_code",
                arguments={"query": "discount calculation"},
            )
        ],
    )

    evaluator = ToolSelectionEvaluator()

    result = evaluator.evaluate_case(case, state)

    assert result.case_id == "BUG-001"
    assert result.actual_tools == ["search_code"]
    assert result.expected_tools == ["search_code"]
    assert result.score == 1.0


def test_wrong_tool_selection():

    case = EvaluationCase(
        case_id="BUG-002",
        bug_description="User creation fails.",
        expected_files=["users.py"],
        expected_tools=["search_code"],
        expected_diagnosis="Missing input is not handled.",
    )

    state = AgentState(
        goal=case.bug_description,
        tool_calls=[
            ToolCall(
                id="call-1",
                name="wrong_tool",
                arguments={},
            )
        ],
    )

    evaluator = ToolSelectionEvaluator()

    result = evaluator.evaluate_case(case, state)

    assert result.actual_tools == ["wrong_tool"]
    assert result.score == 0.0
