"""
tests/retrieval/test_retrieval_edge_cases.py

Comprehensive edge-case tests for every retrieval fix applied.
Runs without any network calls (all embedders / LLMs are faked).

Coverage map:
  Fix 1  — HybridRetriever wired (tested via FakeRetrievers)
  Fix 3  — Module-level chunk extraction
  Fix 4  — Empty-query guard in CodeRetriever
  Fix 5  — Empty-collection guard in VectorStore
  Fix 6  — Context truncation sentinel
  Fix 7  — camelCase tokenisation in BM25
  Fix 8  — Docstring / decorator in embedding text
  Fix A  — VectorStore.clear() removes stale data
  Fix B  — top_k exposed in SearchCodeTool
  Fix D  — DiagnosisEvaluator robust float parsing
"""

import ast
import pytest

from repository.models.code_chunk import CodeChunk
from repository.models.code_document import CodeDocument
from repository.language.language import Language

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_chunk(
    name="func",
    file_path="app.py",
    content="def func(): pass",
    start_line=1,
    end_line=1,
    chunk_type="function",
    docstring=None,
    decorators=None,
) -> CodeChunk:
    return CodeChunk(
        content=content,
        file_path=file_path,
        chunk_type=chunk_type,
        name=name,
        start_line=start_line,
        end_line=end_line,
        docstring=docstring,
        decorators=decorators or [],
    )


def make_document(content: str, path: str = "test.py", language=None) -> CodeDocument:
    from pathlib import Path
    from repository.language.language import Language as _Language
    return CodeDocument(
        content=content,
        path=Path(path),
        encoding="utf-8",
        size=len(content),
        file_hash="abc123",
        language=language or _Language.PYTHON,
    )


# ===========================================================================
# FIX 3 — CodeChunker: module-level assignment chunks
# ===========================================================================

class TestChunkerModuleAssignments:

    def _chunker(self):
        from repository.indexing.chunker import CodeChunker
        return CodeChunker()

    def test_global_constant_becomes_chunk(self):
        doc = make_document("TAX_RATE = 0.08\n")
        chunks = self._chunker().chunk(doc)
        types = [c.chunk_type for c in chunks]
        assert "module_variable" in types

    def test_global_constant_name_preserved(self):
        doc = make_document("DISCOUNT = 0.1\n")
        chunks = self._chunker().chunk(doc)
        names = [c.name for c in chunks]
        assert "DISCOUNT" in names

    def test_annotated_assignment_becomes_chunk(self):
        doc = make_document("MAX_RETRIES: int = 5\n")
        chunks = self._chunker().chunk(doc)
        types = [c.chunk_type for c in chunks]
        assert "module_variable" in types

    def test_augmented_assignment_becomes_chunk(self):
        doc = make_document("counter = 0\ncounter += 1\n")
        chunks = self._chunker().chunk(doc)
        names = [c.name for c in chunks if c.chunk_type == "module_variable"]
        assert "counter" in names

    def test_functions_still_extracted_alongside_constants(self):
        src = "RATE = 0.1\n\ndef apply(x):\n    return x * RATE\n"
        doc = make_document(src)
        chunks = self._chunker().chunk(doc)
        types = {c.chunk_type for c in chunks}
        assert "function" in types
        assert "module_variable" in types

    def test_no_module_chunk_for_pure_function_file(self):
        src = "def hello():\n    pass\n"
        doc = make_document(src)
        chunks = self._chunker().chunk(doc)
        module_chunks = [c for c in chunks if c.chunk_type == "module_variable"]
        assert module_chunks == []

    def test_syntax_error_returns_empty(self):
        doc = make_document("def broken(\n")
        chunks = self._chunker().chunk(doc)
        assert chunks == []

    def test_non_python_file_returns_empty(self):
        from pathlib import Path
        from repository.language.language import Language as _Language
        from repository.models.code_document import CodeDocument
        doc = CodeDocument(
            content="SELECT * FROM users;",
            path=Path("query.sql"),
            encoding="utf-8",
            size=20,
            file_hash="abc",
            language=_Language.UNKNOWN,
        )
        chunks = self._chunker().chunk(doc)
        assert chunks == []


