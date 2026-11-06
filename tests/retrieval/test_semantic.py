from repository.models.code_chunk import CodeChunk
from repository.retrieval.semantic import SemanticRetriever

class FakeEmbedder:
    def embed(self, texts):
        return [
            [1.0, 0.0, 0.0]
            for _ in texts
        ]

class FakeVectorStore:
    def __init__(self):
        self.received_embedding = None
        self.received_top_k = None

    def search(self, query_embedding, top_k):
        self.received_embedding = query_embedding
        self.received_top_k = top_k
        return [
            CodeChunk(
                content="def login(): pass",
                file_path="auth.py",
                chunk_type="function",
                name="login",
                start_line=1,
                end_line=1,
            )
        ]

def test_semantic_search():
    embedder = FakeEmbedder()
    vector_store = FakeVectorStore()
    retriever = SemanticRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )
    results = retriever.search(
        "Where is authentication handled?",
        top_k=3,
    )
    assert len(results) == 1
    assert results[0].name == "login"
    assert vector_store.received_embedding == [
        1.0,
        0.0,
        0.0,
    ]
    assert vector_store.received_top_k == 3

def test_empty_query_returns_empty():
    retriever = SemanticRetriever(
        embedder=FakeEmbedder(),
        vector_store=FakeVectorStore(),
    )
    assert retriever.search("   ") == []

def test_invalid_top_k_returns_empty():
    retriever = SemanticRetriever(
        embedder=FakeEmbedder(),
        vector_store=FakeVectorStore(),
    )
    assert retriever.search("authentication", 0) == []
