from repository.evaluation.overall import calculate_overall_score, OverallEvaluator
from repository.evaluation.models import (
    RetrievalEvaluation,
    ToolSelectionEvaluation,
    DiagnosisEvaluation,
)

def test_overall_score():
    score = calculate_overall_score(
        retrieval_score=1.0,
        tool_selection_score=1.0,
        diagnosis_score=0.8,
    )
    assert score == 0.9


def test_perfect_overall_score():
    score = calculate_overall_score(
        retrieval_score=1.0,
        tool_selection_score=1.0,
        diagnosis_score=1.0,
    )
    assert score == 1.0


def test_overall_evaluator():
    retrieval = RetrievalEvaluation(
        case_id="BUG-001",
        retrieved_files=["pricing.py"],
        expected_files=["pricing.py"],
        score=1.0,
    )

    tool_selection = ToolSelectionEvaluation(
        case_id="BUG-001",
        expected_tools=["search_code"],
        actual_tools=["search_code"],
        score=1.0,
    )

    diagnosis = DiagnosisEvaluation(
        case_id="BUG-001",
        expected_diagnosis="Discount is applied twice.",
        actual_diagnosis="The discount is applied twice.",
        score=0.8,
    )

    evaluator = OverallEvaluator()

    result = evaluator.evaluate(
        retrieval,
        tool_selection,
        diagnosis,
    )

    assert result.case_id == "BUG-001"
    assert result.retrieval_score == 1.0
    assert result.tool_selection_score == 1.0
    assert result.diagnosis_score == 0.8
    assert result.overall_score == 0.9
