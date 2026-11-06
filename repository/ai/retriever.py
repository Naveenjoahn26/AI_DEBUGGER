from repository.embeddings.embedder import CodeEmbedder
from repository.models.code_chunk import CodeChunk
from repository.embeddings.vector_store import CodeVectorStore


class CodeRetriever:

    def __init__(
        self,
        embedder: CodeEmbedder,
        vector_store: CodeVectorStore,
    ):
        self.embedder = embedder
        self.vector_store = vector_store

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[CodeChunk]:
        # FIX 4: guard empty / whitespace queries
        if not question or not question.strip():
            return []

        query_embedding = self.embedder.embed(
            [question]
        )[0]

        return self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
        )