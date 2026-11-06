import traceback
from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
from repository.models.code_chunk import CodeChunk

def run_tests():
    print("--- Testing CodeEmbedder ---")
    try:
        embedder = CodeEmbedder()
        texts = [
            "def add(a, b): return a + b",
            "def sub(a, b): return a - b",
        ]
        embeddings = embedder.embed(texts)
        print(f"Embeddings type: {type(embeddings)}")
        print(f"Embeddings len: {len(embeddings)}")
        print(f"First embedding len: {len(embeddings[0]) if embeddings else 0}")
    except Exception as e:
        print("Error in CodeEmbedder:")
        traceback.print_exc()
        return

    print("\n--- Testing CodeVectorStore (ChromaDB) ---")
    try:
        store = CodeVectorStore()
        chunks = [
            CodeChunk(content=texts[0], file_path="f1.py", chunk_type="function", name="add", start_line=1, end_line=1),
            CodeChunk(content=texts[1], file_path="f2.py", chunk_type="function", name="sub", start_line=1, end_line=1)
        ]
        
        print("\nTest 1: Adding raw output from embedder (list[list[float]])")
        try:
            store.add(embeddings, chunks)
            print("Success!")
        except Exception as e:
            print(f"Failed! Error: {type(e).__name__}: {e}")
            
        print("\nTest 2: Searching with raw output from embedder (list[float])")
        q_emb = embedder.embed(["addition"])
        try:
            # Note: embed returns list[list[float]], so we pass q_emb[0] to search
            res = store.search(q_emb[0], top_k=1)
            print(f"Success! Top result: {res[0].name}")
        except Exception as e:
            print(f"Failed! Error: {type(e).__name__}: {e}")
            
    except Exception as e:
        print("Error in CodeVectorStore:")
        traceback.print_exc()

if __name__ == '__main__':
    run_tests()