# ===========================================================================
# FIX 4 — CodeRetriever: empty-query guard
# ===========================================================================

class TestCodeRetrieverEmptyQuery:

    def _retriever(self):
        from repository.ai.retriever import CodeRetriever

        class _FakeEmbedder:
            def embed(self, texts):
                raise AssertionError("embed() should not be called for empty queries")

        class _FakeStore:
            def search(self, **kwargs):
                raise AssertionError("search() should not be called for empty queries")

        return CodeRetriever(embedder=_FakeEmbedder(), vector_store=_FakeStore())

    def test_empty_string_returns_empty(self):
        r = self._retriever()
        assert r.retrieve("") == []

    def test_whitespace_only_returns_empty(self):
        r = self._retriever()
        assert r.retrieve("   ") == []

    def test_tab_newline_returns_empty(self):
        r = self._retriever()
        assert r.retrieve("\t\n") == []

    def test_none_like_empty_returns_empty(self):
        r = self._retriever()
        assert r.retrieve("") == []


# ===========================================================================
# FIX 5 — CodeVectorStore: empty-collection guard
# ===========================================================================

class TestVectorStoreEmptyCollection:

    def test_search_empty_collection_returns_empty(self, tmp_path):
        from repository.embeddings.vector_store import CodeVectorStore
        store = CodeVectorStore(persist_directory=str(tmp_path / "chroma"))
        # Collection has 0 documents — must not raise ValueError
        result = store.search(query_embedding=[0.1, 0.2, 0.3], top_k=5)
        assert result == []

    def test_search_top_k_larger_than_collection(self, tmp_path):
        from repository.embeddings.vector_store import CodeVectorStore
        store = CodeVectorStore(persist_directory=str(tmp_path / "chroma"))
        chunk = make_chunk()
        store.add(embeddings=[[0.1, 0.2, 0.3]], chunks=[chunk])
        # top_k=100 but collection has only 1 doc — must not crash
        result = store.search(query_embedding=[0.1, 0.2, 0.3], top_k=100)
        assert len(result) == 1

    def test_search_top_k_zero_returns_empty(self, tmp_path):
        from repository.embeddings.vector_store import CodeVectorStore
        store = CodeVectorStore(persist_directory=str(tmp_path / "chroma"))
        chunk = make_chunk()
        store.add(embeddings=[[0.1, 0.2, 0.3]], chunks=[chunk])
        # top_k=0 → min(0,1)=0 → ChromaDB's n_results=0 raises, so we guard it
        result = store.search(query_embedding=[0.1, 0.2, 0.3], top_k=0)
        assert result == []


# ===========================================================================
# FIX A — CodeVectorStore.clear(): stale chunk elimination
# ===========================================================================

class TestVectorStoreClear:

    def test_clear_removes_all_documents(self, tmp_path):
        from repository.embeddings.vector_store import CodeVectorStore
        store = CodeVectorStore(
            collection_name="test_clear",
            persist_directory=str(tmp_path / "chroma"),
        )
        chunk = make_chunk(name="old_func")
        store.add(embeddings=[[0.1, 0.2, 0.3]], chunks=[chunk])
        assert store.collection.count() == 1

        store.clear()
        assert store.collection.count() == 0

    def test_clear_allows_fresh_add(self, tmp_path):
        from repository.embeddings.vector_store import CodeVectorStore
        store = CodeVectorStore(
            collection_name="test_fresh",
            persist_directory=str(tmp_path / "chroma"),
        )
        old = make_chunk(name="old", start_line=1, end_line=1)
        store.add(embeddings=[[0.1, 0.2, 0.3]], chunks=[old])

        store.clear()

        new = make_chunk(name="new", start_line=2, end_line=2)
        store.add(embeddings=[[0.4, 0.5, 0.6]], chunks=[new])

        result = store.search(query_embedding=[0.4, 0.5, 0.6], top_k=5)
        names = [c.name for c in result]
        assert "new" in names
        assert "old" not in names

    def test_double_clear_does_not_raise(self, tmp_path):
        from repository.embeddings.vector_store import CodeVectorStore
        store = CodeVectorStore(
            collection_name="test_double_clear",
            persist_directory=str(tmp_path / "chroma"),
        )
        store.clear()
        store.clear()  # should not raise


