from repository.ai.context_builder import RepositoryContextBuilder
from repository.ai.retriever import CodeRetriever


class RepositoryDebugger:

    def __init__(
        self,
        retriever: CodeRetriever,
        context_builder: RepositoryContextBuilder,
    ):
        self.retriever = retriever
        self.context_builder = context_builder

    def build_context(
        self,
        question: str,
        top_k: int = 5,
    ) -> str:

        chunks = self.retriever.retrieve(
            question,
            top_k=top_k,
        )

        return self.context_builder.build(chunks)