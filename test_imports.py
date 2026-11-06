import traceback

def test_all():
    print("Testing imports...")
    try:
        from repository.ai.context_builder import CodeContextBuilder
        from repository.ai.retriever import CodeRetriever
        from repository.ai.debugger import RepositoryDebugger
        from repository.embeddings.embedder import CodeEmbedder
        from repository.embeddings.vector_store import CodeVectorStore
        from repository.models.code_chunk import CodeChunk
        
        print("All imports successful!")
        
        print("Testing instantiation...")
        embedder = CodeEmbedder()
        vector_store = CodeVectorStore()
        retriever = CodeRetriever(embedder, vector_store)
        context_builder = CodeContextBuilder()
        debugger = RepositoryDebugger(retriever, context_builder)
        
        print("All classes instantiated successfully!")
        
    except ImportError as e:
        print(f"ImportError: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    test_all()
