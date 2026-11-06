from pydantic import BaseModel, Field
from typing import Type

from repository.ai.context_builder import RepositoryContextBuilder


class SearchCodeInput(BaseModel):
    query: str = Field(
        ...,
        description="The natural language query to search the codebase for (e.g., 'authentication logic', 'user model').",
    )
    # FIX B: expose top_k so the agent can request deeper search when needed
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of code chunks to retrieve (1–20). Use a higher value for complex bugs spanning many files.",
    )


class SearchCodeTool:
    """Searches the repository for code matching a natural language query."""

    name = "search_code"
    description = (
        "Use this tool to search the codebase for specific functions, classes, or logic. "
        "Increase top_k for broader searches when the bug may span multiple files."
    )
    args_schema: Type[BaseModel] = SearchCodeInput

    def __init__(
        self,
        retriever,
        context_builder: RepositoryContextBuilder,
    ):
        self.retriever = retriever
        self.context_builder = context_builder

    def execute(self, query: str, top_k: int = 5) -> str:
        # guard empty queries defensively at tool boundary too
        if not query or not query.strip():
            return "No query provided. Please supply a search query."

        chunks = self.retriever.retrieve(query, top_k=top_k)

        if not chunks:
            return f"No relevant code found for query: '{query}'"

        context_items = self.context_builder.build(chunks)
        formatted_context = self.context_builder.format(context_items)

        return formatted_context
