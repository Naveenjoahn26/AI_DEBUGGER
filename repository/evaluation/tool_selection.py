from repository.agent.state.models import AgentState
from repository.evaluation.models import (
    EvaluationCase,
    ToolSelectionEvaluation,
)
from repository.evaluation.tool_metrics import (
    calculate_tool_selection_score,
)


class ToolSelectionEvaluator:

    def evaluate_case(
        self,
        case: EvaluationCase,
        state: AgentState,
    ) -> ToolSelectionEvaluation:

        actual_tools = [
            tool_call.name
            for tool_call in state.tool_calls
        ]

        score = calculate_tool_selection_score(
            actual_tools,
            case.expected_tools,
        )

        return ToolSelectionEvaluation(
            case_id=case.case_id,
            expected_tools=case.expected_tools,
            actual_tools=actual_tools,
            score=score,
        )