from repository.models.code_chunk import CodeChunk
from repository.retrieval.lexical import BM25Retriever
from repository.retrieval.semantic import SemanticRetriever


class HybridRetriever:

    def __init__(
        self,
        semantic_retriever: SemanticRetriever,
        lexical_retriever: BM25Retriever,
        rrf_k: int = 60,
    ):
        self.semantic_retriever = semantic_retriever
        self.lexical_retriever = lexical_retriever
        self.rrf_k = rrf_k

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

        candidate_k = max(top_k * 3, 10)

        semantic_results = (
            self.semantic_retriever.search(
                query,
                top_k=candidate_k,
            )
        )

        lexical_results = (
            self.lexical_retriever.search(
                query,
                top_k=candidate_k,
            )
        )

        ranked_chunks = self._rrf(
            semantic_results,
            lexical_results,
        )

        return ranked_chunks[:top_k]

    def _rrf(
        self,
        *result_lists: list[CodeChunk],
    ) -> list[CodeChunk]:

        scores: dict[str, float] = {}
        chunks: dict[str, CodeChunk] = {}

        for results in result_lists:

            for rank, chunk in enumerate(results, start=1):

                chunk_id = self._chunk_id(chunk)

                score = 1 / (
                    self.rrf_k + rank
                )

                scores[chunk_id] = (
                    scores.get(chunk_id, 0.0)
                    + score
                )

                chunks[chunk_id] = chunk

        ranked_ids = sorted(
            scores,
            key=scores.get,
            reverse=True,
        )

        return [
            chunks[chunk_id]
            for chunk_id in ranked_ids
        ]

    def retrieve(self, query: str, top_k: int = 5) -> list[CodeChunk]:
        """Alias for search() — matches the interface expected by SearchCodeTool."""
        return self.search(query, top_k=top_k)

    def _chunk_id(
        self,
        chunk: CodeChunk,
    ) -> str:

        return (
            f"{chunk.file_path}:"
            f"{chunk.start_line}:"
            f"{chunk.end_line}:"
            f"{chunk.chunk_type}:"
            f"{chunk.name or ''}"
        )