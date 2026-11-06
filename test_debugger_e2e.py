import traceback
import uuid
from repository.embeddings.embedder import CodeEmbedder
from repository.embeddings.vector_store import CodeVectorStore
from repository.models.code_chunk import CodeChunk
from repository.ai.retriever import CodeRetriever
from repository.ai.context_builder import RepositoryContextBuilder
from repository.ai.debugger import RepositoryDebugger

def test_debugger():
    print("Setting up end-to-end test environment...")
    
    try:
        # 1. Setup Embedder and Vector Store with a unique test collection
        embedder = CodeEmbedder()
        collection_name = f"test_collection_{uuid.uuid4().hex}"
        vector_store = CodeVectorStore(collection_name=collection_name)
        
        # 2. Define realistic code snippets
        code_snippets = [
            """def authenticate_user(username, password):
    user = db.get_user(username)
    if user and verify_password(password, user.password_hash):
        return generate_token(user)
    return None""",
            """class DatabaseConnection:
    def __init__(self, uri):
        self.uri = uri
        self.connected = False
    
    def connect(self):
        self.connection = create_connection(self.uri)
        self.connected = True""",
            """def calculate_total(items, discount=0):
    total = sum(item.price for item in items)
    return total * (1 - discount)"""
        ]
        
        # 3. Create Chunk objects
        chunks = [
            CodeChunk(
                content=code_snippets[0], 
                file_path="src/auth.py", 
                chunk_type="function", 
                name="authenticate_user", 
                start_line=10, 
                end_line=14
            ),
            CodeChunk(
                content=code_snippets[1], 
                file_path="src/db.py", 
                chunk_type="class", 
                name="DatabaseConnection", 
                start_line=5, 
                end_line=12
            ),
            CodeChunk(
                content=code_snippets[2], 
                file_path="src/billing.py", 
                chunk_type="function", 
                name="calculate_total", 
                start_line=20, 
                end_line=22
            )
        ]
        
        print("Embedding and storing chunks in ChromaDB...")
        embeddings = embedder.embed([chunk.content for chunk in chunks])
        vector_store.add(embeddings=embeddings, chunks=chunks)
        
        # 4. Setup AI Components
        retriever = CodeRetriever(embedder, vector_store)
        context_builder = RepositoryContextBuilder()
        debugger = RepositoryDebugger(retriever, context_builder)
        
        # 5. Execute Test Cases
        print("\n" + "="*50)
        print("TEST CASE 1: Querying about authentication (top_k=1)")
        print("="*50)
        question1 = "How does user authentication work?"
        print(f"Question: {question1}")
        context1 = debugger.build_context(question1, top_k=1)
        print("--- Generated Context ---")
        print(context1)
        
        print("\n" + "="*50)
        print("TEST CASE 2: Querying about billing totals (top_k=2)")
        print("="*50)
        question2 = "Where is the logic for calculating billing totals with discounts?"
        print(f"Question: {question2}")
        context2 = debugger.build_context(question2, top_k=2)
        print("--- Generated Context ---")
        print(context2)

        print("\n✅ All End-to-End tests passed successfully!")
        
    except Exception as e:
        print("\n❌ Test failed with error:")
        traceback.print_exc()

if __name__ == '__main__':
    test_debugger()
