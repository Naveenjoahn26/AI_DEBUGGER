from pathlib import Path

from repository.intelligence.indexer import RepositoryIndexer
from repository.models.code_chunk import CodeChunk


class FakeReader:

    def read(self, path):

        return type(
            "Document",
            (),
            {
                "content": "def hello():\n    return True",
            },
        )()


class FakeChunker:

    def chunk(self, document):

        return [
            CodeChunk(
                content="def hello():\n    return True",
                file_path="hello.py",
                chunk_type="function",
                name="hello",
                start_line=1,
                end_line=2,
            )
        ]


class FakeEmbedder:

    def embed(self, texts):

        return [
            [1.0, 0.0, 0.0]
            for _ in texts
        ]


class FakeVectorStore:

    def __init__(self):

        self.embeddings = None
        self.chunks = None

    def add(self, embeddings, chunks):

        self.embeddings = embeddings
        self.chunks = chunks


def test_index_repository():

    vector_store = FakeVectorStore()

    indexer = RepositoryIndexer(
        reader=FakeReader(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        vector_store=vector_store,
    )

    chunks = indexer.index(
        [Path("hello.py")]
    )

    assert len(chunks) == 1
    assert chunks[0].name == "hello"

    assert vector_store.embeddings == [
        [1.0, 0.0, 0.0]
    ]

    assert vector_store.chunks == chunks


def test_empty_repository():

    vector_store = FakeVectorStore()

    indexer = RepositoryIndexer(
        reader=FakeReader(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        vector_store=vector_store,
    )

    chunks = indexer.index([])

    assert chunks == []
    assert vector_store.embeddings is None
