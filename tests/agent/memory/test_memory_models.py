from repository.agent.memory.models import Memory
from repository.agent.memory.store import MemoryStore

def test_memory_model_initialization():
    mem = Memory(
        key="auth_issue",
        content="JWT expiration validation is failing in auth/service.py",
        metadata={"source": "agent_investigation"}
    )
    assert mem.key == "auth_issue"
    assert "JWT" in mem.content
    assert mem.metadata["source"] == "agent_investigation"

def test_memory_store_save_and_get():
    store = MemoryStore()
    mem = Memory(key="db", content="FastAPI uses SQLite.")
    
    # Save memory
    store.save(mem)
    
    # Retrieve memory
    retrieved = store.get("db")
    assert retrieved is not None
    assert retrieved.content == "FastAPI uses SQLite."

def test_memory_store_get_nonexistent():
    store = MemoryStore()
    assert store.get("unknown") is None

def test_memory_store_update_existing():
    store = MemoryStore()
    mem1 = Memory(key="db", content="Uses SQLite.")
    mem2 = Memory(key="db", content="Uses PostgreSQL now.")
    
    store.save(mem1)
    store.save(mem2)
    
    assert store.get("db").content == "Uses PostgreSQL now."

def test_memory_store_delete():
    store = MemoryStore()
    mem = Memory(key="temp", content="Delete me")
    store.save(mem)
    
    assert store.get("temp") is not None
    store.delete("temp")
    assert store.get("temp") is None
    
    # Deleting nonexistent key shouldn't raise error
    store.delete("temp")


def setup_test_store() -> MemoryStore:
    store = MemoryStore()
    store.save(Memory(
        key="authentication", 
        content="JWT authentication is handled in auth/service.py"
    ))
    store.save(Memory(
        key="database", 
        content="PostgreSQL is used for persistence"
    ))
    store.save(Memory(
        key="frontend", 
        content="React communicates with FastAPI through REST APIs"
    ))
    return store


def test_search_relevant_memory():
    # 1. Relevant memory
    store = setup_test_store()
    results = store.search("JWT authentication")
    
    assert len(results) >= 1
    assert results[0].key == "authentication"


def test_search_irrelevant_memory():
    # 2. Irrelevant query
    store = setup_test_store()
    results = store.search("payment gateway")
    
    assert len(results) == 0


def test_search_multiple_matches():
    # 3. Multiple matches
    store = setup_test_store()
    # "authentication API" should match "authentication" and "frontend" (which has "APIs")
    results = store.search("authentication API")
    
    assert len(results) >= 2
    keys = [r.key for r in results]
    assert "authentication" in keys
    assert "frontend" in keys


def test_search_limit():
    # 4. Limit
    store = setup_test_store()
    # "is" matches all three memories ("is handled", "is used")
    # Actually, a better common word is "is" or "with" or "e". Let's search "e".
    results = store.search("e", limit=2)
    assert len(results) == 2


def test_search_empty_query():
    # 5. Empty query
    store = setup_test_store()
    
    assert store.search("") == []
    assert store.search("   ") == []
