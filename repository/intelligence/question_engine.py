from repository.intelligence.context_builder import (
    RepositoryContextBuilder,
)
from repository.llm.provider import LLMProvider


class CodeQuestionEngine:

    def __init__(
        self,
        retriever,
        context_builder: RepositoryContextBuilder,
        llm: LLMProvider,
    ):
        self.retriever = retriever
        self.context_builder = context_builder
        self.llm = llm

    def ask(
        self,
        question: str,
        top_k: int = 5,
    ) -> str:

        if not question.strip():
            return ""

        chunks = self.retriever.search(
            question,
            top_k=top_k,
        )

        context_items = self.context_builder.build(
            chunks
        )

        context = self.context_builder.format(
            context_items
        )

        prompt = self._build_prompt(
            question=question,
            context=context,
        )

        return self.llm.generate(prompt)

    def _build_prompt(
        self,
        question: str,
        context: str,
    ) -> str:

        return f"""
You are an AI software engineer analyzing a code repository.

Answer the user's question using the provided repository context.

Rules:
- Use the repository context as the primary source of truth.
- Do not invent files, functions, classes, or behavior.
- If the context is insufficient, explicitly say so.
- Mention relevant file paths and line numbers when available.
- Explain your reasoning clearly but concisely.

Repository Context:
{context}

User Question:
{question}
""".strip()