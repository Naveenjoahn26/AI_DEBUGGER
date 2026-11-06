from repository.ai.context_builder import (
    RepositoryContextBuilder,
)
from repository.intelligence.question_engine import (
    CodeQuestionEngine,
)
from repository.models.code_chunk import CodeChunk


class FakeRetriever:

    def search(self, query, top_k=5):

        return [
            CodeChunk(
                content="def login():\n    return True",
                file_path="auth.py",
                chunk_type="function",
                name="login",
                start_line=10,
                end_line=11,
            )
        ]


class FakeLLM:

    def __init__(self):
        self.received_prompt = None

    def generate(self, prompt):

        self.received_prompt = prompt

        return "Authentication is handled in auth.py."


def test_question_engine():

    retriever = FakeRetriever()
    llm = FakeLLM()

    engine = CodeQuestionEngine(
        retriever=retriever,
        context_builder=RepositoryContextBuilder(),
        llm=llm,
    )

    answer = engine.ask(
        "Where is authentication handled?"
    )

    assert answer == (
        "Authentication is handled in auth.py."
    )

    assert "auth.py" in llm.received_prompt
    assert "login" in llm.received_prompt
    assert "Where is authentication handled?" in (
        llm.received_prompt
    )

def test_empty_question():

    engine = CodeQuestionEngine(
        retriever=FakeRetriever(),
        context_builder=RepositoryContextBuilder(),
        llm=FakeLLM(),
    )

    assert engine.ask("   ") == ""


class EmptyRetriever:

    def search(self, query, top_k=5):
        return []


def test_question_with_no_context():

    llm = FakeLLM()

    engine = CodeQuestionEngine(
        retriever=EmptyRetriever(),
        context_builder=RepositoryContextBuilder(),
        llm=llm,
    )

    answer = engine.ask(
        "Where is authentication implemented?"
    )

    assert answer == (
        "Authentication is handled in auth.py."
    )

    assert "Repository Context:" in (
        llm.received_prompt
    )
