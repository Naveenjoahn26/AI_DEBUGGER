import chromadb

from repository.models.code_chunk import CodeChunk


class CodeVectorStore:

    def __init__(
        self,
        collection_name: str = "repository_code",
        persist_directory: str = "./chroma_db",
    ):
        self.client = chromadb.PersistentClient(
            path=str(persist_directory)
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def clear(self) -> None:
        """
        FIX A: Delete and recreate the collection so stale chunks
        from previous runs never pollute a fresh debug session.
        """
        name = self.collection.name
        self.client.delete_collection(name)
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def _chunk_id(self, chunk: CodeChunk) -> str:
        return f"{chunk.file_path}:{chunk.start_line}:{chunk.end_line}"

    def add(
        self,
        embeddings: list[list[float]],
        chunks: list[CodeChunk],
    ) -> None:

        if not chunks:
            return

        if len(embeddings) != len(chunks):
            raise ValueError(f"Embeddings length ({len(embeddings)}) must match chunks length ({len(chunks)})")

        ids = [
            self._chunk_id(chunk)
            for chunk in chunks
        ]

        documents = [
            chunk.content
            for chunk in chunks
        ]

        metadatas = [
            {
                "file_path": chunk.file_path,
                "chunk_type": chunk.chunk_type,
                "name": chunk.name or "",
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[CodeChunk]:
        # FIX 5: guard against empty collection crash
        count = self.collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        if actual_k <= 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
        )

        chunks = []

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        for document, metadata in zip(
            documents,
            metadatas,
        ):
            chunks.append(
                CodeChunk(
                    content=document,
                    file_path=metadata["file_path"],
                    chunk_type=metadata["chunk_type"],
                    name=metadata["name"] or None,
                    start_line=int(metadata["start_line"]),
                    end_line=int(metadata["end_line"]),
                )
            )

        return chunks