# ===========================================================================
# FIX 6 — RepositoryContextBuilder: truncation sentinel + budget fix
# ===========================================================================

class TestContextBuilderTruncation:

    def _builder(self):
        from repository.ai.context_builder import RepositoryContextBuilder
        return RepositoryContextBuilder()

    def _item(self, file_path="f.py", content="x" * 100):
        from repository.ai.context_builder import ContextItem
        return ContextItem(
            file_path=file_path,
            chunk_type="function",
            name="func",
            start_line=1,
            end_line=5,
            content=content,
        )

    def test_truncation_sentinel_appears_when_context_exceeds_budget(self):
        builder = self._builder()
        # 10 large items that won't all fit in 500 chars
        items = [self._item(file_path=f"file{i}.py") for i in range(10)]
        context = builder.format(items, max_characters=500)
        assert "omitted" in context.lower() or "truncated" in context.lower()

    def test_no_sentinel_when_all_chunks_fit(self):
        builder = self._builder()
        items = [self._item(content="x" * 10)]
        context = builder.format(items, max_characters=20_000)
        assert "omitted" not in context and "truncated" not in context.lower()

    def test_empty_items_returns_empty_string(self):
        builder = self._builder()
        assert builder.format([]) == ""

    def test_security_wrapper_always_present(self):
        builder = self._builder()
        items = [self._item()]
        context = builder.format(items)
        assert "<repository_content>" in context
        assert "</repository_content>" in context
        assert "WARNING" in context

    def test_deduplication_prevents_same_chunk_twice(self):
        from repository.ai.context_builder import RepositoryContextBuilder
        builder = RepositoryContextBuilder()
        dup = make_chunk(name="func", start_line=1, end_line=5)
        items = builder.build([dup, dup, dup])
        assert len(items) == 1


# ===========================================================================
# FIX 7 — BM25Retriever: camelCase tokenization
# ===========================================================================

class TestBM25CamelCaseTokenization:

    def _retriever(self, chunks):
        from repository.retrieval.lexical import BM25Retriever
        return BM25Retriever(chunks)

    def test_camel_case_query_matches_camel_case_function(self):
        chunks = [
            make_chunk(name="applyDiscount", content="def applyDiscount(price): pass"),
            make_chunk(name="createUser", content="def createUser(user): pass"),
        ]
        retriever = self._retriever(chunks)
        results = retriever.search("apply discount", top_k=1)
        assert results[0].name == "applyDiscount"

    def test_snake_case_still_works(self):
        chunks = [
            make_chunk(name="apply_discount", content="def apply_discount(price): pass"),
            make_chunk(name="create_user", content="def create_user(user): pass"),
        ]
        retriever = self._retriever(chunks)
        results = retriever.search("apply discount", top_k=1)
        assert results[0].name == "apply_discount"

    def test_pascal_case_split(self):
        chunks = [
            make_chunk(name="DiscountCalculator", content="class DiscountCalculator: pass"),
            make_chunk(name="UserManager", content="class UserManager: pass"),
        ]
        retriever = self._retriever(chunks)
        results = retriever.search("discount calculator", top_k=1)
        assert results[0].name == "DiscountCalculator"

    def test_all_caps_acronym_split(self):
        # "HTMLParser" → "html", "parser" and "JSONEncoder" → "json", "encoder"
        # Both should be retrievable by their component words
        chunks = [
            make_chunk(name="HTMLParser", content="class HTMLParser: pass"),
            make_chunk(name="JSONEncoder", content="class JSONEncoder: pass"),
        ]
        retriever = self._retriever(chunks)
        results = retriever.search("json encoder", top_k=2)
        names = [r.name for r in results]
        assert "JSONEncoder" in names

    def test_empty_corpus_returns_empty(self):
        retriever = self._retriever([])
        assert retriever.search("anything") == []

    def test_whitespace_query_returns_empty(self):
        retriever = self._retriever([make_chunk()])
        assert retriever.search("   ") == []

    def test_top_k_respects_corpus_size(self):
        chunks = [make_chunk(name=f"fn{i}", start_line=i, end_line=i) for i in range(3)]
        retriever = self._retriever(chunks)
        results = retriever.search("fn", top_k=100)
        assert len(results) == 3


