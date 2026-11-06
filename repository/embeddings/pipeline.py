from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.formatter import CodeChunkFormatter
from repository.models.code_chunk import CodeChunk

class CodeEmbeddingPipeline:

    def __init__(self,embedder:CodeEmbedder,formatter:CodeChunkFormatter,):
        self.embedder = embedder
        self.formatter = formatter

    def embed_chunks(
        self,chunks:list[CodeChunk],
        )-> list[list[float]]:
            if not chunks:
                return []
            texts = [self.formatter.format(chunk)
            for chunk in chunks]
            return self.embedder.embed(texts)
