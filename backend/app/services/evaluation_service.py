"""
Compute real retrieval evaluation metrics from the sample fixture repository.

Baseline: BM25 lexical retrieval
Improved: Hybrid (semantic + BM25) retrieval
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
from repository.indexing.chunker import CodeChunker
from repository.language.detector import LanguageDetector
from repository.reader.reader import CodeReader
from repository.retrieval.evaluation import RetrievalCase, RetrievalEvaluator
from repository.retrieval.hybrid import HybridRetriever
from repository.retrieval.lexical import BM25Retriever
from repository.retrieval.semantic import SemanticRetriever

from app.schemas.evaluation import EvaluationSummaryResponse, MetricComparison

logger = logging.getLogger(__name__)

FIXTURE_REPO = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "sample_repo"
)

EVALUATION_CASES = [
    RetrievalCase(
        query="where is user authentication handled?",
        expected_chunk_name="authenticate_user",
    ),
    RetrievalCase(
        query="where is the JWT token created?",
        expected_chunk_name="create_token",
    ),
    RetrievalCase(
        query="where are users created?",
        expected_chunk_name="create_user",
    ),
    RetrievalCase(
        query="where is the database connection created?",
        expected_chunk_name="create_database_connection",
    ),
]


def _build_index(chroma_dir: Path):
    detector = LanguageDetector()
    reader = CodeReader(detector)
    chunker = CodeChunker()
    embedder = CodeEmbedder()
    vector_store = CodeVectorStore(
        collection_name="evaluation_metrics",
        persist_directory=str(chroma_dir),
    )

    files = list(FIXTURE_REPO.glob("*.py"))
    all_chunks = []
    for py_file in files:
        document = reader.read(py_file)
        all_chunks.extend(chunker.chunk(document))

    if all_chunks:
        from repository.embeddings.formatter import CodeChunkFormatter
        from repository.embeddings.pipeline import CodeEmbeddingPipeline

        pipeline = CodeEmbeddingPipeline(
            embedder=embedder,
            formatter=CodeChunkFormatter(),
        )
        embeddings = pipeline.embed_chunks(all_chunks)
        vector_store.add(embeddings=embeddings, chunks=all_chunks)

    return all_chunks, embedder, vector_store


def _mean_reciprocal_rank(retriever, cases: list[RetrievalCase], k: int = 5) -> float:
    if not cases:
        return 0.0

    total = 0.0
    for case in cases:
        results = retriever.search(case.query, top_k=k)
        names = [chunk.name for chunk in results]
        rank = 0
        for index, name in enumerate(names[:k], start=1):
            if name == case.expected_chunk_name:
                rank = index
                break
        total += (1.0 / rank) if rank else 0.0
    return total / len(cases)


@lru_cache(maxsize=1)
def get_evaluation_summary() -> EvaluationSummaryResponse:
    chroma_dir = Path(__file__).resolve().parents[3] / "backend" / "data" / "eval_chroma"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    try:
        chunks, embedder, vector_store = _build_index(chroma_dir)
        semantic = SemanticRetriever(embedder=embedder, vector_store=vector_store)
        bm25 = BM25Retriever(chunks)
        hybrid = HybridRetriever(semantic_retriever=semantic, lexical_retriever=bm25)

        bm25_eval = RetrievalEvaluator(bm25)
        hybrid_eval = RetrievalEvaluator(hybrid)

        bm25_metrics = bm25_eval.evaluate(EVALUATION_CASES)
        hybrid_metrics = hybrid_eval.evaluate(EVALUATION_CASES)

        bm25_mrr = _mean_reciprocal_rank(bm25, EVALUATION_CASES)
        hybrid_mrr = _mean_reciprocal_rank(hybrid, EVALUATION_CASES)

        return EvaluationSummaryResponse(
            dataset=str(FIXTURE_REPO),
            total_cases=len(EVALUATION_CASES),
            metrics=[
                MetricComparison(
                    label="Recall@5",
                    baseline=round(bm25_metrics.hit_at_5 * 100, 1),
                    improved=round(hybrid_metrics.hit_at_5 * 100, 1),
                    unit="%",
                    description="Fraction of queries where the expected chunk appears in top 5 results.",
                ),
                MetricComparison(
                    label="MRR@5",
                    baseline=round(bm25_mrr * 100, 1),
                    improved=round(hybrid_mrr * 100, 1),
                    unit="%",
                    description="Mean reciprocal rank of the expected chunk within top 5.",
                ),
                MetricComparison(
                    label="Hit@1",
                    baseline=round(bm25_metrics.hit_at_1 * 100, 1),
                    improved=round(hybrid_metrics.hit_at_1 * 100, 1),
                    unit="%",
                    description="Fraction of queries where the expected chunk ranks first.",
                ),
            ],
            notes=[
                "Baseline uses BM25 lexical retrieval only.",
                "Improved uses hybrid semantic + BM25 retrieval (RRF fusion).",
                "Agent-level metrics (tool selection, diagnosis accuracy) require live benchmark runs against evaluation cases.",
            ],
        )
    except Exception as exc:
        logger.exception("evaluation_summary_failed: %s", exc)
        return EvaluationSummaryResponse(
            dataset=str(FIXTURE_REPO),
            total_cases=len(EVALUATION_CASES),
            metrics=[],
            notes=[f"Evaluation could not be computed: {exc}"],
        )
