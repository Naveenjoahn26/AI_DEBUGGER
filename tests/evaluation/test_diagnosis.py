from repository.evaluation.diagnosis import DiagnosisEvaluator
from repository.evaluation.models import EvaluationCase


class FakeLLM:
    def __init__(self, response):
        self.response = response

    def invoke(self, messages):
        return self.response


def test_diagnosis_evaluation():
    case = EvaluationCase(
        case_id="BUG-001",
        bug_description="Discount calculation is wrong.",
        expected_files=["pricing.py"],
        expected_tools=["search_code"],
        expected_diagnosis="Discount is applied twice.",
    )

    evaluator = DiagnosisEvaluator(
        FakeLLM("0.9")
    )

    result = evaluator.evaluate_case(
        case,
        "The discount is applied twice in the calculation."
    )

    assert result.case_id == "BUG-001"
    assert result.score == 0.9


def test_wrong_diagnosis():
    case = EvaluationCase(
        case_id="BUG-002",
        bug_description="Database connection fails.",
        expected_files=["database.py"],
        expected_tools=["search_code"],
        expected_diagnosis="Database URL is invalid.",
    )

    evaluator = DiagnosisEvaluator(
        FakeLLM("0.0")
    )

    result = evaluator.evaluate_case(
        case,
        "The frontend CSS has an incorrect margin."
    )

    assert result.score == 0.0
