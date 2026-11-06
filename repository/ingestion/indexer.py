"""
repository/ingestion/indexer.py

Orchestrates the repository indexing pipeline:

    local repo path
        ↓
    RepositoryScanner  (discover files)
        ↓
    CodeReader         (read source text)
        ↓
    CodeChunker        (AST-based chunking)
        ↓
    CodeEmbeddingPipeline  (embed chunks)
        ↓
    CodeVectorStore    (upsert into ChromaDB)
        ↓
    IndexingSummary

No existing component is modified; this file only orchestrates them.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from repository.embeddings.formatter import CodeChunkFormatter
from repository.embeddings.pipeline import CodeEmbeddingPipeline
from repository.embeddings.vector_store import CodeVectorStore
from repository.embeddings.embedder import CodeEmbedder
from repository.indexing.chunker import CodeChunker
from repository.language.detector import LanguageDetector
from repository.models.code_chunk import CodeChunk
from repository.reader.reader import CodeReader

logger = logging.getLogger(__name__)


@dataclass
class IndexingSummary:
    """Returned after a repository has been indexed."""

    files_scanned: int = 0
    files_processed: int = 0
    chunks_created: int = 0
    chunks_indexed: int = 0
    collection_name: str = ""
    errors: list[str] = field(default_factory=list)
    # All indexed CodeChunk objects — exposed so callers (e.g., BM25Retriever)
    # can reuse the chunk list without re-scanning the repo.
    _chunks: list = field(default_factory=list)


class IndexingPipeline:
    """
    Connects the existing scanner/reader/chunker/embedder/vector-store
    components into a single indexing pass for a cloned repository.

    Usage:
        pipeline = IndexingPipeline(embedder, vector_store)
        summary = pipeline.run(repo_path)
    """

    def __init__(
        self,
        embedder: CodeEmbedder,
        vector_store: CodeVectorStore,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store

        self._language_detector = LanguageDetector()
        self._reader = CodeReader(self._language_detector)
        self._chunker = CodeChunker()
        self._embedding_pipeline = CodeEmbeddingPipeline(
            embedder=self.embedder,
            formatter=CodeChunkFormatter(),
        )

    def run(self, repo_path: Path) -> IndexingSummary:
        """
        Index all Python files found under *repo_path*.

        Returns an IndexingSummary with counts and the collection name.
        Unsupported or problematic files are skipped with a warning; they
        do not raise an exception.
        """
        summary = IndexingSummary(
            collection_name=self.vector_store.collection.name,
        )

        # 1. Discover Python files (scanner excluded for simplicity —
        #    we walk the path directly to stay within the existing
        #    RepositoryScanner limitations; the scanner uses bare imports
        #    that don't work as a package without sys.path manipulation).
        py_files = [
            p for p in repo_path.rglob("*.py")
            if not any(
                part in {".git", "__pycache__", ".venv", "node_modules"}
                for part in p.parts
            )
        ]

        summary.files_scanned = len(py_files)
        logger.info(
            "indexing_start: Found Python files",
            extra={"count": summary.files_scanned, "repo": str(repo_path)},
        )

        # 2. Read → chunk each file individually so one bad file doesn't
        #    abort the whole indexing run.
        all_chunks: list[CodeChunk] = []

        for py_file in py_files:
            try:
                document = self._reader.read(py_file)
            except Exception as exc:
                msg = f"read_error: {py_file.name}: {exc}"
                logger.warning(msg)
                summary.errors.append(msg)
                continue

            try:
                chunks = self._chunker.chunk(document)
            except Exception as exc:
                msg = f"chunk_error: {py_file.name}: {exc}"
                logger.warning(msg)
                summary.errors.append(msg)
                continue

            summary.files_processed += 1
            all_chunks.extend(chunks)

        summary.chunks_created = len(all_chunks)
        logger.info(
            "indexing_chunks: Chunks extracted",
            extra={"total": summary.chunks_created},
        )

        if not all_chunks:
            logger.info("indexing_skip: No chunks to embed — repository may be empty or unsupported.")
            return summary

        # 3. Embed + store.
        try:
            embeddings = self._embedding_pipeline.embed_chunks(all_chunks)
            self.vector_store.add(embeddings=embeddings, chunks=all_chunks)
            summary.chunks_indexed = len(all_chunks)
        except Exception as exc:
            msg = f"embed_store_error: {exc}"
            logger.error(msg)
            summary.errors.append(msg)

        logger.info(
            "indexing_complete: Indexed repository",
            extra={
                "files_scanned": summary.files_scanned,
                "files_processed": summary.files_processed,
                "chunks_indexed": summary.chunks_indexed,
            },
        )

        # Expose chunk list for BM25Retriever in DebugService (Fix 1)
        summary._chunks = all_chunks

        return summary
