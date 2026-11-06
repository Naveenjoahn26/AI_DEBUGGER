from pathlib import Path

from repository.reader.reader import CodeReader
from repository.language.detector import LanguageDetector
from repository.indexing.chunker import CodeChunker
from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
from repository.intelligence.indexer import RepositoryIndexer


FIXTURE_REPO = (
    Path(__file__).parent.parent
    / "fixtures"
    / "sample_repo"
)


def test_real_repository_indexing(tmp_path):

    detector = LanguageDetector()

    reader = CodeReader(detector)

    chunker = CodeChunker()

    embedder = CodeEmbedder()

    vector_store = CodeVectorStore(
        collection_name="integration_test",
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

    assert chunks

    names = {
        chunk.name
        for chunk in chunks
    }

    assert "authenticate_user" in names
    assert "create_token" in names
    assert "verify_token" in names
    assert "create_user" in names
    assert "create_database_connection" in names


def test_real_semantic_retrieval(tmp_path):

    detector = LanguageDetector()

    reader = CodeReader(detector)

    chunker = CodeChunker()

    embedder = CodeEmbedder()

    vector_store = CodeVectorStore(
        collection_name="semantic_test",
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

    assert chunks

    query_embedding = embedder.embed(
        ["where is user authentication handled?"]
    )[0]

    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=3,
    )

    assert results

    names = [
        chunk.name
        for chunk in results
    ]

    assert "authenticate_user" in names
