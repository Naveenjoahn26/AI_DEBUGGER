def calculate_overall_score(
    retrieval_score: float,
    tool_selection_score: float,
    diagnosis_score: float,
) -> float:

    return (
        0.30 * retrieval_score
        + 0.20 * tool_selection_score
        + 0.50 * diagnosis_score
    )
from repository.evaluation.models import (
    OverallEvaluation,
    RetrievalEvaluation,
    ToolSelectionEvaluation,
    DiagnosisEvaluation,
)


class OverallEvaluator:

    def evaluate(
        self,
        retrieval: RetrievalEvaluation,
        tool_selection: ToolSelectionEvaluation,
        diagnosis: DiagnosisEvaluation,
    ) -> OverallEvaluation:

        overall_score = calculate_overall_score(
            retrieval_score=retrieval.score,
            tool_selection_score=tool_selection.score,
            diagnosis_score=diagnosis.score,
        )

        return OverallEvaluation(
            case_id=retrieval.case_id,
            retrieval_score=retrieval.score,
            tool_selection_score=tool_selection.score,
            diagnosis_score=diagnosis.score,
            overall_score=overall_score,
        )