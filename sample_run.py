from pathlib import Path
import os
from dotenv import load_dotenv

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
from repository.intelligence.service import RepositoryIntelligenceService
from repository.intelligence.question_engine import CodeQuestionEngine
from repository.llm.groq_provider import GroqProvider

# Load API keys
load_dotenv()

def run_sample():
    print("Initializing components...")
    detector = LanguageDetector()
    reader = CodeReader(detector)
    chunker = CodeChunker()
    embedder = CodeEmbedder()
    
    # We will use an in-memory/temp vector store for the sample
    vector_store = CodeVectorStore(collection_name="sample_run_collection")

    indexer = RepositoryIndexer(
        reader=reader,
        chunker=chunker,
        embedder=embedder,
        vector_store=vector_store,
    )
    
    # Target our existing sample_repo fixture
    fixture_repo = Path("tests/fixtures/sample_repo")
    files = list(fixture_repo.glob("*.py"))
    
    print(f"Indexing {len(files)} files from {fixture_repo}...")
    chunks = indexer.index(files)
    print(f"Generated {len(chunks)} chunks.")
    
    print("Setting up Retrievers & LLM...")
    semantic_searcher = SemanticRetriever(
        embedder=embedder,
        vector_store=vector_store,
    )
    
    bm25_searcher = BM25Retriever(chunks=chunks)
    
    hybrid = HybridRetriever(
        semantic_retriever=semantic_searcher,
        lexical_retriever=bm25_searcher,
    )
    
    llm = GroqProvider()
    context_builder = RepositoryContextBuilder()
    
    question_engine = CodeQuestionEngine(
        retriever=hybrid,
        context_builder=context_builder,
        llm=llm,
    )
    
    service = RepositoryIntelligenceService(
        indexer=indexer,
        question_engine=question_engine,
    )
    
    question = "How does user authentication and token creation work in this repository?"
    print(f"\nAsking Question: '{question}'\n")
    print("Generating grounded response via Groq API...\n")
    print("-" * 50)
    
    answer = service.ask(question, top_k=3)
    
    print(answer)
    print("-" * 50)

if __name__ == "__main__":
    run_sample()
