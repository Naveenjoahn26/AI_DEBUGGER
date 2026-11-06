from pathlib import Path

from repository.retrieval.semantic import SemanticRetriever
from repository.retrieval.lexical import BM25Retriever
from repository.retrieval.hybrid import HybridRetriever

from repository.reader.reader import CodeReader
from repository.language.detector import LanguageDetector
from repository.indexing.chunker import CodeChunker
from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
from repository.ai.context_builder import RepositoryContextBuilder

from repository.intelligence.indexer import RepositoryIndexer
from repository.intelligence.service import (
    RepositoryIntelligenceService,
)
from repository.intelligence.question_engine import (
    CodeQuestionEngine,
)

from repository.llm.groq_provider import GroqProvider

def create_intelligence_service(chunks=None):
    if chunks is None:
        chunks = []
        
    detector = LanguageDetector()
    reader = CodeReader(detector)
    chunker = CodeChunker()
    embedder = CodeEmbedder()
    vector_store = CodeVectorStore()

    indexer = RepositoryIndexer(
        reader=reader,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )
    
    llm = GroqProvider()
    context_builder = RepositoryContextBuilder()

    semantic_searcher = SemanticRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )
    
    bm25_searcher = BM25Retriever(chunks=chunks)
    
    hybrid = HybridRetriever(
        semantic_retriever=semantic_searcher,
        lexical_retriever=bm25_searcher,
    )
    
    question_engine = CodeQuestionEngine(
        retriever=hybrid,
        context_builder=context_builder,
        llm=llm,
    )
    
    return RepositoryIntelligenceService(indexer=indexer,question_engine=question_engine)
    