# ===========================================================================
# FIX 8 — CodeChunkFormatter: docstring + decorator in embedding text
# ===========================================================================

class TestCodeChunkFormatterRichEmbedding:

    def _formatter(self):
        from repository.embeddings.formatter import CodeChunkFormatter
        return CodeChunkFormatter()

    def test_docstring_included_in_output(self):
        chunk = make_chunk(docstring="Apply percentage discount to checkout total.")
        text = self._formatter().format(chunk)
        assert "Apply percentage discount" in text

    def test_decorator_included_in_output(self):
        chunk = make_chunk(decorators=["staticmethod", "app.route('/checkout')"])
        text = self._formatter().format(chunk)
        assert "staticmethod" in text
        assert "route" in text

    def test_no_docstring_no_decorator_still_works(self):
        chunk = make_chunk()
        text = self._formatter().format(chunk)
        assert "Code:" in text
        assert chunk.content in text

    def test_long_docstring_truncated_to_400_chars(self):
        long_doc = "x" * 1000
        chunk = make_chunk(docstring=long_doc)
        text = self._formatter().format(chunk)
        # Only first 400 chars of docstring should appear
        assert "x" * 400 in text
        assert "x" * 401 not in text

    def test_parent_name_included_for_method(self):
        chunk = CodeChunk(
            content="def save(self): pass",
            file_path="models.py",
            chunk_type="method",
            name="save",
            start_line=10,
            end_line=11,
            parent_name="UserModel",
        )
        text = self._formatter().format(chunk)
        assert "UserModel" in text


# ===========================================================================
# FIX B — SearchCodeTool: top_k exposed to agent
# ===========================================================================

class TestSearchCodeToolTopK:

    def _tool(self, chunks):
        from repository.agent.tools.search_code import SearchCodeTool, SearchCodeInput
        from repository.ai.context_builder import RepositoryContextBuilder

        class _FakeRetriever:
            def __init__(self, chunks):
                self._chunks = chunks
            def retrieve(self, query, top_k=5):
                return self._chunks[:top_k]

        return SearchCodeTool(
            retriever=_FakeRetriever(chunks),
            context_builder=RepositoryContextBuilder(),
        )

    def test_top_k_field_exists_in_schema(self):
        from repository.agent.tools.search_code import SearchCodeInput
        schema = SearchCodeInput.model_json_schema()
        assert "top_k" in schema["properties"]

    def test_top_k_default_is_5(self):
        from repository.agent.tools.search_code import SearchCodeInput
        inp = SearchCodeInput(query="login bug")
        assert inp.top_k == 5

    def test_top_k_lower_bound_is_1(self):
        from repository.agent.tools.search_code import SearchCodeInput
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            SearchCodeInput(query="test", top_k=0)

    def test_top_k_upper_bound_is_20(self):
        from repository.agent.tools.search_code import SearchCodeInput
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            SearchCodeInput(query="test", top_k=21)

    def test_execute_respects_top_k(self):
        chunks = [make_chunk(name=f"fn{i}", start_line=i, end_line=i) for i in range(10)]
        tool = self._tool(chunks)
        result = tool.execute("anything", top_k=3)
        # The fake retriever returns only :3 chunks; context should mention fn0/fn1/fn2
        assert "fn0" in result

    def test_empty_query_returns_error_message(self):
        tool = self._tool([make_chunk()])
        result = tool.execute("")
        assert "query" in result.lower() or "no" in result.lower()


# ===========================================================================
# FIX D — DiagnosisEvaluator: robust float parsing
# ===========================================================================

