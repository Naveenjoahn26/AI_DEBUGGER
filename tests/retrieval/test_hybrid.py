from repository.models.code_chunk import CodeChunk
from repository.retrieval.hybrid import HybridRetriever


def chunk(name: str) -> CodeChunk:
    return CodeChunk(
        content=f"def {name}(): pass",
        file_path="app.py",
        chunk_type="function",
        name=name,
        start_line=1,
        end_line=1,
    )


class FakeSemanticRetriever:

    def search(self, query, top_k):
        return [
            chunk("semantic_one"),
            chunk("shared"),
            chunk("semantic_two"),
        ]


class FakeLexicalRetriever:

    def search(self, query, top_k):
        return [
            chunk("shared"),
            chunk("lexical_one"),
            chunk("semantic_two"),
        ]


def test_hybrid_prefers_results_found_by_both():

    retriever = HybridRetriever(
        semantic_retriever=FakeSemanticRetriever(),
        lexical_retriever=FakeLexicalRetriever(),
    )

    results = retriever.search(
        "authentication",
        top_k=3,
    )

    names = [
        result.name
        for result in results
    ]

    assert names[0] == "shared"


def test_empty_query():

    retriever = HybridRetriever(
        semantic_retriever=FakeSemanticRetriever(),
        lexical_retriever=FakeLexicalRetriever(),
    )

    assert retriever.search("   ") == []
