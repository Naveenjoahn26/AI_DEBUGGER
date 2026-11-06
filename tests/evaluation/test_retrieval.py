from repository.evaluation.retrieval import RetrievalEvaluator
from repository.evaluation.models import EvaluationCase


class FakeChunk:
    def __init__(self, file_path):
        self.file_path = file_path


class FakeRetrieverSuccess:
    def retrieve(self, query, top_k=5):
        return [
            FakeChunk("auth.py"),
            FakeChunk("pricing.py"),
        ]


class FakeRetrieverFailure:
    def retrieve(self, query, top_k=5):
        return [
            FakeChunk("auth.py"),
            FakeChunk("database.py"),
        ]


def test_retrieval_evaluator_success_case():
    evaluator = RetrievalEvaluator(FakeRetrieverSuccess())

    case = EvaluationCase(
        case_id="BUG-001",
        bug_description="Discount calculation is wrong.",
        expected_files=["pricing.py"],
        expected_tools=["search_code"],
        expected_diagnosis="Discount is added instead of subtracted.",
    )

    result = evaluator.evaluate_case(case, top_k=5)

    assert result.case_id == "BUG-001"
    assert "pricing.py" in result.retrieved_files
    assert result.score == 1.0


def test_retrieval_evaluator_failure_case():
    evaluator = RetrievalEvaluator(FakeRetrieverFailure())

    case = EvaluationCase(
        case_id="BUG-001",
        bug_description="Discount calculation is wrong.",
        expected_files=["pricing.py"],
        expected_tools=["search_code"],
        expected_diagnosis="Discount is added instead of subtracted.",
    )

    result = evaluator.evaluate_case(case, top_k=5)

    assert result.case_id == "BUG-001"
    assert "pricing.py" not in result.retrieved_files
    assert result.score == 0.0