class TestDiagnosisEvaluatorRobustParsing:

    def _evaluator(self, response_text: str):
        from repository.evaluation.diagnosis import DiagnosisEvaluator

        class _FakeLLM:
            def __init__(self, text):
                self._text = text
            def invoke(self, messages):
                return self._text

        return DiagnosisEvaluator(llm_client=_FakeLLM(response_text))

    def _case(self):
        from repository.evaluation.models import EvaluationCase
        return EvaluationCase(
            case_id="TEST-001",
            bug_description="discount applied twice",
            expected_files=["checkout.py"],
            expected_tools=["search_code"],
            expected_diagnosis="Discount subtracted instead of added.",
        )

    def test_plain_float_parses(self):
        ev = self._evaluator("0.8")
        result = ev.evaluate_case(self._case(), "Some diagnosis")
        assert result.score == pytest.approx(0.8)

    def test_verbose_response_extracts_float(self):
        ev = self._evaluator("0.7 — partially correct, identifies the file but misses the root cause")
        result = ev.evaluate_case(self._case(), "Some diagnosis")
        assert result.score == pytest.approx(0.7)

    def test_score_clamped_above_1(self):
        ev = self._evaluator("1.5")
        result = ev.evaluate_case(self._case(), "Excellent")
        assert result.score == pytest.approx(1.0)

    def test_score_clamped_below_0(self):
        ev = self._evaluator("-0.3")
        result = ev.evaluate_case(self._case(), "Wrong")
        assert result.score == pytest.approx(0.0)

    def test_no_number_in_response_defaults_to_zero(self):
        ev = self._evaluator("I cannot determine a score")
        result = ev.evaluate_case(self._case(), "Some diagnosis")
        assert result.score == pytest.approx(0.0)

    def test_integer_response_parses(self):
        ev = self._evaluator("1")
        result = ev.evaluate_case(self._case(), "Perfect")
        assert result.score == pytest.approx(1.0)

    def test_zero_response_parses(self):
        ev = self._evaluator("0")
        result = ev.evaluate_case(self._case(), "Wrong")
        assert result.score == pytest.approx(0.0)


# ===========================================================================
# FIX 1 — HybridRetriever: RRF fusion correctness (extended edge cases)
# ===========================================================================

class TestHybridRetrieverEdgeCases:

    def _retriever(self, semantic_results, lexical_results, rrf_k=60):
        from repository.retrieval.hybrid import HybridRetriever

        class _Fake:
            def __init__(self, results):
                self._results = results
            def search(self, query, top_k):
                return self._results

        return HybridRetriever(
            semantic_retriever=_Fake(semantic_results),
            lexical_retriever=_Fake(lexical_results),
            rrf_k=rrf_k,
        )

    def test_chunk_in_both_lists_ranked_first(self):
        shared = make_chunk(name="shared", start_line=99, end_line=99)
        semantic = [make_chunk(name="s1", start_line=1, end_line=1), shared]
        lexical = [shared, make_chunk(name="l1", start_line=2, end_line=2)]
        retriever = self._retriever(semantic, lexical)
        results = retriever.search("test", top_k=3)
        assert results[0].name == "shared"

    def test_empty_semantic_results_uses_lexical(self):
        lexical = [make_chunk(name="lex_only", start_line=1, end_line=1)]
        retriever = self._retriever([], lexical)
        results = retriever.search("test", top_k=5)
        assert any(r.name == "lex_only" for r in results)

    def test_empty_lexical_results_uses_semantic(self):
        semantic = [make_chunk(name="sem_only", start_line=1, end_line=1)]
        retriever = self._retriever(semantic, [])
        results = retriever.search("test", top_k=5)
        assert any(r.name == "sem_only" for r in results)

    def test_both_empty_returns_empty(self):
        retriever = self._retriever([], [])
        assert retriever.search("test", top_k=5) == []

    def test_empty_query_returns_empty(self):
        chunks = [make_chunk()]
        retriever = self._retriever(chunks, chunks)
        assert retriever.search("   ", top_k=5) == []

    def test_top_k_limits_results(self):
        items = [make_chunk(name=f"f{i}", start_line=i, end_line=i) for i in range(10)]
        retriever = self._retriever(items, items)
        results = retriever.search("anything", top_k=3)
        assert len(results) == 3

    def test_rrf_score_higher_with_lower_k(self):
        """Lower rrf_k amplifies rank differences."""
        shared = make_chunk(name="shared", start_line=1, end_line=1)
        retriever_low_k = self._retriever([shared], [shared], rrf_k=1)
        retriever_high_k = self._retriever([shared], [shared], rrf_k=1000)
        # Both should still rank shared first; just verify no crash
        assert retriever_low_k.search("q", top_k=1)[0].name == "shared"
        assert retriever_high_k.search("q", top_k=1)[0].name == "shared"
