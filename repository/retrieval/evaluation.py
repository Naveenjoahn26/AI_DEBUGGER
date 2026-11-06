from dataclasses import dataclass

from repository.models.code_chunk import CodeChunk


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    expected_chunk_name: str


@dataclass(frozen=True)
class RetrievalMetrics:
    total: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float


class RetrievalEvaluator:

    def __init__(self, retriever):
        self.retriever = retriever

    def evaluate(
        self,
        cases: list[RetrievalCase],
    ) -> RetrievalMetrics:

        if not cases:
            return RetrievalMetrics(
                total=0,
                hit_at_1=0.0,
                hit_at_3=0.0,
                hit_at_5=0.0,
            )

        hit_at_1 = 0
        hit_at_3 = 0
        hit_at_5 = 0

        for case in cases:

            results = self.retriever.search(
                case.query,
                top_k=5,
            )

            names = [
                chunk.name
                for chunk in results
            ]

            if case.expected_chunk_name in names[:1]:
                hit_at_1 += 1

            if case.expected_chunk_name in names[:3]:
                hit_at_3 += 1

            if case.expected_chunk_name in names[:5]:
                hit_at_5 += 1

        total = len(cases)

        return RetrievalMetrics(
            total=total,
            hit_at_1=hit_at_1 / total,
            hit_at_3=hit_at_3 / total,
            hit_at_5=hit_at_5 / total,
        )
