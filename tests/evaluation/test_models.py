from repository.evaluation.models import EvaluationCase, EvaluationResult, RetrievalEvaluation


def test_evaluation_case_creation():
    case = EvaluationCase(
        case_id="BUG-001",
        bug_description="Login returns 401 with a valid JWT.",
        expected_files=["auth.py"],
        expected_tools=["search_code"],
        expected_diagnosis="JWT expiration uses the wrong time unit.",
    )

    assert case.case_id == "BUG-001"
    assert case.expected_files == ["auth.py"]
    assert case.expected_tools == ["search_code"]
    assert case.expected_diagnosis == "JWT expiration uses the wrong time unit."

def test_evaluation_result_creation():
    result = EvaluationResult(
        case_id="BUG-001",
        actual_answer="JWT expiration uses the wrong time unit.",
        passed=True,
        scores={
            "diagnosis": 1.0,
        },
    )

    assert result.case_id == "BUG-001"
    assert result.actual_answer == "JWT expiration uses the wrong time unit."
    assert result.passed is True
    assert result.scores["diagnosis"] == 1.0


def test_retrieval_evaluation_creation():
    evaluation = RetrievalEvaluation(
        case_id="BUG-001",
        retrieved_files=["auth.py", "pricing.py"],
        expected_files=["pricing.py"],
        score=1.0,
    )

    assert evaluation.score == 1.0
    assert "pricing.py" in evaluation.retrieved_files
