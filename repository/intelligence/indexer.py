from pathlib import Path

from repository.models.code_chunk import CodeChunk

class RepositoryIndexer:
    def __init__(
        self,
        reader,
        chunker,
        embedder,
        vector_store,
    ):
        self.reader = reader
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
    def index(
        self,
        file_paths: list[Path],
    ) -> list[CodeChunk]:
        all_chunks: list[CodeChunk] = []
        for path in file_paths:
            try:
                document = self.reader.read(path)
            except Exception:
                continue
            chunks = self.chunker.chunk(document)
            if chunks:
                all_chunks.extend(chunks)
        if not all_chunks:
            return []
        embeddings = self.embedder.embed(
            [chunk.content for chunk in all_chunks]
        )
        self.vector_store.add(
            embeddings=embeddings,
            chunks=all_chunks,
        )
        return all_chunks

