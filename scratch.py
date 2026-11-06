from repository.indexing.chunker import CodeChunker
from test_chunker import make_document

doc = make_document(
'''import os
from fastapi import FastAPI
from app.database import get_db

@router.post('/users')
def create_user():
    """Create a new user."""
    return get_db()
'''
)

chunk = CodeChunker().chunk(doc)[0]
print(chunk.to_llm_format())
