from pathlib import Path

from repository.reader.reader import CodeReader
from repository.language.detector import LanguageDetector
from repository.indexing.chunker import CodeChunker
from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
from repository.intelligence.indexer import RepositoryIndexer

from repository.retrieval.semantic import SemanticRetriever
from repository.retrieval.lexical import BM25Retriever
from repository.retrieval.hybrid import HybridRetriever
from repository.retrieval.evaluation import RetrievalEvaluator, RetrievalCase


FIXTURE_REPO = (
    Path(__file__).parent.parent
    / "fixtures"
    / "sample_repo"
)


def build_index(tmp_path):

    detector = LanguageDetector()

    reader = CodeReader(detector)

    chunker = CodeChunker()

    embedder = CodeEmbedder()

    vector_store = CodeVectorStore(
        collection_name="hybrid_test",
        persist_directory=str(tmp_path / "chroma_db"),
    )

    indexer = RepositoryIndexer(
        reader=reader,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )

    files = list(
        FIXTURE_REPO.glob("*.py")
    )

    chunks = indexer.index(files)

    return (
        chunks,
        embedder,
        vector_store,
    )


def test_semantic_retrieval(tmp_path):

    chunks, embedder, vector_store = build_index(tmp_path)

    query_embedding = embedder.embed(
        ["where is user authentication handled?"]
    )[0]

    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=5,
    )

    assert results

    names = [
        chunk.name
        for chunk in results
    ]

    assert "authenticate_user" in names


def test_hybrid_retrieval_multiple_queries(tmp_path):

    chunks, embedder, vector_store = build_index(tmp_path)

    semantic = SemanticRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25 = BM25Retriever(chunks)

    hybrid = HybridRetriever(
        semantic_retriever=semantic,
        lexical_retriever=bm25,
    )

    cases = [
        (
            "where is user authentication handled?",
            "authenticate_user",
        ),
        (
            "where is the JWT token created?",
            "create_token",
        ),
        (
            "where are users created?",
            "create_user",
        ),
        (
            "where is the database connection created?",
            "create_database_connection",
        ),
    ]

    for query, expected in cases:
        results = hybrid.search(
            query,
            top_k=5,
        )

        names = [
            chunk.name
            for chunk in results
        ]

        assert expected in names

def test_evaluate_hybrid_retrieval(tmp_path):
    chunks, embedder, vector_store = build_index(tmp_path)

    semantic = SemanticRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )

    bm25 = BM25Retriever(chunks)

    hybrid = HybridRetriever(
        semantic_retriever=semantic,
        lexical_retriever=bm25,
    )

    cases = [
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

    evaluator = RetrievalEvaluator(hybrid)
    metrics = evaluator.evaluate(cases)

    print("EVALUATION METRICS:")
    print(metrics)
