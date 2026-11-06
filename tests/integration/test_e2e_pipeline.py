from pathlib import Path

from repository.reader.reader import CodeReader
from repository.language.detector import LanguageDetector
from repository.indexing.chunker import CodeChunker
from repository.embeddings.vector_store import CodeVectorStore
from repository.ai.context_builder import RepositoryContextBuilder
from repository.retrieval.semantic import SemanticRetriever
from repository.retrieval.lexical import BM25Retriever
from repository.retrieval.hybrid import HybridRetriever
from repository.intelligence.indexer import RepositoryIndexer
from repository.intelligence.question_engine import CodeQuestionEngine
from repository.intelligence.service import RepositoryIntelligenceService
from repository.llm.provider import LLMProvider


class FakeEmbedder:
    def embed(self, texts):
        # We need an embedding of length 384 for sentence-transformers fallback?
        # Actually our VectorStore doesn't enforce a dimension size unless the collection already exists.
        return [[0.1] * 384 for _ in texts]


class FakeLLM(LLMProvider):
    def __init__(self):
        self.received_prompt = None

    def generate(self, prompt: str) -> str:
        self.received_prompt = prompt
        return "Fake grounded answer"


def test_complete_qa_workflow(tmp_path):

    detector = LanguageDetector()
    reader = CodeReader(detector)
    chunker = CodeChunker()
    embedder = FakeEmbedder()
    
    vector_store = CodeVectorStore(
        collection_name="e2e_test",
        persist_directory=str(tmp_path / "chroma_e2e")
    )

    indexer = RepositoryIndexer(
        reader=reader,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )

    test_file = tmp_path / "auth.py"
    test_file.write_text("def authenticate():\n    return True\n")

    chunks = indexer.index([test_file])
    
    assert len(chunks) > 0

    semantic = SemanticRetriever(embedder, vector_store)
    lexical = BM25Retriever(chunks)
    hybrid = HybridRetriever(
        semantic_retriever=semantic,
        lexical_retriever=lexical,
    )

    context_builder = RepositoryContextBuilder()
    llm = FakeLLM()

    engine = CodeQuestionEngine(
        retriever=hybrid,
        context_builder=context_builder,
        llm=llm,
    )

    service = RepositoryIntelligenceService(
        indexer=indexer,
        question_engine=engine,
    )

    answer = service.ask("Where is authentication?", top_k=5)

    assert answer == "Fake grounded answer"
    assert "def authenticate():" in llm.received_prompt
    assert "auth.py" in llm.received_prompt
    assert "Where is authentication?" in llm.received_prompt
