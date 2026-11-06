from repository.embeddings.embedder import CodeEmbedder
from repository.models.code_chunk import CodeChunk
from repository.embeddings.vector_store import CodeVectorStore

class SemanticRetriever:
    def __init__(self,embedder:CodeEmbedder,vector_store:CodeVectorStore,):
        self.embedder = embedder
        self.vector_store = vector_store

    def search(
    self,
    query: str,
    top_k: int = 5,
) -> list[CodeChunk]:

        if not query.strip():
            return []

        if top_k <= 0:
            return []

        top_k = min(top_k, 50)

        query_embedding = self.embedder.embed([query])[0]

        return self.vector_store.search(
        query_embedding=query_embedding,
        top_k=top_k,
        )


