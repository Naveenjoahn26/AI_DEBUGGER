import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from repository.language.detector import LanguageDetector
from repository.reader.reader import CodeReader
from repository.indexing.chunker import CodeChunker
from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
import numpy as np

def main():
    root = Path(__file__).parent
    
    detector = LanguageDetector()
    reader = CodeReader(detector)
    chunker = CodeChunker()
    
    # Load all python files from repository
    paths = list(root.joinpath('repository').rglob('*.py'))
    docs = reader.read_many(paths)
    
    print(f"Read {len(docs)} documents.")
    
    all_chunks = []
    for doc in docs:
        if doc.language.value != 'python':
            continue
        chunks = chunker.chunk(doc)
        all_chunks.extend(chunks)
        
    print(f"Extracted {len(all_chunks)} chunks.")
    
    if not all_chunks:
        print("No chunks found.")
        return

    print("Loading embedder...")
    embedder = CodeEmbedder()
    
    texts = [chunk.content for chunk in all_chunks]
    
    print("Embedding chunks...")
    embeddings = embedder.embed(texts)
    
    dimension = embeddings.shape[1]
    store = CodeVectorStore(dimension)
    
    print(f"Adding to vector store (dimension: {dimension})...")
    store.add(embeddings, all_chunks)
    
    queries = [
        "How to detect the language of a file?",
        "Extracting AST symbols like classes and functions",
        "Finding cycles in dependency graph"
    ]
    
    print("\n--- Testing Semantic Search ---")
    for query in queries:
        print(f"\nQuery: '{query}'")
        query_emb = embedder.embed([query])
        results = store.search(query_emb, top_k=2)
        for i, res in enumerate(results):
            print(f"  Result {i+1}: [{res.chunk_type}] {res.name} (File: {Path(res.file_path).name}, Lines: {res.start_line}-{res.end_line})")

if __name__ == "__main__":
    main()
