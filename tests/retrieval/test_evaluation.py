from repository.models.code_chunk import CodeChunk
from repository.retrieval.evaluation import (
    RetrievalCase,
    RetrievalEvaluator,
)


def make_chunk(name: str) -> CodeChunk:
    return CodeChunk(
        content=f"def {name}(): pass",
        file_path="app.py",
        chunk_type="function",
        name=name,
        start_line=1,
        end_line=1,
    )


class FakeRetriever:

    def search(self, query, top_k=5):

        if "authentication" in query:
            return [
                make_chunk("login"),
                make_chunk("authenticate_user"),
                make_chunk("helper"),
            ]

        return [
            make_chunk("calculate_total"),
            make_chunk("other"),
        ]


def test_retrieval_evaluation():

    evaluator = RetrievalEvaluator(
        FakeRetriever()
    )

    cases = [
        RetrievalCase(
            query="where is authentication?",
            expected_chunk_name="authenticate_user",
        ),
        RetrievalCase(
            query="calculate order total",
            expected_chunk_name="calculate_total",
        ),
    ]

    metrics = evaluator.evaluate(cases)

    assert metrics.total == 2
    assert metrics.hit_at_1 == 0.5
    assert metrics.hit_at_3 == 1.0
    assert metrics.hit_at_5 == 1.0
